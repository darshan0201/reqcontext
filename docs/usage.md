# Snapshot-first investigation and MCP adapter

## Behavior

Build the snapshot once. It stores eligible source excerpts, folder counts, Python/C
symbols, syntactic call-name relationships, hashes and reference-document excerpts.
Ordinary analysis and plugin lookup use SQLite only; they do not enumerate, read or
hash live source/reference files. The first request builds a missing snapshot, and
an incompatible index-format upgrade rebuilds it once. Filesystem checks for the
repository/cache location are still performed; the zero-read guarantee concerns
source files, not the SQLite database itself.

The model sees the compact root folder map and search candidates, chooses folders,
then can search within a selected prefix or read selected symbols. The final report
can include `scope` entries with a folder, reason and supporting evidence IDs. The
runtime verifies that the cited evidence belongs to that folder. It does not prove
that the selected folders are exhaustive or semantically correct.

Example desired brief (illustrative, not a new model result):

| Folder | Why inspect it |
|---|---|
| `plugins/fw` | Core firmware-download handler and retry helper |
| `Documentation` | Firmware command options and documented behavior |
| `tests/cli` | Relevant tests, after identifying the applicable command/vendor |

The host should narrow further rather than read all files under these folders.

## Build and use

```bash
python -m pip install ".[c,documents,mcp]"
reqcontext snapshot build /path/to/repo --output /path/to/repo-snapshot.db
reqcontext /path/to/repo --snapshot /path/to/repo-snapshot.db --requirement "Add retry support to firmware download"
```

The final command uses the REQCONTEXT model settings from [README.md](../README.md). To inspect
source matches without a model, add `--retrieval-only`. To explicitly refresh:

```bash
reqcontext snapshot refresh /path/to/repo --output /path/to/repo-snapshot.db
```

A refresh enumerates and hashes eligible files, but reparses only changed content.
It rebuilds derived folder/call-name maps from the index. It is not an event watcher
or Git-diff-only refresh. No automatic source-freshness promise is made. Captured
HEAD can differ from file content due to uncommitted edits; each excerpt has a hash.
Snapshot evidence remains frozen until refresh. Source-bound clarifications are
compared against that snapshot, not live source files.

Snapshot caches are bound to their original repository root. This release does not
provide portable/offline snapshots after the original repository directory is moved
or removed. Exclusion/document-manifest changes require an explicit refresh.

## Python API

```python
from reqcontext import analyze, SourceDocument

brief = analyze(
    "Handle reservation reports when registrant count changes",
    repo="/path/to/nvme-cli",
    snapshot="/path/to/repo-snapshot.db",
)
print(brief.scope)
```

For an explicit build/refresh with revision-labelled references:

```python
from reqcontext import RequirementContext, SourceDocument

with RequirementContext(
    "/path/to/repo", cache="/path/to/repo-snapshot.db",
    documents=[SourceDocument(
        "/path/to/spec.pdf", title="Device Specification",
        revision="2.4", source_type="specification",
    )],
) as context:
    context.refresh()
```

Text/PDF references must be explicitly selected. The PDF extra uses pypdf, preserves
page numbers and warns about extraction limitations and textless pages. No OCR,
diagram interpretation, password decryption or perfect table extraction is provided.
Limits: 50 MB input, 500 PDF pages, 2 million extracted characters per reference.
Source type/revision are user-supplied metadata; the model must assess applicability.

Omitting reference selections on an explicit refresh removes previously imported
reference records. Reopening an existing snapshot without refresh preserves its
stored references and requires no access to their original files.

## MCP plugin-style use

The adapter is a local stdio MCP server; it is not an automatically installed
ChatGPT marketplace plugin. Add it to a client that supports stdio MCP using your
client's configuration format. [MCP client example](../integration/mcp-client.example.json) is an example
of the common `mcpServers` format; replace paths and use the Python interpreter in
which the package/extras are installed. Windows accepts absolute Windows paths in
JSON with appropriate escaping. Configure documents with repeated `--document` args
if the server should include them when refreshing.

```bash
python -m reqcontext.mcp_server --repo /path/to/repo --snapshot /path/to/repo-snapshot.db
```

Tools:
- `repository_overview`: captured revision/time and folder map.
- `snapshot_lookup`: folder and symbol-fragment listing, scoped search, source/symbol/document reads,
  and syntactic caller/callee name matches from the snapshot.
- `refresh_repository_snapshot`: explicit source refresh.
- `analyze_requirement`: optional nested model-driven analysis.

**No separate model endpoint is necessary for overview/lookup:** the MCP host's
existing model reasons over their results. The optional `analyze_requirement` tool
requires a separately configured endpoint because it runs the library's own loop.
The SDK extra deliberately targets the documented v1 API and was tested with mcp
1.30.0. This is not a v2 SDK adapter.

The server opens a new context per tool invocation so SQLite connections do not
cross tool threads. It has not been load-tested for multiple concurrent refresh
writers. Initial deployment target is one engineer/client.

## v0.5.1 refresh publication

Refresh uses one SQLite transaction for source/reference rows, derived maps and capture metadata. Unexpected failure preserves the previous snapshot. Individually failed references are removed with warnings in an otherwise successful refresh. This does not make filesystem capture atomic or automatically detect stale files.

## Provider interoperability

The integration boundary is the MCP tool interface. The host chooses its model;
ReqContext supplies repository evidence. Host-driven lookup does not require the
library's own model API key or a second reasoning endpoint.

| Integration path | Current status |
|---|---|
| MCP over local stdio | Automated SDK client/server smoke coverage |
| OpenAI and Anthropic coding clients | Intended integration targets; individual client validation pending |
| Other clients supporting compatible stdio MCP tools | Protocol-level integration path; client-specific validation required |
| Direct chat-completions-compatible endpoint | Adapter implemented; live provider compatibility not validated in CI |
| Native Anthropic Messages API | No built-in adapter; use host-driven MCP or supply a model callable |
| Remote HTTP MCP hosting | Not implemented |

The JSON configuration under `integration/` illustrates a common client schema;
it is not a universal configuration format. Check the chosen client's supported
transport and configuration before connecting it.

Client compatibility is distinct from company adoption. Do not claim that OpenAI,
Anthropic or another company uses, endorses or has validated this project.
