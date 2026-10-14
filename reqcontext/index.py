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
from datetime import datetime, timezone
from contextlib import contextmanager
from uuid import uuid4
from . import c_parser
from .documents import SourceDocument, extract

SUPPORTED = {".py", ".md", ".rst", ".txt", ".json", ".toml", ".yaml", ".yml", ".c", ".h"}
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", ".reqcontext", ".idea"}
STOP = set("a an the to of for in on at is it be we with and or when if this that should shall must add implement support please change update using use".split())



def tokens(text: str) -> list[str]:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return [t for t in re.findall(r"[a-zA-Z][a-zA-Z0-9]*", text.lower()) if t not in STOP]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def chunks(path: str, source: str):
    """Non-overlapping windows with the narrowest lexical symbol as owner.

    Collect definitions and calls in a single AST traversal. Calls in nested
    definitions belong only to that definition, not its enclosing class/function.
    """
    lines = source.splitlines()
    owners = [None] * len(lines)
    definitions = []
    if Path(path).suffix == ".py":
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError):
            tree = None
        if tree is not None:
            class Collector(ast.NodeVisitor):
                def __init__(self):
                    self.stack = []

                def definition(self, node):
                    name = ".".join([d["name"] for d in self.stack] + [node.name])
                    definition = {"name": node.name, "symbol": name,
                                  "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                                  "start": node.lineno, "end": node.end_lineno or node.lineno,
                                  "calls": set()}
                    definitions.append(definition)
                    # Children are visited later and overwrite the owner on their lines.
                    owners[definition["start"] - 1:definition["end"]] = [definition] * (definition["end"] - definition["start"] + 1)
                    self.stack.append(definition)
                    self.generic_visit(node)
                    self.stack.pop()

                visit_FunctionDef = definition
                visit_AsyncFunctionDef = definition
                visit_ClassDef = definition

                def visit_Call(self, node):
                    if self.stack:
                        self.stack[-1]["calls"].add(ast.unparse(node.func))
                    self.generic_visit(node)

            Collector().visit(tree)
    if Path(path).suffix in {".c", ".h"}:
        for definition in c_parser.functions(source):
            owners[definition["start"] - 1:definition["end"]] = [definition] * (definition["end"] - definition["start"] + 1)
    start = 0
    while start < len(lines):
        owner = owners[start]
        end = start + 1
        while end < len(lines) and owners[end] is owner and end - start < 24:
            end += 1
        yield start + 1, end, owner["kind"] if owner else "text", owner["symbol"] if owner else "", "\n".join(lines[start:end]), sorted(owner["calls"]) if owner else []
        start = end


class Index:
    def __init__(self, root, cache=None, excludes=(), max_file_bytes=1_000_000, documents=()):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError("Repository must be an existing directory")
        if max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be positive")
        self.documents = tuple(d if isinstance(d, SourceDocument) else SourceDocument(d) for d in documents)
        self.document_warnings = []
        self.excludes = tuple(excludes)
        self.max_file_bytes = max_file_bytes
        cache = Path(cache) if cache else self.root / ".reqcontext" / "index.sqlite3"
        cache.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(cache)
        self.db.row_factory = sqlite3.Row
        self._transaction_depth = 0
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
        columns = {r[1] for r in self.db.execute("PRAGMA table_info(chunks)")}
        if "page" not in columns:
            self.db.execute("ALTER TABLE chunks ADD COLUMN page INTEGER")
        self.db.executescript("CREATE TABLE IF NOT EXISTS documents(path TEXT PRIMARY KEY, title TEXT, revision TEXT, source_type TEXT, metadata TEXT); CREATE TABLE IF NOT EXISTS folders(path TEXT PRIMARY KEY,parent TEXT,file_count INTEGER); CREATE TABLE IF NOT EXISTS call_edges(path TEXT,symbol TEXT,callee TEXT,PRIMARY KEY(path,symbol,callee)); CREATE INDEX IF NOT EXISTS callee_lookup ON call_edges(callee);")
        owner = self.db.execute("SELECT value FROM metadata WHERE key='root'").fetchone()
        if owner and owner[0] != str(self.root):
            self.db.close()
            raise ValueError("Cache belongs to a different repository")
        self.db.execute("INSERT OR IGNORE INTO metadata VALUES('root', ?)", (str(self.root),))
        version = self.db.execute("SELECT value FROM metadata WHERE key='index_version'").fetchone()
        index_version = "7:c" if c_parser.available() else "7:text"
        if not version or version[0] != index_version:
            self.db.execute("DELETE FROM search")
            self.db.execute("DELETE FROM chunks")
            self.db.execute("DELETE FROM files")
            self.db.execute("DELETE FROM metadata WHERE key='snapshot'")
            self.db.execute("INSERT OR REPLACE INTO metadata VALUES('index_version', ?)", (index_version,))
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

    @contextmanager
    def transaction(self):
        name = f"reqcontext_tx_{self._transaction_depth}"
        self._transaction_depth += 1
        self.db.execute("SAVEPOINT " + name)
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK TO " + name)
            self.db.execute("RELEASE " + name)
            raise
        else:
            self.db.execute("RELEASE " + name)
        finally:
            self._transaction_depth -= 1

    def refresh(self):
        # Source index, references, derived maps and capture metadata become
        # visible together. A failed refresh leaves the last snapshot intact.
        with self.transaction():
            return self._refresh()

    def _refresh(self):
        stats = {"indexed": 0, "reused": 0, "removed": 0, "skipped": 0}
        previous = {r["path"]: r["hash"] for r in self.db.execute("SELECT * FROM files WHERE path NOT LIKE '@documents/%'")}
        seen = set()
        with self.transaction():
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
        stats["documents"] = self.refresh_documents()
        with self.transaction():
            self.db.execute("DELETE FROM call_edges")
            for row in self.db.execute("SELECT DISTINCT path,symbol,calls FROM chunks WHERE symbol!=''").fetchall():
                self.db.executemany("INSERT OR IGNORE INTO call_edges VALUES(?,?,?)",[(row[0],row[1],callee) for callee in json.loads(row[2])])
        counts = {}
        for row in self.db.execute("SELECT path FROM files WHERE path NOT LIKE '@documents/%'"):
            parts = Path(row[0]).parts[:-1]
            for length in range(1,len(parts)+1):
                folder = "/".join(parts[:length])
                counts[folder] = counts.get(folder,0)+1
        revision = "unversioned"
        try:
            result = subprocess.run(["git","-C",str(self.root),"rev-parse","HEAD"],capture_output=True,text=True,timeout=5)
            if result.returncode == 0:
                revision = result.stdout.strip()
        except (OSError,subprocess.SubprocessError):
            pass
        snapshot = {"snapshot_id":str(uuid4()),"captured_at": datetime.now(timezone.utc).isoformat(), "git_revision": revision,
                    "revision_note": "HEAD is recorded, but indexed files may include uncommitted changes.",
                    "files": self.db.execute("SELECT COUNT(*) FROM files").fetchone()[0],
                    "documents": self.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0], "documents_selected":len(self.documents), "excludes": list(self.excludes), "max_file_bytes":self.max_file_bytes,
                    "documents_manifest":[{"key":d.key(),"title":d.title,"revision":d.revision,"type":d.source_type} for d in self.documents],
                    "document_warnings": self.document_warnings}
        with self.transaction():
            self.db.execute("DELETE FROM folders")
            self.db.executemany("INSERT INTO folders VALUES(?,?,?)",[(f,f.rpartition('/')[0],n) for f,n in counts.items()])
            self.db.execute("INSERT OR REPLACE INTO metadata VALUES('snapshot',?)",(json.dumps(snapshot),))
        return stats

    def snapshot(self):
        row = self.db.execute("SELECT value FROM metadata WHERE key='snapshot'").fetchone()
        return json.loads(row[0]) if row else None

    def ensure_snapshot(self):
        existing = self.snapshot()
        if existing is None:
            return self.refresh()
        if list(self.excludes) != existing.get("excludes",[]):
            raise ValueError("Exclusions changed; refresh the snapshot explicitly before using it")
        if self.max_file_bytes != existing.get("max_file_bytes",1_000_000):
            raise ValueError("Source size policy changed; refresh snapshot explicitly")
        current_documents = [{"key":d.key(),"title":d.title,"revision":d.revision,"type":d.source_type} for d in self.documents]
        if self.documents and current_documents != existing.get("documents_manifest",[]):
            raise ValueError("Document selection changed; refresh snapshot explicitly")
        self.document_warnings = existing.get("document_warnings",[])
        return {"indexed":0,"reused":existing["files"],"removed":0,"skipped":0,
                "snapshot_reused":True,"source_files_read":0}

    def folder_map(self,prefix="",limit=100):
        if not isinstance(prefix,str) or type(limit) is not int or not 1<=limit<=100:
            raise ValueError("Folder prefix must be a string and limit must be 1..100")
        prefix = "" if prefix in {"", "."} else prefix.rstrip("/")
        if Path(prefix).is_absolute() or ".." in Path(prefix).parts:
            raise ValueError("Folder prefix must be repository-relative")
        rows = self.db.execute("SELECT path,file_count FROM folders WHERE parent=? ORDER BY path LIMIT ?",(prefix.rstrip('/'),limit+1)).fetchall()
        return {"folders":[dict(r) for r in rows[:limit]],"truncated":len(rows)>limit}


    def refresh_documents(self):
        self.document_warnings = []
        stats = {"indexed": 0, "reused": 0, "removed": 0, "failed": 0}
        previous = {r[0] for r in self.db.execute("SELECT path FROM documents")}
        active = set()
        with self.transaction():
            for document in self.documents:
                key = document.key()
                active.add(key)
                try:
                    # Hash bytes on every refresh; only PDF parsing/indexing is cached.
                    path = Path(document.path)
                    if not path.is_file() or path.is_symlink() or path.stat().st_size > 50_000_000:
                        raise ValueError("Document missing, symlinked or exceeds byte limit")
                    raw = path.read_bytes()
                    fingerprint = digest(raw)
                    previous_hash = self.db.execute("SELECT hash FROM files WHERE path=?", (key,)).fetchone()
                    existing = self.db.execute("SELECT metadata,title,revision,source_type FROM documents WHERE path=?", (key,)).fetchone()
                    if previous_hash and existing and previous_hash[0] == fingerprint and tuple(existing[1:]) == (document.title or path.name,document.revision,document.source_type):
                        warnings = json.loads(existing[0])
                        stats["reused"] += 1
                    else:
                        fingerprint, pages, warnings = extract(document)
                        self._remove(key)
                        self.db.execute("INSERT INTO files VALUES(?, ?)", (key, fingerprint))
                        for page, text in pages:
                            for start, end, _, _, excerpt, _ in chunks("reference.txt", text):
                                cursor = self.db.execute("INSERT INTO chunks(path,start,end,kind,symbol,excerpt,calls,page) VALUES(?,?,?,?,?,?,?,?)", (key,start,end,"document","",excerpt,"[]",page))
                                body = " ".join(tokens(f"{document.title} {path.name} {excerpt}"))
                                self.db.execute("INSERT INTO search(rowid,body) VALUES(?, ?)", (cursor.lastrowid,body))
                        stats["indexed"] += 1
                    self.db.execute("INSERT OR REPLACE INTO documents VALUES(?,?,?,?,?)", (key,document.title or path.name,document.revision,document.source_type,json.dumps(warnings)))
                    self.document_warnings.extend(f"{key}: {w}" for w in warnings)
                except Exception as error:
                    self._remove(key)
                    self.db.execute("DELETE FROM documents WHERE path=?", (key,))
                    stats["failed"] += 1
                    self.document_warnings.append(f"{key}: Document ingestion failed ({type(error).__name__}); stale evidence removed.")
            for key in previous - active:
                self._remove(key)
                self.db.execute("DELETE FROM documents WHERE path=?", (key,))
                stats["removed"] += 1
        return stats

    def decorate(self, match):
        match = dict(match)
        if match["path"].startswith("@documents/"):
            row = self.db.execute("SELECT title,revision,source_type FROM documents WHERE path=?", (match["path"],)).fetchone()
            if row:
                match["source"] = {"title": row[0], "revision": row[1], "declared_type": row[2], "classification_verified": False}
        return match

    def search(self, query, limit=10, prefix=None):
        if not isinstance(query,str) or type(limit) is not int or not 1<=limit<=50:
            raise ValueError("Query must be a string and limit must be 1..50")
        if prefix is not None and not isinstance(prefix,str):
            raise ValueError("Search prefix must be a string")
        prefix = None if prefix in {None,"","."} else prefix.rstrip("/")
        words = sorted(set(tokens(query)))[:32]
        if not words:
            return []
        # Tokens contain only alphanumerics; no user-supplied FTS operators.
        expression = " OR ".join('"' + w + '"' for w in words)
        scope = ""
        parameters = [expression]
        if prefix:
            if Path(prefix).is_absolute() or ".." in Path(prefix).parts:
                raise ValueError("Search prefix must be relative")
            scope = " AND substr(c.path,1,?) = ?"
            literal_prefix = prefix.rstrip('/') + "/"
            parameters.extend([len(literal_prefix),literal_prefix])
        parameters.append(max(100,limit*10))
        rows = self.db.execute('''SELECT c.*, f.hash, bm25(search) AS rank
            FROM search JOIN chunks c ON c.id=search.rowid JOIN files f ON f.path=c.path
            WHERE search MATCH ?''' + scope + ' ORDER BY rank, c.path, c.start LIMIT ?', parameters).fetchall()
        candidates = []
        for row in rows:
            value = self.decorate(row)
            name_overlap = len(set(tokens(value["symbol"])) & set(words))
            value["score"] = -value.pop("rank")
            value["calls"] = json.loads(value["calls"])
            candidates.append(value)
        candidates.sort(key=lambda r: (-r["score"], r["path"], r["start"], r["kind"]))
        selected = []
        for row in candidates:
            if any(row["path"] == r["path"] and row.get("page") == r.get("page") and ((row["symbol"] and row["symbol"] == r["symbol"]) or max(row["start"], r["start"]) <= min(row["end"], r["end"])) for r in selected):
                continue
            selected.append(row)
            if len(selected) == limit:
                break
        return selected

    def symbols(self, query="", prefix=None, limit=50):
        if prefix is not None and not isinstance(prefix,str):
            raise ValueError("Symbol prefix must be a string")
        if not isinstance(query,str) or type(limit) is not int or not 1<=limit<=100:
            raise ValueError("Symbol query must be a string and limit must be 1..100")
        parameters=[query]
        scope=""
        if prefix not in {None,"","."}:
            if not isinstance(prefix,str) or Path(prefix).is_absolute() or ".." in Path(prefix).parts:
                raise ValueError("Symbol prefix must be repository-relative")
            literal=prefix.rstrip('/')+"/"
            scope=" AND substr(path,1,?)=?"
            parameters.extend([len(literal),literal])
        parameters.append(limit+1)
        rows=self.db.execute("SELECT path,symbol,kind,MIN(start) AS start,MAX(end) AS end FROM chunks WHERE symbol!='' AND instr(lower(symbol),lower(?))>0"+scope+" GROUP BY path,symbol,kind ORDER BY path,symbol LIMIT ?",parameters).fetchall()
        return {"symbols":[dict(r) for r in rows[:limit]],"truncated":len(rows)>limit}

    def close(self):
        self.db.close()
