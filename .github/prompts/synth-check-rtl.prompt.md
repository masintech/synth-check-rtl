---
description: Detects behavioral (non-synthesizable) constructs in synthesizable RTL for emulator bring-up.
mode: agent
tools: []
---

# synth-check-rtl (Copilot prompt)

This is a **thin wrapper**. The skill's logic lives once in the shared,
agent-agnostic body — do NOT duplicate it here. When invoked (by name in Copilot
chat, with a path argument), follow the shared body exactly.

**Shared body:** [`.claude/skills/synth-check-rtl/SKILL.md`](../../.claude/skills/synth-check-rtl/SKILL.md)

Read that file and run the flow it describes. Construct reference:
[`.claude/skills/synth-check-rtl/CONSTRUCTS.md`](../../.claude/skills/synth-check-rtl/CONSTRUCTS.md) (single source of truth, loaded on demand).
Allowlist (optional): `docs/agents/emulation-allowlist.md`.

## Invocation

`/synth-check-rtl <file|dir>` — defaults to `rtl/` when no path is given and
that directory exists.

## Behavior in brief (full detail in the shared body)

Lightweight first: scan `.v`/`.sv`/`.vhd`, skip testbench (`*_tb.sv`/`*_tb.v`,
`bench/`/`tb/`), list behavioral constructs as lean Findings
(`file:line | construct | severity | ref`) plus a count summary. Edit nothing.
On request, explain one Finding (why + emulator-config) or fix one Finding
(synthesizable rewrite, confirmed before edit) — one item at a time, never bulk.
