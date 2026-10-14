# Requirement context

## User requirement

Handle reservation reports when the registrant count changes between reads.

## Repository evidence

- **E1** `plugins/resv/resv-plugin.c:266-280` — text
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E2** `Documentation/nvme-resv-report.txt:25-48` — text
  SHA-256: `482a288799ba662ef1dc519c6681f2d3f179031aff59aa725dd5b62c2dcfa05a`
- **E3** `NEWS.md:505-528` — text
  SHA-256: `c4e9d23dcb3c0975c69027cb1a612ee60c61521329301a42e7539d547f85e092`
- **E4** `NEWS.md:241-264` — text
  SHA-256: `c4e9d23dcb3c0975c69027cb1a612ee60c61521329301a42e7539d547f85e092`
- **E5** `plugins/resv/resv-plugin.c:363-386` — resv_report
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E6** `plugins/resv/resv-plugin.c:281-289` — resv_report_size
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E7** `plugins/resv/resv-plugin.c:290-290` — text
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E8** `plugins/resv/resv-plugin.c:291-313` — resv_report
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E9** `plugins/resv/resv-plugin.c:315-338` — resv_report
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E10** `plugins/resv/resv-plugin.c:339-361` — resv_report
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E11** `plugins/resv/resv-plugin.c:387-400` — resv_report
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E12** `plugins/resv/resv-plugin.c:401-410` — resv_report
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E13** `plugins/resv/resv-plugin.c:411-423` — resv_report
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E14** `plugins/resv/resv-plugin.c:424-447` — text
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E15** `plugins/resv/resv-plugin.c:448-463` — text
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E16** `plugins/resv/resv-plugin.c:465-469` — void
  SHA-256: `ff25added1a164fe15c24ff043b2df7b12f9e80fd68003cb2b7762579cb9b7a1`
- **E17** `Documentation/nvme-resv-report.txt:49-69` — text
  SHA-256: `482a288799ba662ef1dc519c6681f2d3f179031aff59aa725dd5b62c2dcfa05a`
- **E18** `src/nvme-print.c:887-891` — nvme_show_resv_report
  SHA-256: `4bb214db1c47981761dc5c0d1bd1af126865a78a7b3a27414ddb6a807eb670ab`
- **E19** `src/nvme-cmds-deprecated.c:1456-1478` — text
  SHA-256: `b3e39526d9e6b72428122060ae1664d5d70fa5966ef03bba1a3d548c9a9fccd0`
- **E20** `src/nvme-cmds-deprecated.c:761-764` — resv_report
  SHA-256: `b3e39526d9e6b72428122060ae1664d5d70fa5966ef03bba1a3d548c9a9fccd0`
- **E21** `libnvme/src/nvme/nvme-cmds-nvm.h:435-453` — nvme_init_resv_report
  SHA-256: `cb3fafd303e449a84dd08a37b5247a36fa673b56033f417685fc8a658752d7df`
- **E22** `src/nvme-print-json.c:636-659` — json_nvme_resv_report
  SHA-256: `73d5761db2f6a24b764d47f2ec77f26f092e7e74076cc196b8f5be4c87469729`
- **E23** `src/nvme-print-stdout.c:1877-1900` — stdout_resv_report
  SHA-256: `4a226cf7b3a7a7a4ea7e356ca4d3267eddb3208ac934d2b699dcd4bbdf36a6aa`
- **E24** `src/nvme-print-json.c:660-682` — json_nvme_resv_report
  SHA-256: `73d5761db2f6a24b764d47f2ec77f26f092e7e74076cc196b8f5be4c87469729`
- **E25** `src/nvme-print-json.c:684-695` — json_nvme_resv_report
  SHA-256: `73d5761db2f6a24b764d47f2ec77f26f092e7e74076cc196b8f5be4c87469729`
- **E26** `src/nvme-print-json.c:696-696` — text
  SHA-256: `73d5761db2f6a24b764d47f2ec77f26f092e7e74076cc196b8f5be4c87469729`
- **E27** `src/nvme-print-json.c:697-720` — json_fw_log
  SHA-256: `73d5761db2f6a24b764d47f2ec77f26f092e7e74076cc196b8f5be4c87469729`
- **E28** `src/nvme-print-json.c:721-721` — json_fw_log
  SHA-256: `73d5761db2f6a24b764d47f2ec77f26f092e7e74076cc196b8f5be4c87469729`
- **E29** `src/nvme-print-json.c:722-722` — text
  SHA-256: `73d5761db2f6a24b764d47f2ec77f26f092e7e74076cc196b8f5be4c87469729`
- **E30** `src/nvme-print-json.c:723-735` — json_changed_ns_list_log
  SHA-256: `73d5761db2f6a24b764d47f2ec77f26f092e7e74076cc196b8f5be4c87469729`
- **E31** `src/nvme-print-stdout.c:1901-1924` — stdout_resv_report
  SHA-256: `4a226cf7b3a7a7a4ea7e356ca4d3267eddb3208ac934d2b699dcd4bbdf36a6aa`
- **E32** `src/nvme-print-stdout.c:1925-1947` — stdout_resv_report
  SHA-256: `4a226cf7b3a7a7a4ea7e356ca4d3267eddb3208ac934d2b699dcd4bbdf36a6aa`
- **E33** `src/nvme-print-stdout.c:1949-1964` — stdout_resv_report
  SHA-256: `4a226cf7b3a7a7a4ea7e356ca4d3267eddb3208ac934d2b699dcd4bbdf36a6aa`
- **E34** `src/nvme-print-stdout.c:1965-1965` — text
  SHA-256: `4a226cf7b3a7a7a4ea7e356ca4d3267eddb3208ac934d2b699dcd4bbdf36a6aa`
- **E35** `src/nvme-print-stdout.c:1966-1982` — stdout_select_result
  SHA-256: `4a226cf7b3a7a7a4ea7e356ca4d3267eddb3208ac934d2b699dcd4bbdf36a6aa`
- **E36** `src/nvme-print-stdout.c:1983-1983` — text
  SHA-256: `4a226cf7b3a7a7a4ea7e356ca4d3267eddb3208ac934d2b699dcd4bbdf36a6aa`
- **E37** `src/nvme-print-stdout.c:1984-1985` — stdout_lba_range
  SHA-256: `4a226cf7b3a7a7a4ea7e356ca4d3267eddb3208ac934d2b699dcd4bbdf36a6aa`

## Observations

- Static function definition found: resv_report. (evidence: E5)

## Clarifications

- For automatically sized reports, should a growing registrant count trigger bounded refetching, or should the CLI return an explicitly marked partial report? (evidence: E5, E11, E13, E22, E24)

## Proposed interpretations — not verified facts

- The automatic path reads a header, sizes a second transfer from that first registrant count, and prints the second response without another size check. A growing count can therefore produce a descriptor list shorter than the second header advertises, even though the printers bound their reads. (evidence: E5, E11, E12, E13, E22, E24, E31, E32)

## Selected constraints

- [implementation_observation] Reservation report sizing depends on registrant count and selects different descriptor/header layouts for EDS. — resv_report_size in this source revision; ordinary layout uses nvme_registrant and extended layout uses nvme_registrant_ext. (evidence: E6, E1)
- [implementation_observation] A nonzero configured numd selects a fixed-length transfer instead of automatic two-pass sizing. — The current resv_report command; --numd=0 is represented by the same zero value as the automatic default. (evidence: E5, E11)
- [implementation_observation] The transfer command must be reinitialized when the allocated report length changes. — nvme_init_resv_report encodes the allocated length into data_len and cdw10 at this revision. (evidence: E12, E13, E21)
- [implementation_observation] JSON and normal-output paths clamp descriptor iteration to the allocated buffer capacity for both layouts. — The inspected reservation printers; binary output is documented separately and is not parsed. (evidence: E22, E24, E31, E32)

## Unresolved

- A report that fits its count is not automatically a stable membership snapshot; generation-change handling is a separate semantic requirement.
- The external NVMe specification was not supplied or validated in this run, so layout and command-field statements above are observations of this checkout.
- Output-format compatibility and the desired behavior for explicitly fixed-length transfers require a product/API decision if the requirement expands beyond automatic sizing.
- If the first header reports zero registrants, the current condition skips the second read entirely; whether to cover registrations occurring after that read is an additional scope decision.

## Saved clarifications

None.

## Limitations / warnings

- Semantic interpretation and question selection require a configured model.
- Static symbol/call observations do not prove runtime reachability or behavior.
- Evidence is a snapshot; refresh before acting if the workspace changes.
- Model review and matching quotations do not prove semantic correctness.
