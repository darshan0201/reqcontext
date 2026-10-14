> Historical report for an earlier release. Use README.md and RESEARCH_DESIGN.md for v0.4.0 behavior and usage.

# NVMe check and ease-of-use update: v0.3.0

Repository: https://github.com/linux-nvme/nvme-cli

Exact checked revision: `cd1449b72e18cea3a4f669e0bf72d6227d27ce10`.
Read source only; no device, firmware download, sanitize operation, repository
build or test-suite execution was involved.

## What the check revealed

v0.2.0 indexed 569 eligible files, but skipped C and headers. It could return
manual pages but could not ground requirements in the main C implementation.
The four fixed queries are in `benchmarks/nvme_eval.py`. Before/after rankings are
in `benchmarks/nvme-baseline.json` and `benchmarks/nvme-v030.json`.

v0.3.0 adds `.c` and `.h` text indexing and an optional Tree-sitter C adapter.
With the adapter installed, 1,089 eligible files were indexed. The first analysis
took 2.78 seconds in this environment; the remaining three took 113–136 ms each.
These are single observations, not a statistically rigorous speed benchmark;
the earlier release processed much less content, so the two timings are not a
like-for-like optimization comparison.

## Observed results (top five evidence entries)

| Request | Useful evidence found | Remaining issue |
|---|---|---|
| Report reservation registrants as JSON | `src/nvme-print-json.c::json_nvme_resv_report` at rank 1; `plugins/resv/resv-plugin.c::resv_report_size` at rank 2 | Main `resv_report` handler was not in the top five |
| Firmware download in chunks with offset | `plugins/fw/fw-plugin.c::fw_download` at rank 3 | Documentation and a Windows library helper ranked higher |
| Sanitize progress log | `src/nvme-print-stdout-log.c::stdout_sanitize_log` at rank 5 | Main `plugins/log/log-plugin.c::sanitize_log` handler was absent |
| Error log with configurable entry count | `plugins/log/log-plugin.c::get_error_log` at rank 4 | Vendor-specific code occupied the first three results |

This is a smoke evaluation, not a claim of complete requirement understanding or
four fully solved requests. Useful evidence was found, but cross-file relationship
traversal and intent-aware ranking remain gaps. No NVMe-specific vocabulary patch
was used to force these results.

## What heuristic means here

The offline question generator uses explicit rules. For example, if the requirement
contains "retry" but no retry-limit wording, it suggests asking about limits. Such a
rule cannot determine whether an existing implementation already answers the
question, or infer arbitrary domain behavior. Lexical retrieval likewise ranks
word matches; it is not semantic understanding. A model adapter can provide richer
interpretations, but no live model was exercised in this evaluation.

## Easier usage

From the extracted `reqcontext` project directory:

```bash
python -m pip install ".[c]"
```

Then, from the target repository:

```bash
reqcontext --requirement "Report reservation registrants in JSON format"
```

Or use a text file (multi-line requirements work):

```bash
reqcontext /path/to/nvme-cli --requirement-file requirement.txt
```

The single-call Python interface automatically creates/updates the index, returns
a brief and closes the database:

```python
from reqcontext import analyze

brief = analyze(
    "Report reservation registrants in JSON format",
    repo="/path/to/nvme-cli",
)
print(brief.to_markdown())
```

`repo` defaults to the current directory. No manual indexing step, vector database,
API key or GPU is required. Use `--requirement-file -` to read standard input.
The package is delivered locally; it has not been published to PyPI.

Without the `[c]` extra, C/header files remain searchable as plain text and a warning
explains the missing symbol extraction. Python parsing continues to use the standard
library. Installing/removing the parser causes a derived-index rebuild on the next
new context instance while preserving saved clarifications.

## Validation and boundaries

36 tests passed with Tree-sitter 0.25.2 and tree-sitter-c 0.24.2. New cases cover the
one-call API, current-directory/stdin CLI, C function/call extraction, multiline
pointer-return declarations, missing-parser fallback and capability-change cache
rebuilds. No live LLM evaluation was performed.

C parsing is syntactic: macros are not expanded, compilation flags and active
preprocessor branches are not resolved, call targets are not linked, and C++ is
not supported by this adapter. Header macros and structs remain text evidence.
Source names and calls do not establish runtime behavior. Repository edits during
analysis are not an atomic snapshot.
