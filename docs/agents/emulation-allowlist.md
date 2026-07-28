# Emulation Allowlist

Per-project override for `synth-check-rtl`. List constructs this flow accepts
despite being generically non-synthesizable. A Finding against a listed
construct is downgraded to `note` severity instead of `error`/`warning`.

The construct names here must match the **short token** the detector uses (the
leading token of the CONSTRUCTS.md construct cell, e.g. `#delay`, `wait`,
`class`, `real parameter`). See `.claude/skills/synth-check-rtl/CONSTRUCTS.md`.

## Accepted constructs

<!-- Add one construct per line under the list. Empty by default: the generic
     IEEE 1800 synthesizable subset governs until you add entries. -->

- (none)

## Notes

- Absent this file (or with no entries), the generic synthesizable subset
  governs — every non-synthesizable construct is flagged at its base severity.
- This is the **only** per-project override surface. Vendor-specific accepted
  constructs go here, not in `CONSTRUCTS.md`.
