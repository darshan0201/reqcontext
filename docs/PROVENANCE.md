# Implementation and evidence provenance

The ReqContext implementation was developed in this workspace with AI assistance
from the user's design requirements. We did not import implementation files from
Aider, Continue or CodeGraph. Their documentation was consulted to assess overlap
and design approaches; this is not a guarantee that every general technique is novel.

## Runtime dependencies

| Dependency | Use | Observed distribution metadata |
|---|---|---|
| tree-sitter / tree-sitter-c | Optional C parsing | See tree-sitter distribution notices; tree-sitter-c reports MIT |
| pypdf | Optional PDF text extraction | BSD-3-Clause |
| mcp | Optional stdio server/client integration | MIT |

These are third-party dependencies, not original implementations of those parsers
or protocols. Transitive dependencies are installed separately and are not bundled
into our wheel. Check the actual locked distributions before publishing a release.

## Repository evidence

The manually facilitated NVMe audit records contain attributed excerpts from
nvme-cli and its vendored libnvme. Their license texts are retained under
`benchmarks/agent-audit/licenses/`. Historic baseline folders contain our own earlier
ReqContext implementations, not competitor source code.

HTTPX evaluation records store paths, symbol names, commit and rankings rather than
copying its implementation into our library. The evaluated repository itself is not
bundled. The public research PDF used for extraction smoke testing is not bundled.

## Release status

The project has no selected license or package publication yet. Source availability
does not establish open-source licensing. No external adoption is claimed.
