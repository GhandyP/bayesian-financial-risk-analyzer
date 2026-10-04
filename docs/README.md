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

## Active follow-up

The two model-reliability advisories have separate fixes under review; neither change has merged to `main` yet. Follow the ordered steps in [remaining work](remaining-work.md).

- **R2-001** — The VaR interval-label fix is in [PR #5](https://github.com/GhandyP/bayesian-financial-risk-analyzer/pull/5), linked to issue #3.
- **R4-low-draws-convergence** — The actionable convergence-guidance fix is in [PR #6](https://github.com/GhandyP/bayesian-financial-risk-analyzer/pull/6), stacked on PR #5 and linked to issue #4.
- **Legacy review lineage** — Still unresolved; see the [historical lineage note](archive/old-review-lineage.md).
