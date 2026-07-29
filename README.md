# synth-check-rtl

A portable, lightweight-first agent skill that detects **behavioral
(non-synthesizable) constructs** in synthesizable RTL, built for emulator
**bring-up**. HW-side RTL often arrives carrying constructs that simulate fine
but won't elaborate on an emulator; this skill finds them so you can resolve
each one — either via the emulator's own config/construct, or by rewriting to a
**synthesizable** idiom.

It is a **skill**, not a linter: detection of semantic constructs (clock-domain
crossings, logic on reset, dual-clock hazards, inferred latches) is done by an
agent reasoning against a rules reference, not by a regex. Accuracy on those is
**model-dependent and probabilistic**, not guaranteed. Pattern-based constructs
(`#delay`, `$display`, `class`, …) are caught deterministically from a
single source of truth.

## What it does

`synth-check-rtl <file|dir>` (defaults to `rtl/` when no path is given) scans
`.v`/`.sv`/`.vhd` files — skipping testbench (`*_tb.sv`, `bench/`, `tb/`) — and
works in two phases:

1. **Detect** (lightweight, edits nothing): lists behavioral constructs as lean
   **Findings** — `file:line | construct | severity | category` — plus a one-line
   summary (`N findings: X errors, Y warnings, Z notes`).
2. **On demand**: point at a specific Finding to see why it's non-synthesizable
   and the emulator-config option that lets it run as-is; ask to fix it and the
   skill produces a synthesizable rewrite for that one item, confirmed before
   any file is edited. Fixes are one item at a time — never bulk.

Three severities: `error` (won't synthesize/elaborate), `warning` (synthesizes
but wrong/ambiguous hardware), `note` (tool-dependent, structural, or
allowlisted).

## Install / use

It ships as three thin wrappers over one shared, agent-agnostic body — pick
your tool:

| Tool | Wrapper | Invoke |
|------|---------|--------|
| **Claude Code** | `.claude/skills/synth-check-rtl/` (user-invoked skill) | `/synth-check-rtl <file\|dir>` |
| **Cursor** | `.cursor/rules/synth-check-rtl.mdc` (manual rule, `alwaysApply: false`) | `@synth-check-rtl <file\|dir>` |
| **GitHub Copilot** | `.github/prompts/synth-check-rtl.prompt.md` (reusable prompt) | `/synth-check-rtl <file\|dir>` |

All three point at the shared body — no logic is duplicated, so behavior never
drifts between tools. The wrappers are manual in every tool (no ambient
auto-trigger on RTL edits).

Clone into your project (or copy the `.claude/`, `.cursor/`, and `.github/`
trees) and invoke from your editor's agent.

## Example prompts

**Detect** — scan a file or directory:

```
# Claude Code / Copilot
> /synth-check-rtl rtl/uart_tx.sv

5 findings: 3 errors, 2 warnings, 0 notes

file:line          | construct                | severity | category
uart_tx.sv:42      | #delay                   | error    | timing & sim-only
uart_tx.sv:58      | inferred latch (if/else) | warning  | synthesis-correctness
...
```

```
# Cursor
> @synth-check-rtl rtl/uart_tx.sv
```

With no path given and an `rtl/` directory present, `/synth-check-rtl` scans
it by default.

**Explain** a specific Finding, once you have the table above:

```
> explain finding 2
> why is the inferred latch on line 58 a problem?
```

**Fix** one Finding at a time — nothing is edited until you confirm:

```
> fix finding 1
> rewrite the #delay on line 42 to be synthesizable
```

The skill never bulk-fixes: each fix is scoped to the one Finding you point
at, shown for review before any file is touched.

## Skill structure

```
.claude/skills/synth-check-rtl/
├── SKILL.md        # the shared body: two-phase flow, completion criteria, pointers
├── CONSTRUCTS.md   # single source of truth: per-construct severity, why,
│                   #   emulator-config option, synthesizable rewrite (+ pattern
│                   #   or semantic tag for detection)
└── SYNTH-RULES.md  # the three synthesizable-RTL rules + canonical good/bad forms
```

- **`CONSTRUCTS.md`** is the single source of truth. Each row co-locates a
  construct's severity, why it's non-synthesizable, the emulator-config option,
  and the synthesizable rewrite. Detection reads this table: adding a construct
  (with its `pattern:` or `semantic:` tag) extends detection — one place to edit.
- **`SYNTH-RULES.md`** holds the canonical forms the reasoning pass classifies
  against (the three "unforgivable rules": no logic on reset/clock, no latches,
  separate sequential/combinational). Sourced from [Adi Teman's walkthrough](https://www.youtube.com/watch?v=BIqLk23hE90).

## Per-project tuning

`docs/agents/emulation-allowlist.md` (optional) lists constructs this flow
accepts despite being generically non-synthesizable; a Finding against an
allowlisted construct downgrades to `note`. The shipped seed is empty (the
generic IEEE 1800 synthesizable subset governs). Edit the file — not the skill —
to tune per project.

## Honest limitations

- **Model-dependent.** Semantic detection (CDC, logic on reset/clock, multi-edge
  sensitivity, inferred latches, mixed logic, multi-driver, blocking-in-clocked,
  generate misuse, port-width) is done by reasoning, not pattern. A weaker model
  or an ambiguous case can miss or misjudge. There is no deterministic proof of
  correctness — that would be tautological — so verification is by fixture
  comparison against known cases, not a unit test (see [Development](#development)).
- **Pattern detection is line-based.** It strips `//` comments and string
  contents before matching, but does not build a full AST. Edge cases (block
  comments `/* */`, unusual escapes) may slip through.
- **Generic subset by default.** Vendor-specific accepted constructs belong in
  the allowlist, not in `CONSTRUCTS.md`.

## Development

`main` ships only what you need to install and run the skill. The pytest
suite (40 tests), the `fixtures/` acceptance corpus, the original spec and
ticket breakdown, and the Claude Code project instructions used to build this
repo live on the [`dev`](../../tree/dev) branch.

```bash
git checkout dev
python3 -m pytest tests/ -q
```

## License

[MIT](LICENSE)
