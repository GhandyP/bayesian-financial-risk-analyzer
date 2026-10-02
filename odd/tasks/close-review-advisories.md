# Feature: close-review-advisories

**Branch**: `fix/close-review-advisories`
**Owner**: parent session (el Gentleman)
**Status**: in progress

## Objective

Close the two deferred, non-blocking findings from the prior native review without changing the model's statistical guarantees or adding unrelated scope.

## Problem and rationale

- `R2-001`: the Flutter label `VaR intervalo 90%` does not identify the interval as a posterior credible interval for parameter uncertainty.
- `R4-low-draws-convergence`: the API accepts `draws=500`, which can fail the existing convergence gate on fat-tailed data. Convergence is data-dependent: a fixed request minimum would reject some valid low-cost requests, while an automatic retry could push latency beyond the current request timeout. Keep the existing gate and draw bounds; make its failure actionable and ensure the guidance reaches the user.

## Scope and constraints

- First, add `.github/ISSUE_TEMPLATE/model-reliability-followup.yml` and create the repository-level `status:approved` label; the user explicitly authorized this workflow setup.
- Use a separate approved issue for each independent advisory before implementing its code change; never apply `status:approved` to an issue without a later exact user instruction for that issue.
- Clarify the VaR interval label in Spanish and update `flutter_app/test/widgets/risk_widgets_test.dart`.
- Add actionable guidance to `ConvergenceError`; verify the API's HTTP 500 `detail` retains it in `backend/test_main.py`.
- Update the convergence guidance in `README.md` and mark both findings resolved in `docs/README.md`; preserve `docs/archive/model-reliability.md` as historical evidence.
- Product implementation surfaces: `Analisis_Riesgo_PyMC.py`, `backend/test_main.py`, `flutter_app/lib/widgets/results_card.dart`, `flutter_app/test/widgets/risk_widgets_test.dart`, `README.md`, and `docs/README.md`.
- Do not change sampler defaults, convergence thresholds, draw bounds, retry behavior, model calculations, or the old review lineage.

## Tasks

| ID | Task | Status | Evidence |
|---|---|---|---|
| A0 | Establish the authorized issue-intake form and repository approval label. | IN_PROGRESS | YAML form added locally and parsed; repo label `status:approved` created with target-host read-back. Form is not on `main` yet. |
| A1 | Close both advisories only after separate approved issues, with focused tests and docs. | BLOCKED | No issue exists yet; implementation stays behind the issue-approval gate. |
| A2 | Resolve the old review lineage only after separate explicit user authorization for its destructive disposition. | DEFERRED | No reset/recovery is authorized by this request; lineage remains untouched. |

## Acceptance criteria

- The UI names the reported VaR range as a 90% credible interval.
- A convergence failure tells the API caller what to adjust, without weakening the existing fail-closed convergence gate or adding an automatic retry.
- Regression tests cover both user-visible wording changes.
- Current documentation no longer lists the two advisories as open; the archived plan remains unchanged.
- Relevant local checks pass, and any unavailable or skipped checks are reported accurately.
- The candidate receives the required native review preflight before completion; no native review outcome is inferred.

## Verification plan

- Focused backend test for the convergence-failure response.
- Focused Flutter widget test for the interval label.
- `ruff check .`
- `python3 -m pytest -m "not slow" -q`
- Flutter analyzer and widget tests cannot run locally because `flutter` is not installed; validate them in CI if delivery is authorized.
- Run expensive slow model tests only if implementation changes model behavior or focused evidence indicates a need.

## Progress and decisions

- The existing convergence gate remains authoritative because minimum draws needed for convergence depend on the input data; the API's `detail` is propagated by the Flutter API service.
- No automatic retry or fixed higher minimum will be added; neither guarantees convergence and a retry could exceed the current timeout.
- RDD mode is globally on (`gentle-ai review mode status`); the verified target is `https://github.com/GhandyP/bayesian-financial-risk-analyzer`.
- The repository currently has no GitHub issues, no open PRs, no YAML issue form on `main`, and no `status:approved` label. The loaded defect workflow requires an approved issue before implementation and forbids creating an issue without a repository YAML form.
- The user explicitly authorized adding the YAML form and creating the repository-level `status:approved` label. The label was created after confirming target-host `viewerPermission: ADMIN`; read-back confirmed its description and color. The form parses as YAML but is not yet on `main`. No issue has been created or approved, and no product source was changed.
- Each advisory will remain blocked until its own issue is approved; the protected approval label will not be attached without a separate exact user instruction for that issue.
- The old lineage `review-18744d5406eacc4e` is explicitly out of scope; reset/recovery remains gated on separate user authorization.
- Flutter is unavailable in the local environment, so Flutter analyzer/widget tests need CI or must be reported as unavailable.

## Next step

Obtain native review authority for the YAML-form candidate, deliver the form to `main`, then create one issue per advisory. Stop for explicit approval of each issue before product implementation.
