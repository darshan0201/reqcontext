# Requirement context

## User requirement

Add retry support for firmware download when the transfer fails.

## Repository evidence

- **E1** `Documentation/nvme-fw-download.txt:1-24` — text
  SHA-256: `5efbcdb6a73ec79eac0ffeab74e778bfb85e418acb4ff48bb5f9fc33cffd0594`
- **E2** `tests/cli/micron/micron_options_mock_test.py:531-541` — TestMicronSelectDownload.test_download_failure_stops_the_transfer
  SHA-256: `ec0e634a8041f080adcfd6a4d576034a7c1eb571c6d7e2a33a54d6e20e7a8d23`
- **E3** `Documentation/nvme-fw-download.txt:49-72` — text
  SHA-256: `5efbcdb6a73ec79eac0ffeab74e778bfb85e418acb4ff48bb5f9fc33cffd0594`
- **E4** `plugins/fw/fw-plugin.c:39-62` — fw_download_single
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E5** `Documentation/nvme-fw-download.txt:73-95` — text
  SHA-256: `5efbcdb6a73ec79eac0ffeab74e778bfb85e418acb4ff48bb5f9fc33cffd0594`
- **E6** `plugins/fw/fw-plugin.c:63-86` — fw_download_single
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E7** `plugins/fw/fw-plugin.c:87-110` — fw_download_single
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E8** `plugins/fw/fw-plugin.c:111-123` — fw_download_single
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E9** `plugins/fw/fw-plugin.c:124-124` — text
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E10** `plugins/fw/fw-plugin.c:125-142` — fw_read_full
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E11** `plugins/fw/fw-plugin.c:145-168` — fw_download
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E12** `plugins/fw/fw-plugin.c:169-192` — fw_download
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E13** `plugins/fw/fw-plugin.c:193-216` — fw_download
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E14** `plugins/fw/fw-plugin.c:217-240` — fw_download
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E15** `plugins/fw/fw-plugin.c:241-249` — fw_download
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E16** `plugins/fw/fw-plugin.c:250-264` — fw_download
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E17** `plugins/fw/fw-plugin.c:265-288` — fw_download
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E18** `plugins/fw/fw-plugin.c:289-303` — fw_download
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E19** `plugins/fw/fw-plugin.c:304-304` — text
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E20** `plugins/fw/fw-plugin.c:305-317` — nvme_fw_status_reset_type
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E21** `plugins/fw/fw-plugin.c:318-318` — text
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E22** `plugins/fw/fw-plugin.c:319-339` — fw_commit_support_mud
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E23** `plugins/fw/fw-plugin.c:340-340` — text
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E24** `plugins/fw/fw-plugin.c:341-356` — fw_commit_print_mud
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E25** `plugins/fw/fw-plugin.c:357-357` — text
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`
- **E26** `plugins/fw/fw-plugin.c:358-365` — fw_commit_err
  SHA-256: `d44ac856ad90dfe4afe93878cc7058ab1a66c758dab7b2d39b7342699e1dc287`

## Observations

- Static function definition found: TestMicronSelectDownload.test_download_failure_stops_the_transfer. (evidence: E2)
- Static function definition found: fw_download_single. (evidence: E4)

## Clarifications

- The core command already makes up to three attempts per chunk. Is the requested change a configurable attempt/backoff policy, or support for a specific failing command/path that this loop does not recover? (evidence: E4, E6, E8, E17, E18)

## Proposed interpretations — not verified facts

- The canonical firmware-download command already retries through fw_download_single. The requirement needs refinement into a change to existing retry behavior rather than the addition of a second retry loop. (evidence: E4, E6, E17, E18)

## Selected constraints

- [implementation_observation] Existing retry policy permits at most three total submission attempts per chunk; three attempts should not be described as three extra retries. — plugins/fw/fw-plugin.c::fw_download_single at this revision; max_retries is 3 in the same excerpt. (evidence: E4)
- [implementation_observation] The current helper stops resending NVMe errors carrying DNR. — Positive NVMe-type error responses in fw_download_single; not a verified statement of all transport behavior. (evidence: E6)
- [implementation_observation] An overlapping-range response is either accepted with ignore_ovr or made non-retryable otherwise. — Non-ignored overlapping firmware-range errors in the existing core helper. (evidence: E6, E7, E8)
- [implementation_observation] The caller stops advancing chunks when fw_download_single returns an error. — The core fw_download chunk loop, including its stream and mapped-buffer paths. (evidence: E17, E18)

## Unresolved

- No NVMe specification revision was supplied; DNR and overlapping-range behavior above are source observations, not independently verified normative requirements.
- Vendor-specific firmware commands are not established to share the core helper; the Micron seed test is insufficient evidence for a repository-wide retry policy.

## Saved clarifications

None.

## Limitations / warnings

- Semantic interpretation and question selection require a configured model.
- Static symbol/call observations do not prove runtime reachability or behavior.
- Evidence is a snapshot; refresh before acting if the workspace changes.
- Model review and matching quotations do not prove semantic correctness.
