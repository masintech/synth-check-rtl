# 08 — Agent reasoning for semantic constructs

**What to build:** The constructs that cannot be caught by pattern — clock-domain crossing, logic on reset, logic on clock, multi-edge sensitivity (dual-clock hazard), inferred latch, and mixed logic in a sequential block — are flagged by the agent reasoning against `SYNTH-RULES.md`, not by a regex. Define how the skill's Detect step applies that reasoning and distinguishes valid forms (a true async reset `posedge clk or negedge rst` is not flagged; `posedge a or posedge b` is). Establish how model-dependent detection is verified honestly — a deterministic unit test on these would be tautological, so the verification approach must treat accuracy as probabilistic (e.g. fixture manifests exercised through the agent), not claim a false guarantee.

**Blocked by:** 07 — Detection reads CONSTRUCTS.md (single source of truth).

**Status:** ready-for-agent

- [ ] Semantic constructs (CDC, logic on reset, logic on clock, multi-edge sensitivity, inferred latch, mixed logic in a sequential block) are flagged by reasoning against `SYNTH-RULES.md`, distinguished from valid forms (a true async reset is not flagged).
- [ ] The skill body's Detect step describes how to apply that reasoning, so a valid `posedge clk or negedge rst` is not flagged while `posedge a or posedge b` is.
- [ ] The verification approach for model-dependent detection is documented and honest — accuracy treated as probabilistic, not a tautological deterministic unit test.
- [ ] Fixtures for the semantic cases exist and carry expected-Findings manifests.
