---
name: synth-check-rtl
description: Detects behavioral (non-synthesizable) constructs in synthesizable RTL for emulator bring-up.
disable-model-invocation: true
---

# synth-check-rtl

A portable, lightweight-first detector for **behavioral** code in synthesizable
RTL. Built for emulator **bring-up**: HW-side RTL often arrives carrying
constructs that simulate fine but won't elaborate on an emulator. This skill
finds them so the user can resolve each one — either via the emulator's own
config/construct, or by rewriting to a **synthesizable** idiom.

**Lightweight first.** The first pass does the minimum: scan, match, **list**.
It edits nothing, explains nothing per-item, and computes no fixes. The heavy
per-item detail loads only when the user points at one specific **Finding**.
The skill generates a fix for the asked item only — generating fixes for every
behavioral code at once would be slow and token-heavy.

This is a portable skill: one shared, agent-agnostic body holds all the logic;
each tool (Claude Code, Cursor, Copilot) reaches it through a thin wrapper that
points here. Wrappers carry no duplicated logic.

## Invocation

Invoke with a path: `/synth-check-rtl <file|dir>`. With no path and an `rtl/`
directory present, scan `rtl/`.

## The flow

### Step 1 — Detect

Scan the given path. For every `.v`/`.sv`/`.vhd` file, skip testbench
(`*_tb.sv`/`*_tb.v`, or any path under `bench/`/`tb/`) silently. Detect runs in
two passes over the construct reference, reached by the context pointer below:

- **Pattern pass** — for each construct whose row carries a `pattern:` comment,
  test every remaining line against that pattern. Strip `//` line comments and
  the contents of `"..."` string literals from a line before testing it — words
  inside comments or strings (e.g. `// response time`) must not trigger a
  Finding. Every match is one **Finding**.
- **Reasoning pass** — for constructs whose row carries a `semantic:` comment
  (CDC, logic on reset/clock, multi-edge sensitivity, inferred latch, mixed
  logic, multi-driver, blocking-in-clocked, generate misuse, port-width), reason
  against `SYNTH-RULES.md` to decide whether the code is a real instance. A valid
  async reset (`posedge clk or negedge rst`) is not flagged; a dual-clock hazard
  (`posedge a or posedge b`) is. This pass is model-dependent — treat accuracy
  as probabilistic, not guaranteed. There is no deterministic test that can
  prove semantic detection correct (it would be tautological); verify it against
  the semantic fixture's expected-Findings manifest by reading, not by mirroring.

Every Finding carries `file:line | construct | severity | category`.

The reference is the single source of truth: adding a construct with its pattern
to `CONSTRUCTS.md` extends detection — edit one place, detection follows. Load
the reference one row at a time, leaving the rest unloaded.

**Completion criterion (exhaustive + checkable):** every line of every scanned
RTL file has been tested against every pattern-bearing construct, and every
semantic construct has been reasoned about. Every match is a Finding. Testbench
files are skipped, not flagged. Detect edits no file and produces no per-item
why or fix.

Apply the allowlist (`docs/agents/emulation-allowlist.md`) within Detect: a
Finding against a listed construct downgrades to `note`. Absent the allowlist,
base severities govern.

### Step 2 — Report (Detect output)

Print the Findings as a lean table — `file:line | construct | severity | category` —
then a one-line summary: `N findings: X errors, Y warnings, Z notes`.

**Completion criterion:** the table's error/warning/note counts equal the
summary line. Every Finding has all five fields.

Stop here. Wait for the user. Explanations, fixes, and file edits happen only in
Steps 3–4, on request.

### Step 3 — On demand: explain a specific Finding

Only when the user points at one Finding (e.g. "explain #3"). Load that
construct's reference entry and show why it is non-synthesizable and the
emulator-config/construct option that lets it run as-is. Edit nothing.

**Completion criterion:** the asked Finding's why and emulator-config option are
shown, drawn from its reference entry. Only that Finding is explained; the
others stay untouched, and no file is edited.

### Step 4 — On demand: fix a specific Finding

Only when the user asks to fix a specific Finding. Generate the **synthesizable**
idiom-level rewrite for that one Finding, drawn from its reference entry. Surface
it for review. Edit a file only after the user confirms that rewrite.

**Completion criterion:** the asked Finding has a synthesizable rewrite shown.
Fixes proceed one item at a time. A file is edited only after confirmation, and
only the confirmed item is rewritten.

## Context pointers

- **Construct reference:** [`CONSTRUCTS.md`](CONSTRUCTS.md) — the single source
  of truth. Each construct co-locates its severity, why, emulator-config option,
  and synthesizable rewrite in one row. Loaded one row at a time, on demand.
  Change a verdict or rewrite here and Detect/Fix follow.
- **Synthesizable-RTL rules & canonical forms:** [`SYNTH-RULES.md`](SYNTH-RULES.md)
  — the three unforgivable rules (no logic on reset/clock, no latches, separate
  sequential/combinational) with good/bad examples. Consult when classifying a
  synthesis-correctness Finding (valid async reset vs logic-on-reset, a latch, a
  CDC) and when writing a Fix rewrite — the canonical code lives there.
- **Allowlist:** `docs/agents/emulation-allowlist.md` (optional). A Finding
  against an allowlisted construct downgrades to `note`. Absent it, the generic
  IEEE 1800 synthesizable subset governs.

## Leading words

`behavioral` (what gets flagged), `synthesizable` (the target), `bring-up` (the
goal), `Finding` (the atomic output). These recruit EDA priors the agent already
holds; they anchor execution to the same behavior every run.

## Finding fields

A Finding carries `{file, line, construct, severity, category}`. The `construct`
field is the canonical short name a row declares via its `name:` comment (e.g.
`#delay`, `wait`, `class`, `multi-edge sensitivity`). `CONSTRUCTS.md` cells may
read richer (`wait(sig)`, `force`/`release`); the `name:` field is the single
join key between a Finding and its reference row — there is no separate `ref`
field.
