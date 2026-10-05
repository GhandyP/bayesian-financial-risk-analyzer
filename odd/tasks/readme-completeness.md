# Feature: readme-completeness

**Branch**: `docs/readme-completeness`
**Owner**: parent session (el Gentleman)
**Status**: in progress (bilingual README verified; commit/push pending)

## Objective

Make the root `README.md` a complete, accurate bilingual guide: the full English version first, followed by the full Spanish version.

## Scope and constraints

- Edit only the root `README.md` for the user-facing documentation.
- Keep `docs/README.md` as the separate archive/follow-up index.
- Put all English content first, then all Spanish content; do not alternate languages section by section. Keep each language block complete and structurally parallel.
- Preserve technical identifiers, commands, and API field names in both blocks.
- State Python 3.11 and Flutter 3.47.0 as CI toolchain versions, not as minimum supported versions. State the Dart SDK range declared by `pubspec.yaml`.
- Base API behavior, bounds, error statuses, model assumptions, and commands on source/CI evidence. Remove or qualify unverified empirical numbers.
- Do not alter application code, close issues, merge PRs, or open a PR. The user explicitly authorized committing and pushing this README work-unit.

## Tasks

| ID | Task | Status | Evidence |
|---|---|---|---|
| R1 | Reorganize the root README into a complete and source-accurate guide, then run structural checks. | IN_PROGRESS | Rewritten with all English sections first and matching Spanish sections second. Verification confirmed order, anchors, balanced fences, paths, and source accuracy. README diff: 356 insertions, 110 deletions; one cohesive bilingual documentation unit. Commit/push authorized, still pending. |

## Acceptance criteria

- The README has a scannable structure and table of contents covering overview, capabilities, requirements, setup/run, architecture, configuration, API contract/errors, model assumptions/non-goals, validation, verification, and troubleshooting.
- Every technical claim matches repository source or CI; CI toolchain versions are not mislabeled as compatibility minimums.
- The README has a complete English block followed by a complete Spanish block, with parallel sections and matching technical facts.
- Unsupported measured numbers are removed or explicitly qualified.
- Relative links and command examples are checked; `git diff --check` passes.
- No application tests are run because this is passive documentation-only work.
- Commit the verified README work-unit and push its feature branch, as explicitly authorized. Do not create a PR.

## Verification plan

- Compare README API/status/configuration/model/CI claims with the delegated source map.
- Check Markdown structure, local relative links, and whitespace.
- Do not run application tests for this passive documentation change.

## Progress

- Source map: `.github/workflows/ci.yml`, backend models/routes/requirements, shared limits, model implementation, and Flutter configuration were checked read-only by `gentle-ai-explore`.
- Root README now contains a complete English block followed by a complete Spanish block with parallel sections and distinct TOC anchors.
- `gentle-ai-verify` confirmed content order, matching sections, anchor targets, 32 balanced code fences, local paths/commands, and source-backed API/config/model/CI facts. No unsupported empirical claims remain.
- `git diff --check -- README.md` passed. No application tests apply to passive documentation.
- README diff is 356 additions and 110 deletions (466 changed lines); it is one cohesive file-level bilingual guide. Commit/push are explicitly authorized; no PR is authorized.
- Next: commit README plus task record, run the required native review preflight, push the branch, and report CI status.
