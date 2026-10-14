# Requirement context

## User requirement

Add upload retries

## Repository evidence

- **E1** `uploads.py:1-3` — text
  SHA-256: `698d5bc507d1177126cddb2d2adce527a412658567b072fb6ebeee91175d17b1`
- **E2** `policy.md:1-5` — text
  SHA-256: `29c8a2cf244938e6b2cf94d8cb4148d90b8fa8f1c777a93bc42b360522b6d294`
- **E3** `uploads.py:10-12` — foreground_upload
  SHA-256: `698d5bc507d1177126cddb2d2adce527a412658567b072fb6ebeee91175d17b1`
- **E4** `uploads.py:5-7` — background_upload
  SHA-256: `698d5bc507d1177126cddb2d2adce527a412658567b072fb6ebeee91175d17b1`
- **E5** `retry.py:5-12` — retry_call
  SHA-256: `31fbec969c995f4067b97fcc3987f242b55a223d64772fa57dbf99bc2fcd8124`
- **E6** `uploads.py:8-8` — text
  SHA-256: `698d5bc507d1177126cddb2d2adce527a412658567b072fb6ebeee91175d17b1`
- **E7** `retry.py:1-3` — text
  SHA-256: `31fbec969c995f4067b97fcc3987f242b55a223d64772fa57dbf99bc2fcd8124`

## Observations

- Static function definition found: foreground_upload. (evidence: E3)
- Static function definition found: background_upload. (evidence: E4)
- Static function definition found: retry_call. (evidence: E5)

## Clarifications

None.

## Proposed interpretations — not verified facts

None.

## Selected constraints

None selected.

## Saved clarifications

None.

## Limitations / warnings

- Semantic interpretation and question selection require a configured model.
- Static symbol/call observations do not prove runtime reachability or behavior.
- Evidence is a snapshot; refresh before acting if the workspace changes.

