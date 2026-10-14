# ReqContext 0.5.1

A Python context engine for incomplete implementation requirements, with stored
repository snapshots and a local MCP adapter.

## Current behavior

Build a snapshot once. Requirements are investigated using its folder map, source
excerpts, symbols, call-name relationships and selected reference documents. Normal
analysis never enumerates/reads/hashes live source files after snapshot creation.
Refresh explicitly when evidence should change. Captured revision/time are shown;
frozen evidence can be stale. No keyword-triggered semantic questions are generated.

A configured model can select folders, follow evidence, propose applicable
constraints and ask consequential questions. Without a model, retrieval-only mode
returns evidence and makes no semantic conclusions. An MCP host can also use its
own existing model directly with the snapshot tools, without a nested API endpoint.

## Install

Python 3.11+, SQLite FTS5:

```bash
python -m pip install ".[c,documents,mcp]"
```

The extras are optional: C function parsing uses Tree-sitter, PDF text extraction
uses pypdf, and MCP stdio uses the v1 SDK compatibility API. The base install uses
Python AST and text search. This package is not published to PyPI.

## Build and investigate

```bash
reqcontext snapshot build /path/to/repo --output /path/to/snapshot.db
reqcontext /path/to/repo --snapshot /path/to/snapshot.db --requirement "Add retry support" --retrieval-only
reqcontext snapshot refresh /path/to/repo --output /path/to/snapshot.db
```

For model-directed interpretation, configure `REQCONTEXT_BASE_URL`,
`REQCONTEXT_MODEL`, and, if your endpoint requires it, `REQCONTEXT_API_KEY` locally.
The base URL is the chat-completions API root; the adapter appends
`/chat/completions`. The endpoint must support JSON-object responses.

```python
from reqcontext import analyze
brief = analyze("Add retry support", repo="/path/to/repo", snapshot="/path/to/snapshot.db")
print(brief.to_markdown())
print(brief.scope)
```

Reference documents, MCP client setup, refresh semantics, exclusions and limitations
are detailed in `SNAPSHOT_AND_PLUGIN.md`. Example MCP configuration:
`integration/mcp-client.example.json`. This is a local MCP server, not a marketplace
plugin automatically installed into your account.

## Validation

65 tests passed. Real stdio initialization/discovery/symbol lookup passed. A real
text-extractable PDF and nvme-cli folder-scoped snapshot lookup were checked.
Synthetic 10,000-file indexing took approximately five seconds in this runtime;
subsequent snapshot queries read no live source files. Those are indexing/integration
measurements, not evidence of LLM accuracy or end-to-end latency.

```bash
python -m unittest discover -s tests -v
PYTHONPATH=. python benchmarks/mcp_smoke.py
PYTHONPATH=. python benchmarks/scale_snapshot.py --output scale.json
```

`PROGRESS_V050.md` describes measurements and the same-tools model comparison runner.
No unattended model comparison ran here because no endpoint was configured. Prior
version reports are historical; they do not establish v0.5.0 semantic quality.

## Design boundaries

- Folder/constraint selection is model inference, not a newly trained policy.
- Lexical BM25 search is not semantic search. Name-based call relationships do not
  resolve aliases, dispatch, macros or same-name definitions.
- Quotations/citation IDs are checked; semantic entailment/applicability are not proven.
- PDFs retain page provenance but no OCR, diagram reasoning or perfect table layout.
- Snapshots are bound to their repository root and are not atomic multi-file captures.
- Snapshot-mode staleness detection compares saved decisions to the stored snapshot,
  not live source state. Explicit refresh is necessary after changes.
- Initial target is a single engineer/client; concurrent refresh writers are untested.
- Hidden/symlink/generated paths and oversized/binary/non-UTF-8 files are omitted;
  there is no general secret detector. Only selected references are imported.
- Model endpoint requests send bounded evidence but schemas/metadata/history add to
  the total prompt. Message separation does not guarantee prompt-injection resistance.

Research rationale: `RESEARCH_DESIGN.md`. Historical assistant-facilitated NVMe audit:
`NVME_REASONING_AUDIT.md`. Snapshot/MCP ideas already have substantial overlap with
Aider, Continue and CodeGraph; novelty and adoption value remain to be demonstrated.

## Documentation and PR preparation

- `docs/ARCHITECTURE.md`: components, principles and snapshot publication.
- `docs/API.md`: API fields, model phases and tool behavior.
- `SNAPSHOT_AND_PLUGIN.md`: build/refresh, MCP and reference setup.
- `docs/HTTPX_VALIDATION.md`: non-storage test results and remaining retrieval miss.
- `docs/ROBUSTNESS.md`: implemented safeguards and prioritized future work.
- `docs/PROVENANCE.md`: original implementation, dependencies and evidence notices.
- `CONTRIBUTING.md`, `CHANGELOG.md`, `.github/`: contribution and review workflow.

v0.5.1 makes refresh publication atomic, treats folder prefixes literally, validates
query limits and adds symbol-fragment lookup. A project license has not yet been selected. Historic reports are labelled by the version they measured.
