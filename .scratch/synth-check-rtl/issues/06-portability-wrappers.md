# 06 — Portability: Cursor and Copilot wrappers

**What to build:** make the skill portable across Claude Code, Cursor, and GitHub Copilot. The skill logic lives once in the shared, agent-agnostic body; add thin wrappers that only point each tool at that body — no logic duplicated. Cursor: a `.cursor/rules/synth-check-rtl.mdc` rule (`alwaysApply: false`, no globs), manual `@`-invoke in chat — runs only when asked, never auto-attached. Copilot: a `.github/prompts/synth-check-rtl.prompt.md` reusable prompt file, invoked by name in Copilot chat. Both wrappers reproduce the same lightweight Detect behavior against a fixture, proving the shared-body structure works in each tool without drift.

**Blocked by:** 01 — Detect behavioral codes, list lean Findings.

**Status:** ready-for-agent

- [ ] A Cursor rule wrapper exists and points at the shared skill body with no duplicated logic.
- [ ] The Cursor wrapper is `alwaysApply: false` with no globs (manual `@`-invoke only, no auto-attach).
- [ ] A Copilot reusable prompt file exists and points at the shared skill body with no duplicated logic.
- [ ] Each wrapper, invoked in its tool, reproduces the lightweight Detect behavior against a fixture (same lean Findings as the shared body).
- [ ] The construct logic and lightweight-first behavior live once in the shared body — single source of truth across all three tools.
