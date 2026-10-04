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
| A0 | Establish the authorized issue-intake form and repository approval label. | DONE | Native review `review-20409118ee8a4d48` approved and acknowledged; YAML form parsed; repo label read back; commit `8f7fc451fc513087cdb273d584229a7f85602ed8` is on `main` at `cf09b97`; CI run `37049527767` succeeded. |
| A1 | Clarify the VaR credible-interval label for approved issue #3, with a focused widget test and docs. | DONE | Work-unit commit `135d4ec0c63b6df024ba5ac73fecb2bfcbbcccce` was pushed to `origin/fix/close-review-advisories` and approved/acknowledged under native lineage `review-880b037661960504`. Issue #3 remains OPEN with `status:approved`. CI run `37169068216` passed backend lint/tests/real-model tests and Flutter analyze/tests. |
| A2 | Make convergence failures actionable for approved issue #4, with an API regression test and docs. | IN_PROGRESS | Issue #4 is OPEN with `status:approved`. Test-first RED was observed at the missing-guidance assertion; the focused tests now pass. `git diff --check`, `ruff check .`, and non-slow pytest pass; commit/review/CI remain. |
| A3 | Resolve the old review lineage only after separate explicit user authorization for its destructive disposition. | DEFERRED | No reset/recovery is authorized by this request; lineage remains untouched. |

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
- At setup start, the repository had no issues, YAML issue form, or `status:approved` label. A0 added the form and label; the form is now on `main`, and issues #3 and #4 are open. The loaded defect workflow requires a separate approved issue per independent finding before implementation.
- The user explicitly authorized adding the YAML form and creating the repository-level `status:approved` label. The label was created after confirming target-host `viewerPermission: ADMIN`; read-back confirmed its description and color.
- The form and task record were reviewed and acknowledged under native lineage `review-20409118ee8a4d48`; YAML parse and staged diff checks passed. Work-unit commit `8f7fc451fc513087cdb273d584229a7f85602ed8` (`chore(issue-forms): add model reliability follow-up form`) is on `main` at `cf09b97`.
- Issues #3 (R2-001) and #4 (R4-low-draws-convergence) were created from the YAML form. Target-host read-back confirmed exact titles/bodies and OPEN state. After the user explicitly selected approval for both, target-host reads verified actor `GhandyP` with `ADMIN`, and pre/post read-backs confirmed `status:approved` on each issue without conflicting status labels.
- CI run `37049527767` for `cf09b977f00606bfc122a7f5a313a98e9e62d3e3` completed successfully. RDD is enabled and there are no open PR conflicts. Current main reproduction confirms the old VaR label and that convergence failures currently expose metrics but no adjustment guidance; `/analyse` returns the `ConvergenceError` detail as HTTP 500.
- CodeGraph impact mapping found the VaR display in `flutter_app/lib/widgets/results_card.dart`, the existing UI tests in `flutter_app/test/widgets/risk_widgets_test.dart`, and the convergence path from `Analisis_Riesgo_PyMC.py` through `backend/main.py` to `backend/test_main.py`. Issue #3 commit `135d4ec0c63b6df024ba5ac73fecb2bfcbbcccce` updates the label, test expectation, and current documentation; native review `review-880b037661960504` approved and consumed the exact candidate. Local Flutter was unavailable, so local RED/GREEN is not claimed; CI run `37169068216` passed both Flutter analyze/tests and all backend jobs, including real model tests.
- Issue #4 test-first evidence: the focused backend test failed first because `Revise los datos` was absent, then both focused tests passed after the message update. `git diff --check`, `ruff check .`, and `python3 -m pytest -m "not slow" -q` passed (20 passed, 3 deselected). Pytest emitted a Starlette deprecation warning and an unawaited `to_thread` coroutine warning. The fail-closed gate, draw bounds, sampler defaults, and no-retry behavior remain unchanged.
- The old lineage `review-18744d5406eacc4e` is explicitly out of scope; reset/recovery remains gated on separate user authorization.
- Flutter is unavailable in the local environment, so Flutter analyzer/widget tests need CI or must be reported as unavailable.

## Next step

Commit the approved issue #4 work unit, run its native review, push the branch, and verify the resulting CI before marking A2 complete.
