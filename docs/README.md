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

## Resolved advisories

- **R2-001** — Resolved by clarifying the ResultsCard label as the 90% credible interval for VaR. See [issue #3](https://github.com/GhandyP/bayesian-financial-risk-analyzer/issues/3).
- **R4-low-draws-convergence** — Resolved by adding diagnostic-guided next steps while preserving the data-dependent convergence gate, accepted draw/tune bounds, and no-automatic-retry behavior. See [issue #4](https://github.com/GhandyP/bayesian-financial-risk-analyzer/issues/4).
