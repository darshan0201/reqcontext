# Testing

Run from the repository root after installing the optional dependencies:

```bash
python -m pip install -e ".[c,documents,mcp]"
python -m unittest discover -s tests -v
python tests/integration/mcp_smoke.py
```

## Coverage

| Check | Purpose |
|---|---|
| `test_core.py` | Indexing, retrieval, clarification memory and C parser behavior |
| `test_investigation.py` | Model tool loop, schema validation and evidence handling |
| `test_snapshot_documents.py` | Snapshot reuse, refresh rollback, scoped lookup and documents |
| `test_markdown.py` | Readable reports and optional source fingerprints |
| `integration/mcp_smoke.py` | Actual stdio initialization, tool listing and symbol lookup |

The base suite can run without optional C dependencies, but C-specific cases will
be skipped. CI installs all extras and also runs the MCP integration check.

## Evaluation versus regression tests

Scripted models test orchestration, not model intelligence. Assess reasoning quality
separately with representative requirements, fixed repository revisions and reviewed
expected outcomes. Record unsupported conclusions and missed relevant context as
well as latency and resource use. Keep raw experiment output outside version control;
include a concise result and limitations in the relevant PR.

No live endpoint or storage hardware is needed for the committed regression suite.
