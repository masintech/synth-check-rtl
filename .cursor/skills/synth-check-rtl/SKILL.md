---
name: synth-check-rtl
description: Detects behavioral (non-synthesizable) constructs in synthesizable RTL for emulator bring-up.
disable-model-invocation: true
---

# synth-check-rtl (Cursor skill)

A **thin wrapper**: the skill's logic lives once in the shared, agent-agnostic
body — invoke it with `/synth-check-rtl <file|dir>` (defaults to `rtl/` when no
path is given and that directory exists), then follow the shared body exactly.

**Shared body:** [`.claude/skills/synth-check-rtl/SKILL.md`](../../../.claude/skills/synth-check-rtl/SKILL.md)

Construct reference (single source of truth, loaded on demand):
[`.claude/skills/synth-check-rtl/CONSTRUCTS.md`](../../../.claude/skills/synth-check-rtl/CONSTRUCTS.md).
Optional allowlist: `docs/agents/emulation-allowlist.md`.
