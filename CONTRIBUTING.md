# Contributing

Create an isolated environment and install the project with the features you test:

```bash
python -m venv .venv
# Activate it using your platform's normal command.
python -m pip install -e ".[c,documents,mcp]"
python -m unittest discover -s tests -v
PYTHONPATH=. python benchmarks/mcp_smoke.py
```

Use snapshot-focused tests for new tools: verify no source enumeration on reuse,
source provenance, bounds, literal path scoping and explicit refresh behavior.
Add failure-injection coverage for snapshot changes. Model adapters in unit tests
are scripted; label them as mechanics tests, not semantic-quality results.

For a model comparison, fix repository commit, source selections, model/version,
requirements and grading criteria. Record model calls/usage and grade unsupported
claims, missed constraints and unnecessary questions. Do not tune on evaluation
examples and then describe them as held-out results.

Avoid repository-specific aliases or query patches added solely to pass an example.
Prefer structural tools or model-directed investigation improvements. Document
scope differences when comparing full search versus folder-scoped retrieval.

## Pull requests

Explain the concrete failure, resulting behavior, tests and limits. Use the template
under `.github/`. Keep edits focused. Do not commit credentials, local snapshots,
virtual environments, scraped private repositories or installed dependencies.
Include provenance/permission information for external excerpts or fixtures.

## Publishing

Before a public release, the owner must select the project's license, choose a
repository/maintainer identity and review included third-party evidence fixtures.
No project license is selected in this draft. Dependency licensing and source
excerpt notices are documented in `docs/PROVENANCE.md`.
