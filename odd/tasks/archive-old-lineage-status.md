# Feature: archive-old-lineage-status

**Branch**: `docs/old-lineage-status`
**Owner**: parent session (el Gentleman)
**Status**: in progress

## Objective

Document the inaccessible legacy review lineage as unresolved and make the remaining repository work easy to act on, without changing native review authority or mixing documentation into advisory PRs #5/#6.

## Scope and constraints

- Keep `odd/tasks/close-review-advisories.md` as the active task record while A3 remains unresolved.
- Add an archival note under `docs/archive/` describing the old lineage's known history and the current inability to bind it.
- Add `docs/remaining-work.md` with the ordered PR work, issue status, and the legacy-lineage blocker.
- Link both documents from `docs/README.md`.
- Do not mutate the old lineage's native authority or follow the unrelated fresh START offered for it. Do not RESET/RECOVER/ABANDON that lineage, close issues, merge PRs, or change advisory code. The separate review lifecycle for this documentation work-unit follows the user-owned RDD switch.
- Keep this documentation on a separate `docs/` branch so the existing issue-specific PR slices remain focused.

## Tasks

| ID | Task | Status | Evidence |
|---|---|---|---|
| D1 | Archive the legacy-lineage diagnosis and document all currently pending repository work. | IN_PROGRESS | User approved the recommended archival scope. Historical memory records lineage `review-18744d5406eacc4e` as `correction_required` with an unexecutable correction route; current native status/inspect returned `applicability: unrelated`, `repair: unsupported`, and no candidates. No native mutation was performed. |

## Acceptance criteria

- The archive note clearly distinguishes historical lineage state from the current native authority result and does not claim the lineage is resolved.
- The pending-work page records PR #5 as the first slice, PR #6 as stacked on #5, both issues as open, and the old lineage as unresolved.
- The docs index links both new pages.
- Existing task tracking and native authority remain untouched.
- Markdown structure and repository-relative links are checked; no behavior tests are applicable to this passive documentation-only change.
- A Conventional Commit is created and pushed to the documentation branch; the exact commit is recorded below.

## Verification plan

- `git diff --check` on the documentation slice.
- Read back the new Markdown and confirm every relative link resolves.
- No application test suite is applicable because the change is passive documentation only.

## Progress and decisions

- The current native controller did not bind the exact old lineage ID in this repository context and returned no repair candidates. Its `inspect` offered a fresh review for the unrelated accumulated seven-path candidate; that transition was not followed.
- Historical project memory says the old lineage was `correction_required` for an obsolete candidate and that correction captures were rejected. Those historical observations will be attributed as historical, not represented as current provider authority.
- No RESET, RECOVER, or ABANDON was performed on the old lineage. This separate documentation work-unit was natively inspected and returned low-risk `state: approved`, `action: closed`, and `lenses_required: false` under lineage `review-34142cdb45f43d59`; no capture or acknowledgment route was returned.

## Delivery evidence

- Work-unit commit: `c8412a7b80625cf565fe69c482f345a3d1900f1f` (`docs(review): archive legacy lineage and list pending work`).
- Push: pending.
