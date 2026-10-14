# Robustness: implemented safeguards and remaining work

## Implemented in v0.5.1

- Atomic database refresh with rollback of source, reference, map and metadata changes.
- Literal folder prefixes, including names containing wildcard characters.
- Validated bounded query limits and explicit refresh on source-size-policy changes.
- Source hashes, capture IDs, reference revisions/pages and scope citations.
- Snapshot reuse without source enumeration or reference re-extraction.
- Symbol-fragment lookup to help find helpers missed by natural-language ranking.
- C macro parse guard, unsupported-citation rejection and quoted-source checks.
- Bounded evidence, tool rounds and transport response sizes.

## Highest-value next improvements

1. **Unattended model evaluation:** repeated labelled tasks across repositories/models,
   with measured downstream implementation outcomes and human review. Current tests
   cannot establish semantic reliability.
2. **Change-aware refresh:** use explicit Git changes or watchers to update affected
   files while retaining safe fallbacks for untracked files, branch switches and
   missed events. Ordinary analysis should remain snapshot-only.
3. **Better discovery:** model reranking or a measured semantic retriever for synonyms
   and indirect intent. Keep lexical/symbol tools as inspectable baselines.
4. **Stronger evidence checks:** independently test applicability/entailment, conflicting
   revisions and omitted exceptions. A valid quotation does not establish correctness.
5. **Concurrent operations:** load-test reader/refresh overlap, lock timeouts and multiple
   writers. Atomic publication is necessary but not proof of concurrency scalability.
6. **Parser/document coverage:** evaluate macros, function pointers, aliases, generated
   code and PDF tables/diagrams; add OCR only with explicit provenance and confidence
   limits. Do not invent resolved relationships where parsers are uncertain.
7. **Repository privacy controls:** deliberate include/exclude policies and optional
   redaction before a remote model receives excerpts. Current exclusions are not a
   general secret detector.
8. **Operational recovery:** snapshot validation/backup, corruption handling and an
   overall investigation deadline. The current per-request HTTP timeout is not enough
   for every provider or custom adapter.

No claim is made that these future features already exist. The project currently
supports one engineer/client and Python/C source snapshots.
