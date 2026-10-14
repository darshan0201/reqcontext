> Historical report for an earlier release. Use README.md and RESEARCH_DESIGN.md for v0.4.0 behavior and usage.

# Multi-repository evaluation: ReqContext 0.2.0

## Scope and method

Cloned three public GitHub repositories and analyzed their source, tests and documentation without executing their project code. Only the 281 eligible files were indexed; excluded/unsupported files are not part of this count. No live LLM was used.

Twelve manually authored requirements and expected primary implementation targets were fixed before running the baseline. Six queries were used to inspect retrieval failures and guide changes; the other six were reserved for generalization checks. Intermediate aggregate counts for the reserved set were visible, so this is a development split, not a fully blinded holdout study. Query-level reserved results were not used to tune the implementation.

A file hit means the expected file appeared in the first five evidence entries. A symbol hit means the exact expected symbol, or a member of the expected class when a class was the target, appeared there. These targets are illustrative primary locations, not exhaustive labels of all valid code. They do not evaluate whether an implementation would be correct.

## Repositories

| Repository | Eligible files | Exact commit |
|---|---:|---|
| [click](https://github.com/pallets/click.git) | 142 | `2247b35ea1c47c727d7a06e51fa280e12a863ff6` |
| [requests](https://github.com/psf/requests.git) | 61 | `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60` |
| [jinja](https://github.com/pallets/jinja.git) | 78 | `5ef70112a1ff19c05324ff889dd30405b1002044` |

## Retrieval results

| Metric | v0.1.0 | v0.2.0 |
|---|---:|---:|
| All 12: file hits@5 | 10/12 | 12/12 |
| All 12: symbol/family hits@5 | 4/12 | 11/12 |
| Development 6: file hits@5 | 6/6 | 6/6 |
| Development 6: symbol/family hits@5 | 2/6 | 5/6 |
| Reserved 6: file hits@5 | 4/6 | 6/6 |
| Reserved 6: symbol/family hits@5 | 2/6 | 6/6 |

## Performance

Cold means a fresh ReqContext index, not a cleared operating-system filesystem cache. Cold timings are single runs; warm timings are medians of five refreshes. All times are environment-specific, with no statistical confidence claim.

| Repository | Cold before → after | Warm before → after | Index size reduction |
|---|---:|---:|---:|
| click | 612 → 468 ms | 16.0 → 14.2 ms | 31.2% |
| requests | 238 → 170 ms | 7.5 → 8.0 ms | 30.0% |
| jinja | 470 → 314 ms | 9.3 → 11.6 ms | 34.7% |

Initial indexing improved by 23.5–33.2% in these runs. Warm timing was mixed: Requests and Jinja were slightly slower. No general warm-speedup claim is made. Refresh still reads and hashes all eligible files for correctness.

## Changes driven by observations

1. **One AST traversal:** profiling the baseline Click cold index attributed roughly 0.95 seconds of a 1.45-second profiled run to recursive chunk collection, with repeated subtree walks. The collector now records definitions and calls in one visitor traversal. Profiled timings have instrumentation overhead and are not the table timings.
2. **Symbol-owned chunks:** plain windows previously displaced function evidence. Every Python window now retains its narrowest lexical owner, including late lines in long functions. Nested calls no longer leak to parents.
3. **No duplicate source windows:** replaced overlapping full-function excerpts plus plain text windows with one non-overlapping partition. This reduces cache size.
4. **More useful candidate selection:** a wider bounded candidate pool, one result per symbol, and modest source/test priors reduce test-helper crowding for implementation requests. Explicit test requests disable the prior.
5. **Upgrade compatibility:** derived indexes rebuild on schema-version change; saved decisions survive.

## Remaining failure

“Reload a cached template when its source file changes” retrieves `src/jinja2/environment.py` but misses `Environment._load_template` in its top five. The top results emphasize the class documentation and loader methods. This illustrates lexical retrieval's remaining inability to reliably traverse from described behavior to the exact implementation. No repository-specific keyword patch was added.

## Correctness and limitations

30 unit/integration tests pass, including seven new regressions for long-function ownership, nested calls, complete non-overlapping coverage, symbol deduplication, migration persistence and explicit test retrieval. Packaging and CLI were checked. These tests do not establish real-model interpretation quality, prompt-injection robustness or performance on every language/repository.

Raw before/after query rankings and metadata: `benchmarks/baseline.json` and `benchmarks/optimized.json`. Runner: `benchmarks/multi_repo.py`. Baseline implementation: `benchmarks/baseline_v010/`.
