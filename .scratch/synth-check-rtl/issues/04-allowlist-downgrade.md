# 04 — Allowlist: per-project downgrade to note

**What to build:** per-project override of the generic verdict. An optional allowlist at `docs/agents/emulation-allowlist.md` lists constructs this flow accepts; a Finding against an allowlisted construct downgrades to `note` severity. Absent the allowlist, the generic subset governs. A fixture with a construct that appears in a test allowlist is asserted at `note`; the same fixture without the allowlist asserts that construct at its base severity. The allowlist file ships as a tool-agnostic seed (format + empty list).

**Blocked by:** 01 — Detect behavioral codes, list lean Findings.

**Status:** ready-for-agent

- [ ] A construct listed in `docs/agents/emulation-allowlist.md` is reported at `note` severity.
- [ ] Without the allowlist, the same construct is reported at its base severity.
- [ ] Absent the allowlist, the generic subset governs (no error, no behavior change).
- [ ] The allowlist file ships as a tool-agnostic seed: format documented plus an empty list.
- [ ] One fixture asserts the downgrade at `note` with the allowlist and at base severity without it.
