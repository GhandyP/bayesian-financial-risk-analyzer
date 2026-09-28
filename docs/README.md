# Documentation

## Layout

| Path | Contents |
|------|----------|
| `archive/` | Closed plan artifacts, kept as provenance rather than as current guidance |

## Archived plans

Both phases of the hardening work are delivered and merged into `main`. Their task files record what each work unit did, the commit that closed it, and the measurements behind each decision. They are archived rather than deleted because the numbers in them — the volatility prior bias, the Student-t scale conversion, the coverage backtest — are the evidence for the code that shipped.

| Plan | Commits | Merged as | Delivered |
|------|---------|-----------|-----------|
| [portfolio-hardening](archive/portfolio-hardening.md) | 12 | PR #1 → `f4ec95a` | Repaired a broken analysis path and enforced the Python/Dart contract |
| [model-reliability](archive/model-reliability.md) | 10 | PR #2 → `8cc61ed` | Student-t likelihood, convergence diagnostics, analytic VaR and expected shortfall |

Their `Branch:` headers name branches that were deleted after the merges: the work lives on `main`.

## Current guidance

The archived plans are history. For how the project works today, read the top-level `README.md` (setup, API contract, model assumptions and explicit non-goals) and the `AGENTS.md` files (one per area: repository root, `backend/`, `flutter_app/`).

## Deferred work

Neither item below blocks anything that shipped, and both are code-level rather than process-level.

1. **`R2-001`** — the label of the VaR credible interval in `flutter_app/lib/widgets/results_card.dart` does not explain that the range is parameter uncertainty rather than a confidence interval.
2. **`R4-low-draws-convergence`** — the API accepts `draws=500`, but that configuration was measured not to converge on fat-tailed data (rhat 1.0260, ESS 258), so such a request returns 500. Raising the minimum, or degrading with a warning, is an open decision. The README documents the measured behaviour.
