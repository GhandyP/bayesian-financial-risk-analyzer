# Old review lineage: historical record

**Current disposition: unresolved.** This note records the old lineage for provenance; it does not change native review authority.

## Timeline

### Historical evidence

- Memory records lineage `review-18744d5406eacc4e` as `correction_required` for an obsolete candidate tree beginning `709b7bb`.
- Its correction path became unusable after three `capture-binding-rejected` attempts.

### Current observation (2026-10-04)

- Native `status` and `inspect` calls for that exact lineage returned `applicability: unrelated`, `repair.status: unsupported`, and zero lineage/candidate counts.
- `inspect` offered a different fresh START for the current seven-path aggregate target `sha256:da8e54d6bd8f22a75ae974591ddeab94968feae293075d1c9cdfe6e09115491f` under a different lineage. It was not started.
- No RESET, RECOVER, or ABANDON was performed.

## Why it remains unresolved

The current native context does not recognize the old lineage and cannot provide a supported repair path. The old lineage cannot be moved into a folder. Its safe disposition remains unresolved unless the original native authority/workspace is restored or the maintainer chooses to leave it untouched. Do not treat the unrelated current context as authority to reset or recover it.

**No native authority was changed.** The historical memory record is evidence of past state, not current native authority.
