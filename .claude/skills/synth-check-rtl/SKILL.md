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
Defaulting to generating fixes for every behavioral code would be slow and
token-heavy; this skill never does that.

This is a portable skill: one shared, agent-agnostic body holds all the logic;
each tool (Claude Code, Cursor, Copilot) reaches it through a thin wrapper that
points here. Wrappers never duplicate logic.

## Invocation

Invoke with a path: `/synth-check-rtl <file|dir>`. With no path and an `rtl/`
directory present, scan `rtl/`.

## The flow

### Step 1 — Detect

Scan the given path. For every `.v`/`.sv`/`.vhd` file, skip testbench
(`*_tb.sv`/`*_tb.v`, or any path under `bench/`/`tb/`) silently. For each
remaining line, test it against every construct in the reference — reached by
the context pointer below. Every match is one **Finding**:
`file:line | construct | severity | ref`.

**Completion criterion (exhaustive + checkable):** every line of every scanned
RTL file has been tested against every construct in the reference, and every
match is a Finding. Testbench files are skipped, not flagged. Detect edits no
file and produces no per-item why or fix.

Load the construct reference only when Step 1 needs it to classify a match — and
again in Step 2 on demand. Load it one row at a time, never the whole table.

### Step 2 — Report (Detect output)

Print the Findings as a lean table — `file:line | construct | severity | ref` —
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
shown, drawn from its reference entry. No other Finding is explained. No file is
edited.

### Step 4 — On demand: fix a specific Finding

Only when the user asks to fix a specific Finding. Generate the **synthesizable**
idiom-level rewrite for that one Finding, drawn from its reference entry. Surface
it for review. Edit no file until the user confirms that rewrite.

**Completion criterion:** the asked Finding has a synthesizable rewrite shown.
Fixes are one item at a time — never all at once. No file is edited before
confirmation, and only the confirmed item is rewritten.

## Context pointers

- **Construct reference:** [`CONSTRUCTS.md`](CONSTRUCTS.md) — the single source
  of truth. Each construct co-locates its severity, why, emulator-config option,
  and synthesizable rewrite in one row. Loaded on demand, never bulk. Change a
  verdict or rewrite here and Detect/Fix follow.
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

## Vocabularies

A Finding's `ref` names a construct. The detector uses a short token
(`#delay`, `wait`, `class`); `CONSTRUCTS.md` uses a richer cell
(`wait(sig)`, `force`/`release`). Join them by the leading token — strip
backticks, parens, and `/`-alternatives.
