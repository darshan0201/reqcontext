# Research basis and implementation decisions

The user's requirement is model-selected applicability and clarification, without
hard-coded domain-word triggers. Literature informs the workflow; the project does
not claim novelty or reproduce the papers' trained models/reported gains.

## Relevant primary research

- **Self-RAG (ICLR 2024)**: learns retrieval and critique behavior using reflection
  tokens. We borrow the idea of evaluating relevance and support after retrieval.
  Our separate JSON review call does not reproduce its training or decoding method.
  https://arxiv.org/html/2310.11511v1
- **Active Retrieval Augmented Generation / FLARE (EMNLP 2023)**: retrieves as
  generation needs new information. Our model chooses follow-up queries/tools;
  we do not implement FLARE's low-confidence-token retrieval trigger.
  https://aclanthology.org/2023.emnlp-main.495/
- **RepoCoder (EMNLP 2023)**: iterative retrieval and generation use context spread
  across repositories. Our loop serves requirement investigation rather than code
  completion, and remains bounded by configurable resource limits.
  https://aclanthology.org/2023.emnlp-main.151/
- **STaR-GATE (2024)**: trains clarifying questions using task-specific outcomes.
  It motivates evaluating whether questions improve subsequent work. We do not
  train its questioner or assume prompting achieves the same result.
  https://arxiv.org/html/2403.19154v2
- **Uncertainty-Aware Clarification with Information Gain (ICML 2026)**: trains a
  clarifier using belief updates toward a target goal. It motivates measuring
  ambiguity reduction rather than question fluency. Our implementation asks the
  model to explain consequential alternatives but computes no Bayesian reward.
  https://proceedings.mlr.press/v306/deng26l.html
- **Value of Information (ACL 2026)**: weighs expected task utility from asking
  against user effort. It suggests a future decision-cost objective for question
  selection. We do not claim our review prompt implements its utility estimator.
  https://aclanthology.org/2026.acl-long.1987/

## How a constraint is selected

The model investigates a requirement in its actual repository. It proposes a
constraint with a cited exact quotation, source-origin classification, applicable
scope/version and why it affects the task. A second model invocation critiques the
proposal. The runtime rejects nonexistent references or quotations, but cannot
prove applicability/entailment. User-confirmed clarifications are available in the
same task scope; stale records explicitly show their changed sources.

Example (illustrative, not a live-model result): if a repository upload policy
already states three attempts, a model should cite it and establish applicability
rather than ask for the count. It may instead ask whether the policy covers the
foreground path, if that choice remains unresolved and changes implementation.

## Proposed evaluation

Use fixed incomplete requirements plus repository/specification snapshots with
human-reviewed relevant constraints and unresolved decisions. Compare a model
with ordinary search, our adaptive loop, and an evidence-oracle condition. Measure:
correct applicable constraints, unsupported claims, consequential questions,
unnecessary questions, downstream implementation success, model calls and tokens.
Keep development examples separate from final evaluation; repeat across models.
No numeric confidence from a model should be treated as calibrated probability.

Next learning step: collect outcome-labelled investigation trajectories and prefer
question/search choices that improve task success while reducing human interaction
cost. Fine-tuning or a learned selector is warranted only after the prompting/tool
baseline is measured. The current code is the infrastructure for that experiment.
