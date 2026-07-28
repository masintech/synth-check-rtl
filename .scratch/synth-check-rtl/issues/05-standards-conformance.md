# 05 — Standards conformance: writing-great-skills pass

**What to build:** a conformance pass over the skill against `writing-great-skills`. Verify the construct table is progressively disclosed (out of the main skill body, behind a context pointer); the construct list is a single source of truth (one place to edit a verdict/rewrite); completion criteria are checkable and exhaustive rather than "be thorough"; behavior is phrased positively (no negation); leading words (`behavioral`, `synthesizable`, `bring-up`, `Finding`) are repeated as tokens, not sentences; co-location holds (each construct's severity, why, emulator-config option, and rewrite sit in one row). Tighten any drift found. No `CONTEXT.md` or ADR is created for this feature.

**Blocked by:** 03 — On-demand detail and fix for a specific Finding, 04 — Allowlist: per-project downgrade to note.

**Status:** ready-for-agent

- [ ] The construct table is progressively disclosed — out of the main skill body, behind a context pointer.
- [ ] The construct list is a single source of truth — one place to edit a verdict or rewrite.
- [ ] Completion criteria are checkable and exhaustive, not "be thorough"-style no-ops.
- [ ] Behavior is phrased positively; no negation (no "don't miss", "don't auto-rewrite").
- [ ] Leading words (`behavioral`, `synthesizable`, `bring-up`, `Finding`) repeat as tokens, not as sentences.
- [ ] Each construct's severity, why, emulator-config option, and rewrite are co-located in one row.
- [ ] No `CONTEXT.md` or ADR created for this feature.
