"""Incremental, content-addressed SQLite FTS index and static Python observations."""
from __future__ import annotations
import ast
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess

SUPPORTED = {".py", ".md", ".rst", ".txt", ".json", ".toml", ".yaml", ".yml"}
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", ".reqcontext", ".idea"}
STOP = set("a an the to of for in on at is it be we with and or when if this that should shall must add implement support please change update using use".split())
ALIASES = {"retries": "retry", "retrying": "retry", "uploads": "upload", "uploading": "upload", "failed": "fail", "fails": "fail", "failure": "fail", "failures": "fail", "timeouts": "timeout", "deletion": "delete", "deleting": "delete"}


def tokens(text: str) -> list[str]:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return [ALIASES.get(t, t) for t in re.findall(r"[a-zA-Z][a-zA-Z0-9]*", text.lower()) if t not in STOP]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def chunks(path: str, source: str):
    lines = source.splitlines()
    # Short windows retain context for documentation/configuration and imports.
    for start in range(0, len(lines), 24):
        yield start + 1, min(start + 24, len(lines)), "text", "", "\n".join(lines[start:start + 24]), []
    if Path(path).suffix != ".py":
        return
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return

    def visit(node, scope=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{scope}.{child.name}" if scope else child.name
                end = child.end_lineno or child.lineno
                calls = sorted({ast.unparse(n.func) for n in ast.walk(child) if isinstance(n, ast.Call)})
                # Large symbols retain a bounded excerpt; range describes that excerpt.
                excerpt_end = min(end, child.lineno + 59)
                yield child.lineno, excerpt_end, "class" if isinstance(child, ast.ClassDef) else "function", name, "\n".join(lines[child.lineno - 1:excerpt_end]), calls
                yield from visit(child, name)
            else:
                yield from visit(child, scope)
    yield from visit(tree)


class Index:
    def __init__(self, root, cache=None, excludes=(), max_file_bytes=1_000_000):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError("Repository must be an existing directory")
        if max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be positive")
        self.excludes = tuple(excludes)
        self.max_file_bytes = max_file_bytes
        cache = Path(cache) if cache else self.root / ".reqcontext" / "index.sqlite3"
        cache.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(cache)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, path TEXT, start INTEGER,
                end INTEGER, kind TEXT, symbol TEXT, excerpt TEXT, calls TEXT);
            CREATE INDEX IF NOT EXISTS chunk_paths ON chunks(path);
            CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(body, tokenize='porter unicode61');
            CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY, task TEXT, question TEXT,
                answer TEXT, sources TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
        ''')
        owner = self.db.execute("SELECT value FROM metadata WHERE key='root'").fetchone()
        if owner and owner[0] != str(self.root):
            self.db.close()
            raise ValueError("Cache belongs to a different repository")
        self.db.execute("INSERT OR IGNORE INTO metadata VALUES('root', ?)", (str(self.root),))
        self.db.commit()

    def paths(self):
        # Use Git's own ignore implementation when available, including nested rules.
        try:
            top = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
            if top.returncode == 0 and Path(top.stdout.strip()).resolve() == self.root:
                result = subprocess.run(["git", "-C", str(self.root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"], capture_output=True, timeout=10, check=True)
                candidates = sorted(set(os.fsdecode(p) for p in result.stdout.split(b"\0") if p))
            else:
                candidates = self._walk()
        except (OSError, subprocess.SubprocessError):
            candidates = self._walk()
        for rel in candidates:
            path = self.root / rel
            parts = Path(rel).parts
            if any(p in SKIP or p.startswith(".") for p in parts):
                continue
            if path.suffix.lower() not in SUPPORTED or any(fnmatch.fnmatch(rel, p) for p in self.excludes):
                continue
            # Never follow file or ancestor symlinks, even to targets inside the repo.
            if any((self.root.joinpath(*parts[:i])).is_symlink() for i in range(1, len(parts) + 1)):
                continue
            if path.is_file() and path.resolve().is_relative_to(self.root):
                yield rel, path

    def _walk(self):
        result = []
        for directory, dirs, files in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith(".") and not (Path(directory) / d).is_symlink())
            result.extend((Path(directory) / f).relative_to(self.root).as_posix() for f in sorted(files))
        return sorted(result)

    def _remove(self, path):
        self.db.execute("DELETE FROM search WHERE rowid IN (SELECT id FROM chunks WHERE path=?)", (path,))
        self.db.execute("DELETE FROM chunks WHERE path=?", (path,))
        self.db.execute("DELETE FROM files WHERE path=?", (path,))

    def refresh(self):
        stats = {"indexed": 0, "reused": 0, "removed": 0, "skipped": 0}
        previous = {r["path"]: r["hash"] for r in self.db.execute("SELECT * FROM files")}
        seen = set()
        with self.db:
            for rel, path in self.paths():
                try:
                    with path.open("rb") as handle:
                        data = handle.read(self.max_file_bytes + 1)
                    if len(data) > self.max_file_bytes or b"\0" in data:
                        stats["skipped"] += 1
                        continue
                    source = data.decode("utf-8")
                except (OSError, UnicodeError):
                    stats["skipped"] += 1
                    continue
                seen.add(rel)
                fingerprint = digest(data)
                if previous.get(rel) == fingerprint:
                    stats["reused"] += 1
                    continue
                self._remove(rel)
                self.db.execute("INSERT INTO files VALUES(?, ?)", (rel, fingerprint))
                for start, end, kind, symbol, excerpt, calls in chunks(rel, source):
                    cursor = self.db.execute("INSERT INTO chunks(path,start,end,kind,symbol,excerpt,calls) VALUES(?,?,?,?,?,?,?)", (rel, start, end, kind, symbol, excerpt, json.dumps(calls)))
                    body = " ".join(tokens(f"{rel} {symbol} {symbol} {excerpt}"))
                    self.db.execute("INSERT INTO search(rowid,body) VALUES(?, ?)", (cursor.lastrowid, body))
                stats["indexed"] += 1
            for deleted in previous.keys() - seen:
                self._remove(deleted)
                stats["removed"] += 1
        return stats

    def search(self, query, limit=10):
        words = sorted(set(tokens(query)))[:32]
        if not words:
            return []
        # Tokens contain only alphanumerics; no user-supplied FTS operators.
        expression = " OR ".join('"' + w + '"' for w in words)
        rows = self.db.execute('''SELECT c.*, f.hash, bm25(search) AS rank
            FROM search JOIN chunks c ON c.id=search.rowid JOIN files f ON f.path=c.path
            WHERE search MATCH ? ORDER BY rank, c.path, c.start LIMIT ?''', (expression, limit * 5)).fetchall()
        candidates = []
        for row in rows:
            value = dict(row)
            name_overlap = len(set(tokens(value["symbol"])) & set(words))
            value["score"] = -value.pop("rank") + name_overlap * 0.5
            value["calls"] = json.loads(value["calls"])
            candidates.append(value)
        candidates.sort(key=lambda r: (-r["score"], r["path"], r["start"], r["kind"]))
        selected = []
        for row in candidates:
            if any(row["path"] == r["path"] and max(row["start"], r["start"]) <= min(row["end"], r["end"]) for r in selected):
                continue
            selected.append(row)
            if len(selected) == limit:
                break
        return selected

    def close(self):
        self.db.close()
