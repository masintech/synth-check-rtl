# 07 — Detection reads CONSTRUCTS.md (single source of truth)

**What to build:** Make the deterministic detection of pattern-based constructs derive from `CONSTRUCTS.md` rather than a parallel hardcoded pattern list — the single-source-of-truth invariant the code review found broken. Adding a construct (with its pattern) to the table extends detection: change a verdict there and Detect follows. Wire the allowlist into this detection path so the skill body actually applies the `note` downgrade (today it lives only in a test helper). Fix the Finding shape so the construct table, the expected-Findings manifests, and `SKILL.md` agree on the same fields — resolving the `ref` vs `category` mismatch the review flagged.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Detection of pattern-based constructs is driven by `CONSTRUCTS.md` (one source of truth), not a separate hardcoded list; adding a construct + its pattern to the table makes Detect catch it.
- [ ] The allowlist is applied within the detection path (a Finding against an allowlisted construct downgrades to `note`), not only inside a test helper.
- [ ] The Finding shape is consistent across `CONSTRUCTS.md`, the expected-Findings manifests, and `SKILL.md` (same fields — resolve the `ref` vs `category` mismatch).
- [ ] Every existing fixture's expected-Findings manifest is still reproduced (no regression in the Detect acceptance seam).
