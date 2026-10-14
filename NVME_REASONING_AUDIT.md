# NVMe requirement reasoning audit and v0.4.1 improvements

Repository: https://github.com/linux-nvme/nvme-cli
Revision: `cd1449b72e18cea3a4f669e0bf72d6227d27ce10`.

## Evaluation method and limits

Two requirements were investigated through the real v0.4.0 model-interface loop.
The ChatGPT assistant inspected each emitted request and authored its next response;
the library executed the selected tools and validated the final reports. Responses
were recorded only after inspecting actual retrieved evidence. This was a manually
facilitated assistant audit, not autonomous inference through ChatModel, a blinded
benchmark, or a comparison across models. The assistant had broader conversation
context, so this does not isolate model behavior under the serialized prompt alone.
No GPU/API throughput, provider token cost or semantic accuracy percentage is claimed.

The synchronous replay harness in `benchmarks/interactive_eval.py` replays prior
recorded responses and emits the next request. Its purpose is to inspect the
interface. Replaying these responses later is not a new intelligence evaluation.

No NVMe commands, firmware downloads, sanitize operations or device tests were run.
The code was analyzed only. No external NVMe specification was used, so findings
are source observations and conditional design implications, not certified compliance
requirements or a reproduced firmware/controller defect.

## Case 1: firmware retry

Requirement: “Add retry support for firmware download when the transfer fails.”

The assistant chose to read the core helper, its caller and the chunk loop after
initial retrieval surfaced an existing `max_retries = 3` declaration.

Observed:
- The canonical helper already makes at most three attempts, not three additional
  retries. A second retry loop could multiply submissions.
- Its current status handling suppresses NVMe DNR resends.
- Overlapping-range responses use special handling controlled by `ignore_ovr`.
- The caller stops advancing chunks on helper failure.
- The Micron test returned by initial search is vendor-specific; it was not treated
  as a universal policy for the core firmware command.

Selected clarification: does the user want configuration/timing changes to existing
retries, or recovery for a particular failure or different path?

The final brief has four source-linked constraints and one consequential question.
See `benchmarks/agent-audit/fw-retry/brief.md` and the captured requests/responses.

## Case 2: changing reservation count

Requirement: “Handle reservation reports when the registrant count changes between reads.”

The assistant read the command's sizing helper and second-read logic, then explicitly
searched the output dispatch and JSON/text printers rather than stop at the man page.

Observed:
- Automatic sizing uses the first header's registrant count for the second transfer.
- The inspected command prints the second response without another capacity check.
- JSON and normal output bound descriptor iteration to buffer capacity in ordinary
  and extended layouts. Bounds protection alone does not establish report completeness.
- A nonzero configured `numd` selects fixed-length behavior.
- Changing allocation requires reinitializing command length fields, not merely
  repointing the buffer.
- If the first count is zero, the current condition skips the second read; handling
  registrations after that read is another scope question.

Selected clarification: bounded refetching until the report fits the latest observed
count, or explicitly marked partial output? A stable membership generation is a
separate requirement; merely fitting the count does not establish snapshot stability.

The final brief has four source-linked constraints and one consequential question.
See `benchmarks/agent-audit/reservation/brief.md` and the captured requests/responses.

## What this establishes

The interface can support source-dependent investigation and select different
questions for different requests, without a retry/reset keyword template. It can
expose an already-implemented feature and distinguish current code from desired
behavior. It does not establish that an arbitrary configured model will do this
reliably. A subsequent unattended, labelled evaluation is still required.

## Improvements implemented as v0.4.1

1. **Exact-symbol reads:** broad line reads included unrelated neighboring functions.
   The model now has `read_symbol(path, symbol)` to collect only the named symbol's
   indexed chunks, subject to the evidence-character budget. A real-repository smoke
   check isolated `fw_download_single` without adjacent commit/other helpers.
2. **C macro parse guard:** an unexpanded constructor macro caused Tree-sitter to
   label a region as a function named `void`. The adapter now requires a structural
   function declarator before accepting a function symbol. Unsupported macro-shaped
   regions remain text evidence instead of a fabricated function definition.
3. **Regression coverage:** 49 tests pass, including the macro case, symbol-only
   reading and bounded symbol-read evidence. Final audit quotations/citation IDs
   also pass replay validation against the exact captured evidence snapshots.

The audit records describe v0.4.0 source extraction. The macro guard changes chunk
boundaries in v0.4.1, so replay validation uses captured evidence; do not assume old
IDs match a fresh index. Historic records may contain the old unsupported `void`
label, which was not used as a final constraint.

## Reproduction

From the project directory:

```bash
python -m unittest discover -s tests -v
PYTHONPATH=. python benchmarks/validate_audit.py
```

For fresh unattended evaluation, configure your selected model endpoint as described
in README.md and call `analyze(requirement, repo=...)`. Keep the model/version,
repository revision, requirement set and human-reviewed expected constraints fixed.
Measure applicable constraints, unsupported interpretations, unnecessary questions,
missed questions and downstream implementation success. The counts of questions in
this audit are descriptive, not a quality metric on their own.

## Third-party excerpt notices

Audit requests contain excerpts of nvme-cli and its vendored libnvme sources.
Original sources and copyright/SPDX notices belong to their respective authors.
License texts are retained under `benchmarks/agent-audit/licenses/`. The recorded
source excerpts are for reproducibility of the evidence inspection.
