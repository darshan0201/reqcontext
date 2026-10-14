# ReqContext

Repository context for AI coding agents, built from a reusable source snapshot.

Give ReqContext an implementation requirement. It retrieves relevant code and lets
an LLM identify the folders to inspect, constraints to consider and decisions that
need clarification. After the initial snapshot, queries reuse stored evidence
instead of scanning the entire repository again.

## What it does

- Indexes Python and C source, symbols and folder structure in SQLite.
- Offers scoped search and symbol lookup through a Python API, CLI or MCP server.
- Lets a configured model investigate evidence and produce a cited implementation brief.
- Stores task-specific clarification answers and explicitly selected PDF/text references.
- Refreshes the snapshot on request, with rollback if an unexpected update fails.

ReqContext supplies context; it does not implement the requested code change.
Search is lexical. Interpretation and clarification selection are performed by the model.

## Quick start

Requires Python 3.11+ and SQLite with FTS5. From a checkout of this repository:

```bash
python -m pip install -e .
reqcontext snapshot build examples/upload_app --output example.db
reqcontext examples/upload_app --snapshot example.db --requirement "Add upload retries" --retrieval-only
```

This example runs without an API key and returns source matches. For model-generated
folder recommendations and clarifications, configure `REQCONTEXT_BASE_URL` and
`REQCONTEXT_MODEL`, plus `REQCONTEXT_API_KEY` if your endpoint requires it. Store keys
in your local environment. The endpoint must support JSON chat-completion responses.

```python
from reqcontext import analyze

brief = analyze(
    "Add upload retries",
    repo="examples/upload_app",
    snapshot="example.db",
)
print(brief.to_markdown())
```

The Markdown brief lists source locations and conclusions. Full source fingerprints
remain available in `brief.to_dict()` or `brief.to_markdown(include_provenance=True)`.

## MCP and optional features

```bash
python -m pip install -e ".[c,documents,mcp]"
python -m reqcontext.mcp_server --repo /path/to/project --snapshot /path/to/snapshot.db
```

An MCP client's existing model can use the snapshot tools directly. See the
[usage guide](docs/usage.md) and [client configuration](integration/mcp-client.example.json).
The package is not currently published to PyPI.

## Project layout

| Directory | Purpose |
|---|---|
| `reqcontext/` | Library, CLI and MCP implementation |
| `tests/` | Unit tests and the MCP integration check |
| `docs/` | Usage, API, architecture and development guidance |
| `examples/` | Small source repository for the quick start |
| `integration/` | Example MCP client configuration |
| `.github/` | CI and contribution templates |

## Documentation

- [Usage and MCP setup](docs/usage.md)
- [API reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Testing](docs/testing.md)
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)

## Limits and privacy

Snapshot evidence stays frozen until refresh. Source relationships are syntactic;
PDF extraction does not provide OCR. Model conclusions require review. A remote
model receives selected excerpts, and the index is not a secret detector: only use
repositories and references you are permitted to send to that endpoint.

The initial target is one engineer/client. Concurrent refresh writers and large
monorepositories have not been validated. See [provenance](docs/provenance.md) for
dependency information. A project license has not yet been selected.
