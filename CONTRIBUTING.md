# Contributing

## Development setup

```bash
python -m venv .venv
# Activate the environment using your shell's activation command.
python -m pip install -e ".[c,documents,mcp]"
python -m unittest discover -s tests -v
python tests/integration/mcp_smoke.py
```

See [testing](docs/testing.md) for coverage and optional dependencies.

## Changes and pull requests

Keep each change focused. Describe the problem, resulting behavior and validation.
Update the relevant guide when public behavior changes. Add regression coverage
for behavioral fixes, particularly snapshot reuse, refresh rollback and evidence bounds.

Do not add repository-specific keyword rules to improve individual evaluation cases.
Semantic interpretation belongs to the model; structural tools and validation belong
to the library. Unit tests use scripted models and do not measure reasoning quality.

Keep benchmark runs, generated reports, source snapshots, credentials and private
repository content out of commits. Reproduce experiments locally and summarize
relevant results in the PR instead of adding raw output to the project.

## Release status

The owner must select a project license before an open-source release. Dependency
provenance is documented in [provenance](docs/provenance.md).
