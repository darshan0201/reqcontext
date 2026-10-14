# v0.5.0 implementation and validation

## Delivered

- Snapshot-first analysis: no whole-source scan per requirement; explicit refresh.
- Cached folder map, scoped search and model-selected folder brief with citations.
- Indexed caller/callee name lookup. It is syntactic, not a resolved call graph.
- Explicit local PDF/text references with title/revision/page/hash provenance.
- MCP stdio adapter that exposes snapshot tools to a host's own model.
- Matched-tools prompt-ablation runner and fixed NVMe grading criteria.

## Verification

60 tests passed with C/PDF/MCP extras available. New tests cover frozen snapshot
behavior, explicit refresh, no source/reference reads on reuse, scoped search,
call-name lookup, PDF page-local evidence identity, reference metadata updates,
removal of failed/removed reference evidence and folder citation validation.

Actual MCP stdio initialization, tool discovery and symbol lookup passed. Actual
PDF extraction/retrieval passed on a public text-extractable research PDF; page
metadata and extraction warnings were retained. These are mechanical integration
checks, not semantic interpretation benchmarks.

A real nvme-cli snapshot of 1,089 eligible files was searched with the live-source
enumerator deliberately blocked. Search scoped to `plugins/fw` returned only the
firmware plugin. Caller lookup linked the spelling `fw_download_single` to the
core `fw_download` caller in this revision. That does not resolve every macro,
function pointer, alias or dynamic call.

## Synthetic scale measurements

| Eligible Python files | Functions | Build + first query | Snapshot bytes | Repeated source reads |
|---|---:|---:|---:|---:|
| 1,000 | 6,001 | 0.57 s | 3,698,688 | 0 |
| 10,000 | 60,001 | 4.97 s | 36,491,264 | 0 |

Nine warm, narrow snapshot queries were measured per size. Median analysis time
was below 1 ms in this small-query synthetic workload; this excludes model calls
and reopening the context and is not a real-repository latency guarantee. Linux
process peak RSS reached approximately 43 MB, a cumulative high-water mark. No
end-to-end model latency, throughput or accuracy claim is made.

Raw evidence: `benchmarks/scale-v050.json`, `mcp-smoke-v050.json`,
`pdf-smoke-v050.json`, `nvme-snapshot-v050.json`.

## Comparative model evaluation

`benchmarks/compare_model.py` compares generic tool-agent guidance and ReqContext
investigation guidance with the same model, snapshot, tool set, final schema,
evidence-character cap and maximum calls. Arm order alternates. Outputs retain
provider token usage when available and require human grading. This is a controlled
prompt ablation, not a benchmark against a deployed coding assistant.

No endpoint is configured in this environment. The runner has not produced live
comparative results; no advantage over the generic arm is claimed. The NVMe criteria
were authored from earlier source inspections, so these are development cases,
not held-out novelty/quality evidence.

```bash
PYTHONPATH=. python benchmarks/compare_model.py /path/to/nvme-cli \
  --snapshot /path/to/nvme-snapshot.db \
  --cases benchmarks/nvme-requirements.json --output comparison.json
```

## Existing work and scope of novelty

The broad snapshot/repository-map idea already exists:
- Aider documents a concise repository map and graph-based selection within a token
  budget: https://aider.chat/docs/repomap.html
- Continue documents indexed artifacts and incremental reuse, including branch
  changes: https://github.com/continuedev/continue/blob/main/core/indexing/README.md
- CodeGraph MCP documents pre-indexed code lookup and synchronization:
  https://github.com/StarQuant/codegraph-mcp

These are overlap observations based on primary project documentation, not an
independent validation of their performance or maintenance. ReqContext's candidate
focus is resolving an incomplete requirement into applicable constraints and
consequential questions with revision-aware evidence. Novelty and usefulness are
unproven until evaluated against strong alternatives.
