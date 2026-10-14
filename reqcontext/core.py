"""Requirement briefs with explicit provenance and optional untrusted model proposals."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import json
from typing import Callable
from .index import Index
from . import c_parser


@dataclass
class Brief:
    requirement: str
    evidence: list[dict]
    questions: list[dict]
    observations: list[dict]
    interpretations: list[dict]
    decisions: list[dict]
    index_stats: dict
    warnings: list[str] = field(default_factory=list)
    mode: str = "retrieval-only"
    constraints: list[dict] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    investigation: dict = field(default_factory=dict)
    snapshot: dict = field(default_factory=dict)
    scope: list[dict] = field(default_factory=list)

    @property
    def relevant_symbols(self):
        return [e for e in self.evidence if e["symbol"]]

    def to_dict(self):
        return asdict(self)

    def to_markdown(self, *, include_provenance=False):
        lines = ["# Requirement context", "", "## User requirement", "", self.requirement,
                 "", "## Repository evidence", ""]
        for e in self.evidence:
            if e.get("page") is not None:
                lines.append(f"PDF page {e['page']}; line numbers below refer to extracted page text.")
            lines += [f"- **{e['id']}** `{e['path']}:{e['start']}-{e['end']}` — {e['symbol'] or e['kind']}"]
        if not self.evidence:
            lines.append("No matching evidence found. This does not establish that the feature is absent.")
        for title, items, key in [("Observations", self.observations, "text"), ("Clarifications", self.questions, "question"), ("Proposed interpretations — not verified facts", self.interpretations, "text")]:
            lines += ["", f"## {title}", ""]
            lines += [f"- {v[key]} (evidence: {', '.join(v.get('evidence_ids', [])) or 'none'})" for v in items] or ["None."]
        lines += ["", "## Recommended folders", ""]
        lines += [f"- `{s['folder']}`: {s['reason']}" for s in self.scope] or ["No model-selected folder scope."]
        lines += ["", "## Snapshot", "", f"Captured: {self.snapshot.get('captured_at','unknown')}; HEAD: `{self.snapshot.get('git_revision','unknown')}`"]
        lines += ["", "## Selected constraints", ""]
        lines += [f"- [{c['origin']}] {c['text']} — {c['applicability']} (evidence: {', '.join(c['evidence_ids'])})" for c in self.constraints] or ["None selected."]
        if self.unresolved:
            lines += ["", "## Unresolved", ""] + [f"- {u}" for u in self.unresolved]
        lines += ["", "## Saved clarifications", ""]
        lines += [f"- [{d['status']}] {d['question']} → {d['answer']}" for d in self.decisions] or ["None."]
        if self.warnings:
            lines += ["", "## Limitations / warnings", ""] + [f"- {w}" for w in self.warnings]
        if include_provenance:
            lines += ["", "## Source fingerprints", ""]
            for path, digest in dict.fromkeys((e["path"], e["hash"]) for e in self.evidence):
                lines.append(f"- `{path}` — SHA-256: `{digest}`")
        return "\n".join(lines) + "\n"


class RequirementContext:
    """Context manager recommended. `model` is a user-provided callable(dict)->dict.

    Bounded retrieved excerpts go to the callable. Use ChatModel for a configured
    endpoint or supply your own adapter with its own timeout/transport policy.
    """
    def __init__(self, repo, *, cache=None, model: Callable | None = None, excludes=(), max_file_bytes=1_000_000, documents=(), refresh_mode="snapshot"):
        if refresh_mode not in {"snapshot", "auto"}:
            raise ValueError("refresh_mode must be snapshot or auto")
        self.refresh_mode = refresh_mode
        self.index = Index(repo, cache, excludes, max_file_bytes, documents)
        self.model = model

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        self.index.close()

    def refresh(self):
        return self.index.refresh()

    def remember(self, *, task, question, answer, sources=()):
        """Store a user-confirmed answer, scoped to exact task and source hashes.

        Source changes cause 'needs_review'; never auto-promote old answers.
        """
        if not all(isinstance(x, str) and x.strip() for x in (task, question, answer)):
            raise ValueError("task, question and answer must be nonempty strings")
        if self.refresh_mode == "auto":
            self.index.refresh()
        else:
            self.index.ensure_snapshot()
        fingerprints = {}
        for path in sources:
            row = self.index.db.execute("SELECT hash FROM files WHERE path=?", (path,)).fetchone()
            if not row:
                raise ValueError(f"Source is not indexed: {path}")
            fingerprints[path] = row[0]
        with self.index.db:
            result = self.index.db.execute("INSERT INTO decisions(task,question,answer,sources) VALUES(?,?,?,?)", (task.strip(), question.strip(), answer.strip(), json.dumps(fingerprints)))
        return result.lastrowid

    def _decisions(self, task):
        records = []
        for row in self.index.db.execute("SELECT * FROM decisions WHERE task=? ORDER BY id", (task,)):
            value = dict(row)
            value["sources"] = json.loads(value["sources"])
            stale = []
            for path, fingerprint in value["sources"].items():
                current = self.index.db.execute("SELECT hash FROM files WHERE path=?", (path,)).fetchone()
                if not current or current[0] != fingerprint:
                    stale.append(path)
            value["status"] = "needs_review" if stale else "user_confirmed"
            value["changed_sources"] = stale
            records.append(value)
        return records

    def analyze(self, requirement, *, task=None, max_evidence=8, max_chars=12000, max_rounds=4):
        if not isinstance(requirement, str) or not requirement.strip():
            raise ValueError("A nonempty requirement is required")
        if len(requirement) > 20000:
            raise ValueError("Requirement exceeds 20,000 characters")
        if not 1 <= max_evidence <= 50 or max_chars < 200:
            raise ValueError("max_evidence must be 1..50 and max_chars at least 200")
        requirement = requirement.strip()
        stats = self.index.refresh() if self.refresh_mode == "auto" else self.index.ensure_snapshot()
        matches = self.index.search(requirement, max_evidence)
        evidence, used = [], 0
        for match in matches:
            remaining = max_chars - used
            if remaining <= 0:
                break
            match.pop("id")
            excerpt = match["excerpt"][:remaining]
            match["truncated"] = len(excerpt) < len(match["excerpt"])
            match["excerpt"] = excerpt
            match["end"] = match["start"] + max(0, len(excerpt.splitlines()) - 1)
            match["id"] = f"E{len(evidence) + 1}"
            evidence.append(match)
            used += len(excerpt)
        observations = []
        for e in evidence:
            if e["symbol"]:
                observations.append({"text": f"Static {e['kind']} definition found: {e['symbol']}.", "evidence_ids": [e["id"]]})
        questions = []
        decisions = self._decisions(task.strip() if task else requirement)
        warnings = ["Semantic interpretation and question selection require a configured model.",
                    "Static symbol/call observations do not prove runtime reachability or behavior.",
                    "Evidence is a snapshot; refresh before acting if the workspace changes."]
        if not c_parser.available():
            warnings.append("C/header files are searchable as text only. Install the c extra for C function ownership.")
        warnings.extend(self.index.document_warnings)
        if stats["skipped"]:
            warnings.append(f"Skipped {stats['skipped']} unreadable, oversized, binary or non-UTF-8 files.")
        if any(d["status"] == "needs_review" for d in decisions):
            warnings.append("Saved clarifications have changed or missing source evidence; review before reuse.")
        warnings.append("Snapshot evidence may be stale; source files are not checked during snapshot-mode analysis. Refresh explicitly after relevant changes.")
        brief = Brief(requirement, evidence, questions, observations, [], decisions, stats, warnings)
        brief.snapshot = self.index.snapshot() or {}
        if self.model:
            from .investigation import Investigator
            Investigator(self, brief, max_rounds=max_rounds, max_chars=max_chars).run()
        return brief

