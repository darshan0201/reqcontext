# Non-storage repository validation: HTTPX

Repository: https://github.com/encode/httpx
Revision: `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`.
Selection was arbitrary and outside storage, not statistically random sampling.
The source was inspected; HTTPX's own test suite was not executed.

Six manually authored requests covered redirect authorization, environment proxies,
separate timeout settings, streamed response chunks, connection limits and per-request
cookie merging. Primary expected locations were reviewed in source before evaluation.

| Check | Result |
|---|---:|
| Expected file in initial top five | 6/6 |
| Expected symbol/class family in initial top five | 5/6 |
| Expected file in HTTPX-folder-scoped top five | 6/6 |
| Known-target exact-symbol lookup | 6/6 |
| Live repository enumeration during snapshot queries | Blocked by a test guard |

Exact-symbol lookup is not a discovery score: expected names were supplied to test
that the tool works. The proxy helper was missed by initial natural-language symbol
retrieval even though the correct file was retrieved. The new `symbols(query="proxy",
prefix="httpx")` tool can expose it for further model-directed reading; this does
not retroactively turn the initial score into 6/6.

Approximately 90 eligible files were indexed. v0.5.1 build time was about 0.29 seconds
and median query time about 2.7 milliseconds in one local run. No model calls are
included. A small manually labelled set does not establish universal accuracy.

Source inspection highlights why semantic review matters: redirect authorization
handling has a direct HTTP-to-HTTPS exception; `trust_env` affects configuration
beyond one proxy helper; and `iter_bytes` returns decoded data whereas `iter_raw`
serves a different purpose. Finding a file alone does not resolve those distinctions.
Those observations were reviewed manually, not produced by an unattended model run.

Raw rankings and timing: `benchmarks/httpx-v050-baseline.json` and
`benchmarks/httpx-v051.json`. Runner: `benchmarks/httpx_eval.py`.
