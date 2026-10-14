# API reference

## One-call entry point

```python
analyze(requirement, repo=".", *, model=None, excludes=(), max_evidence=8,
        max_rounds=4, retrieval_only=False, documents=(), snapshot=None,
        refresh=False)
```

Returns `Brief`. Semantic mode requires a `model(payload)->dict` callable or
REQCONTEXT endpoint configuration. Retrieval-only mode makes no semantic claims.
`refresh=True` explicitly rebuilds the source snapshot before analysis.

## Context

```python
RequirementContext(repo, *, cache=None, model=None, excludes=(),
                   max_file_bytes=1_000_000, documents=(),
                   refresh_mode="snapshot")
```

Use as a context manager. `analyze()` additionally accepts `task`, `max_chars`
(default 12,000 evidence-excerpt characters) and `max_rounds`. `refresh()` builds
or updates the snapshot. `remember(task=..., question=..., answer=..., sources=...)`
stores an exact-task clarification bound to indexed source hashes.

`refresh_mode="auto"` is an explicit compatibility mode that hashes sources before
each analysis. Use snapshot mode for the no-per-request-source-scan behavior.

`SourceDocument(path, title="", revision="unspecified", source_type="reference")`
selects a local reference. PDF extraction requires the documents extra. Type/revision
metadata are declared, not independently verified.

## Brief fields

| Field | Meaning |
|---|---|
| `requirement` | Original user request |
| `evidence` | Retrieved source excerpts, local IDs, hashes and optional PDF pages/source metadata |
| `scope` | Model-recommended folders, reasons and citations |
| `constraints` | Model-selected constraints with origin, quotation, applicability and relevance |
| `questions` | Consequential unresolved choices and alternative effects |
| `interpretations` | Proposed interpretation, not a verified fact |
| `unresolved` | Remaining gaps/conflicts |
| `snapshot` | Capture ID/time, HEAD, counts and selection policy |
| `investigation` | Status, tool events and evidence-character use |
| `decisions` | Saved scoped clarifications and snapshot-relative status |
| `warnings` | Known extraction, model or snapshot limitations |

`to_dict()` supports JSON serialization and retains full source hashes.
`to_markdown()` creates a readable brief without repeated source hashes.
Use `to_markdown(include_provenance=True)` to append distinct source fingerprints.
Investigation status is `completed`, `budget_exhausted` or `failed`. Completed means
the model elected to stop; it does not certify coverage or correctness.

## Snapshot tools

- `folders(prefix)`: immediate stored subfolders and counts.
- `symbols(query,prefix)`: literal symbol-name-fragment lookup.
- `search(query,prefix)`: lexical retrieval; prefix is literal and case-sensitive.
- `read_symbol(path,symbol)`: all indexed chunks of an exact symbol within the budget.
- `read(path,start,end)`: indexed line range, at most 120 lines.
- `neighbors(path,symbol)`: syntactic call-name matches, not resolved call targets.
- `read_document(path,page)`: selected indexed reference page.

MCP exposes these through `snapshot_lookup`. References use their indexed
`@documents/...` paths. PDF line numbers are local to extracted page text.

## Errors and transport

CLI codes: 0 returned report, 2 input/configuration error, 3 failed model investigation.
No automatic model retries are performed. The default HTTP adapter uses a 60-second
request timeout and JSON-object chat responses; custom adapters supply their own
transport policies. A per-call timeout is not an overall investigation deadline.
