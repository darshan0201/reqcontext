# ReqContext

Persistent project orientation for fresh AI coding sessions.

Build a folder map once, then let new sessions load responsibilities and follow
relevant component relationships without rediscovering the entire repository.
Pass any directory path; ReqContext keeps its cache outside that project and
requires no repository restructuring.

## What it does

- Saves folder structure and optional model-written responsibility summaries.
- Offers quick sampling or an explicitly selected full eligible-text scan.
- Records Python import relationships with file and line evidence.
- Refreshes explicitly, reusing summaries and tracking pending component changes.
- Exposes cached orientation through Python, CLI, MCP and a SessionStart adapter.
- Retains a separate SQLite source snapshot for deeper scoped investigation.

ReqContext supplies navigation context; the coding agent interprets the requirement
and inspects current source before editing. It does not guarantee complete impact
analysis or automatically implement a change.

## Quick start: reusable project orientation

Requires Python 3.11+. Install from this checkout, then supply any directory:

```bash
python -m pip install -e .
reqcontext map build /path/to/project
reqcontext map session /path/to/project
reqcontext map describe /path/to/project --folder src
```

Build traverses internally once and stores a compact map outside your project.
Repeated builds and session reads reuse it. Refresh when structure or responsibilities change:

```bash
reqcontext map refresh /path/to/project
```

For model-written folder descriptions, configure `REQCONTEXT_BASE_URL`,
`REQCONTEXT_MODEL` and, if required, `REQCONTEXT_API_KEY`, then use
`reqcontext map refresh /path/to/project --with-model`. This sends bounded source
samples to that endpoint. Without a model, briefs are labeled documentation excerpts
or inventories; semantic folder understanding is not claimed.

For mixed-purpose folders or deeper coverage, opt into full mode:

```bash
reqcontext map refresh /path/to/project --mode full --with-model
reqcontext map related /path/to/project --folder src
```

Full mode sends all eligible text through bounded chunks when a model is enabled.
It reports exclusions and parse failures; relationships currently cover static
Python imports only. Subsequent refreshes preserve scan mode. Ordinary changes
accumulate per folder until the summary threshold (default five changed files);
structural and shared-dependency changes bypass it. See [limits and refresh rules](docs/usage.md#explicit-full-scan-and-component-relationships).

For automatic Claude Code session context, merge the hook example in
[integration/claude-session-start.example.json](integration/claude-session-start.example.json)
into your user-level settings. Use the Python interpreter where ReqContext is installed.
No repository layout changes are required. Build the map for the session's working
directory first. See [project map usage](docs/usage.md#persistent-project-orientation).

The original source-snapshot API remains available for deeper investigation.

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
