# Spec: synth-check-rtl skill

## Problem Statement

As a hardware engineer bringing a design up on an emulator, I receive RTL from the HW side that contains behavioral code — constructs that are valid SystemVerilog for simulation but non-synthesizable, so the design won't elaborate on the emulator. I currently have no fast, repeatable way to find these constructs before I try to compile for emulation, and when I do find them I have to recall both whether the emulator has a supported config/construct for each one and what the synthesizable rewrite looks like. This slows bring-up and lets non-synthesizable code slip into the emulation set.

## Solution

A cross-tool, portable skill for detecting behavioral (non-synthesizable) constructs in synthesizable RTL for emulator bring-up. It is **agent-agnostic**: the skill body is plain markdown that any coding agent can read and run, and each supported tool gets a thin **wrapper** that points the agent at the shared body. Wrappers exist for Claude Code, Cursor, and GitHub Copilot. All three wrappers point at one shared skill definition, so the construct logic and the lightweight-first behavior never diverge between tools.

I invoke the skill explicitly with a path (`synth-check-rtl <file|dir>`, defaulting to `rtl/` when no path is given and that directory exists). It scans synthesizable RTL design files (`.v`/`.sv`/`.vhd`) and, in a lightweight **Detect** pass, lists the behavioral (non-synthesizable) constructs it finds as **Findings** — each a short row (`file:line | construct | severity`) with a reference to that construct's entry in the construct reference, so the list is cheap to produce and easy to scan. It edits nothing, and it pre-computes no per-finding explanation or fix.

The heavy per-item detail — why the construct is non-synthesizable, the emulator-config/construct option that lets it run as-is, and the synthesizable rewrite — is produced **only on request, for the specific item I point at**, never in bulk. I ask about a Finding, the skill loads that construct's reference entry and shows the why, the emulator-config option, and the rewrite; I confirm, and only that item is rewritten. Per-project, an optional allowlist lets me mark constructs this flow accepts; findings against allowlisted constructs downgrade to `note` severity.

## User Stories

1. As a bring-up engineer, I want to invoke `/synth-check-rtl` on a file, so that I can find non-synthesizable constructs before compiling for emulation.
2. As a bring-up engineer, I want to invoke `/synth-check-rtl` on a directory, so that I can lint a whole subtree of RTL in one pass.
3. As a bring-up engineer, I want the skill to scan `.v`/`.sv`/`.vhd` files, so that it works across the Verilog/SystemVerilog/VHDL RTL I receive.
4. As a bring-up engineer, I want testbench/test code skipped automatically, so that I'm not flooded with findings on `*_tb.sv`/`bench/`/`tb/` files that are expected to be behavioral.
5. As a bring-up engineer, I want each flagged construct reported as a Finding with file and line, so that I can locate it precisely.
6. As a bring-up engineer, I want each Finding to carry a severity of error/warning/note, so that I can tell a hard-elaboration failure from a synthesizes-wrong hazard from a tool-dependent/allowlisted note.
7. As a bring-up engineer, I want each Finding in the Detect list to carry only the construct, its file:line, and a reference to the construct's entry, so that the list is cheap and scannable — not a wall of per-item explanation.
8. As a bring-up engineer, I want the per-item why/explanation produced only when I ask about a specific Finding, so that the skill does not spend time and tokens explaining every Finding up front.
9. As a bring-up engineer, I want, when I ask about a specific Finding, to see why the construct is non-synthesizable, so that I understand the failure on demand.
10. As a bring-up engineer, I want, when I ask about a specific Finding, to see the emulator-config/construct option that lets the construct run as-is, so that I can choose to keep the construct and configure the emulator instead of rewriting.
11. As a bring-up engineer, I want to request the fix for a specific Finding, so that the skill generates the synthesizable rewrite for just that item, not all of them at once.
12. As a bring-up engineer, I want the skill to NOT auto-suggest fixes for all behavioral codes, so that fix generation is bounded to the items I actually want to fix — defaulting to all would be time- and token-consuming.
13. As a bring-up engineer, I want the Detect phase to NOT edit my files, so that I can review the list before any change is made.
14. As a bring-up engineer, I want no file edited until I confirm a fix for a specific item, so that I review every rewrite before it lands.
15. As a bring-up engineer, I want timing/sim-only constructs (`#delay`, `initial`, `$display`, `event`, `wait`, `forever`, `real`/`time` types, `force`/`release`, `fork/join`, `disable`, `deassign`) flagged, so that classic non-synthesizable behavioral constructs don't reach the emulator.
16. As a bring-up engineer, I want SV testbench-isms (dynamic/associative arrays, `class`, `randomize`, `new()`, queues, `string`, `chandle`) flagged, so that high-level SystemVerilog constructs the emulator rejects in RTL are caught.
17. As a bring-up engineer, I want synthesis-correctness issues (inferred latches from incomplete `if/else` or missing `case`/`default`, multi-driver nets, blocking-vs-nonblocking misuse in clocked blocks) flagged as warnings, so that code that synthesizes but produces wrong hardware is caught.
18. As a bring-up engineer, I want structural/port issues (`generate` misuse, `real`/`time` parameters, port-width/instantiation concerns) flagged, so that flow-unsupported structural choices are surfaced.
19. As a project owner, I want an optional allowlist file where I can list constructs this flow accepts, so that findings against those constructs downgrade to `note` instead of error/warning.
20. As a project owner, I want the allowlist to live at `docs/agents/emulation-allowlist.md`, so that per-project tuning is a file edit, not a skill edit.
21. As a project owner, I want the allowlist to be optional, so that the skill works out-of-the-box with the generic synthesizable subset when no allowlist exists.
22. As a bring-up engineer, I want the construct vocabulary to default to the generic IEEE 1800 synthesizable subset, so that the skill is useful without me providing a tool-specific spec.
23. As a bring-up engineer, I want the skill to default to scanning `rtl/` when I give no path and that directory exists, so that I can invoke it with no args in the common case.
24. As a bring-up engineer, I want the skill portable across Claude Code, Cursor, and GitHub Copilot, so that I can use whichever tool my team uses without a different skill per tool.
25. As a bring-up engineer, I want each tool to reach the same shared skill body via a thin wrapper, so that the detection logic and lightweight-first behavior stay identical across tools — no drift.
26. As a bring-up engineer, I want one shared source of truth for the construct table, so that fixing a verdict or rewrite in one place updates the skill in all three tools at once.
27. As a bring-up engineer, I want the Cursor wrapper manual only (invoked by name in chat, no auto-attach), so that it stays lightweight-first and runs only when I ask, matching Claude Code and Copilot.
28. As a bring-up engineer, I want the skill to be a project skill that ships with the repo, so that anyone cloning it gets it across all three tools.
29. As a bring-up engineer, I want the skill user-invoked / manual in every tool, so that it adds no ambient context load and only runs when called.
30. As a bring-up engineer, I want the construct reference disclosed to a separate file (`CONSTRUCTS.md`), so that the main skill body stays legible and the table loads only when needed.
31. As a bring-up engineer, I want the skill to skip file types it doesn't handle rather than error, so that pointing it at a mixed directory is forgiving.
32. As a bring-up engineer, I want a fixture suite that exercises all four construct categories, so that detection behavior is verified and regressions are caught.
33. As a bring-up engineer, I want an expected-Findings manifest per fixture, so that re-invoking the skill on a fixture is a reproducible acceptance check.
34. As a bring-up engineer, I want a fix-phase fixture set, so that the rewrite generation is verified against known behavioral-to-synthesizable cases.
35. As a bring-up engineer, I want the skill to follow the repo's domain glossary vocabulary in its output, so that Finding language is consistent with project terminology.
36. As a bring-up engineer, I want the skill to respect ADRs in the area being scanned, so that deliberate deviations aren't flagged as problems.

## Implementation Decisions

- **Skill location & invocation.** A project skill that ships with the repo, **user-invoked / manual in every tool** — it adds no ambient context load and runs only when called. The skill body is agent-agnostic plain markdown; each supported tool reaches it through a thin wrapper. Default invocation uses a path argument (`<file|dir>`), defaulting to `rtl/` when no path is given and that directory exists.

- **Portability: one body, three thin wrappers.** The skill is portable across Claude Code, Cursor, and GitHub Copilot. The construct logic and lightweight-first behavior live once in the shared body; each tool gets a minimal wrapper whose only job is to point the agent at that body. The wrappers never duplicate the logic — they keep a single source of truth so the three tools never drift. Specifically:
  - **Claude Code** — a user-invoked skill at `.claude/skills/synth-check-rtl/` (`disable-model-invocation: true`; human-facing one-line description).
  - **Cursor** — a manual `.cursor/rules/synth-check-rtl.mdc` rule (`alwaysApply: false`, no `globs`), invoked by name in chat. Manual-only keeps it lightweight-first: it runs only when asked, never auto-attached on RTL edits.
  - **GitHub Copilot** — a reusable prompt file at `.github/prompts/synth-check-rtl.prompt.md`, invoked by name in Copilot chat.

- **Lightweight first.** The skill is deliberately cheap on the first pass. Detect does the minimum: scan, match constructs, list. It does not pre-explain every Finding, does not pre-compute fixes, does not edit. The model loads `CONSTRUCTS.md` only when a specific item is asked about — keeping the common "just scan and list" invocation light in time and tokens. The anti-pattern, defaulting to generating a fix for every behavioral code at once, is explicitly out.

- **Two branches, run as phases.** The skill has two branches: **Detect** (phase 1, default) and **Fix** (phase 2, entered only on explicit user request for a specific item after Detect). Both share the same construct reference; only the output and the file-mutation behavior differ. A per-item "explain" step sits between them: the user asks about one Finding, the reference entry loads, the why and emulator-config option are shown — still no file edit.

- **Scope of files scanned.** Synthesizable RTL design files: `.v`, `.sv`, `.vhd`. Testbench/test code is excluded by path convention — files matching `*_tb.sv` / `*_tb.v` or under `bench/` / `tb/` directories are skipped silently. Unsupported file types are skipped silently rather than erroring.

- **The unit of output is a Finding.** A Finding is the atomic reported unit. In the Detect list it is intentionally lean: the flagged construct, its `file:line`, its **severity**, and a **reference** to that construct's entry in the construct reference. The per-item why, emulator-config option, and rewrite are not part of the Detect row — they load on demand for the specific item the user asks about. Every flagged construct becomes exactly one Finding.

- **Severity model (three tiers).**
  - `error` — the construct will not synthesize/elaborate (e.g. `#delay`, `forever`, `class`, dynamic arrays).
  - `warning` — the construct synthesizes but produces wrong or ambiguous hardware (e.g. inferred latch, multi-driver net, blocking-vs-nonblocking misuse in a clocked block).
  - `note` — tool-dependent/structural, OR a construct listed in the project allowlist.

- **Four construct categories, all in scope.** (1) Timing & sim-only; (2) SV testbench-isms; (3) Synthesis-correctness; (4) Structural/port. The full per-construct mapping — construct → severity, why, emulator-config option, synthesizable rewrite — lives in a single source of truth, `CONSTRUCTS.md`, disclosed from `SKILL.md` by a context pointer.

- **Source of truth for "non-synthesizable".** The generic IEEE 1800 synthesizable subset. Per-project override via an optional allowlist at `docs/agents/emulation-allowlist.md`; when present, a finding against an allowlisted construct is downgraded to `note`. Absent the allowlist, the generic subset governs.

- **Detect phase output.** A lightweight list/table of lean Findings (`file:line | construct | severity | ref`), grouped or sortable by category, plus a one-line summary (`N findings: X errors, Y warnings, Z notes`). The Detect phase edits no files and generates no per-item explanations or fixes. Each Finding row points to its construct reference entry for on-demand detail.

- **On-demand per-item detail (between Detect and Fix).** When the user asks about a specific Finding (e.g. "explain #3"), the skill loads that construct's `CONSTRUCTS.md` entry and shows the why and the emulator-config/construct option — no file edit. This is the only place the per-item explanation and emulator-config option are produced, and only for the asked item.

- **Fix phase output.** On the user's request for a specific item, the skill generates an idiom-level synthesizable rewrite (the construct → replacement idiom from `CONSTRUCTS.md`) for that one Finding, surfaced for review. No file is edited until the user confirms that rewrite. Fixes are generated one asked-item at a time — never all at once by default — keeping each fix bounded and reviewable.

- **Skill file structure.**
  - Shared body (agent-agnostic): the two-phase flow as ordered steps, each with a checkable+exhaustive completion criterion; the leading words (`behavioral`, `synthesizable`, `bring-up`, `Finding`); and the context pointer to `CONSTRUCTS.md` and the allowlist.
  - `CONSTRUCTS.md` — disclosed reference: the construct table across the four categories, each row co-locating severity, why, emulator-config option, and synthesizable rewrite. Single source of truth, shared by all three tools.
  - `docs/agents/emulation-allowlist.md` — external reference (seed): the allowlist format plus an empty seed list. Tool-agnostic; consumed by the shared body.
  - Three thin wrappers (Claude Code skill frontmatter, Cursor `.mdc` rule, Copilot prompt file), each only pointing the agent at the shared body — no logic duplicated.

- **Standards conformance (writing-great-skills).** Single source of truth for the construct list (`CONSTRUCTS.md`); progressive disclosure of the table out of `SKILL.md`; co-location of each construct's verdict and remedy in one row; completion criteria are exhaustive and checkable rather than "be thorough"; no negation — behavior phrased positively (report Findings, show the rewrite); leading words repeated as tokens not sentences.

- **Domain docs.** No `CONTEXT.md` and no ADRs created for this feature. The candidate terms (Finding, allowlist) are skill-implementation terms, and `behavioral code` / `synthesizable RTL` are general EDA concepts — neither belongs in a project glossary per the domain-modeling skill's "only project-specific terms" rule, and `CONTEXT.md` is created lazily only when genuine project-specific language crystallizes. The skill consumes `CONTEXT.md`/ADRs per the repo's `docs/agents/domain.md` rules when they exist; if absent, it proceeds silently.

## Testing Decisions

- **What makes a good test here.** Test external behavior only, not implementation details. The externally observable behavior of this skill is: given a known input file, the Detect phase produces the expected lean list of Findings (construct, line, severity, category, reference); when asked about a specific item, it shows that construct's why and emulator-config option; when asked to fix a specific item, it produces the expected synthesizable rewrite for that item. The internal pattern-matching, parsing approach, or wording of prose is not tested — only the Findings, the on-demand detail, and the rewrites are.

- **One acceptance seam: a fixture suite with an expected-Findings manifest.** A `fixtures/` directory of `.sv` files, each seeded with known constructs spanning all four categories, paired with an expected-Findings manifest per fixture (the lean Finding shape: construct, line, severity, category). Invoking `/synth-check-rtl` on a fixture must reproduce that fixture's manifest. A separate fix-phase fixture set pairs a specific behavioral construct with its expected synthesizable rewrite, so rewrites are verified against known cases — requested one item at a time, not in bulk. This single seam covers detection, severity assignment, allowlist downgrade, skip-of-testbench, and the lean report shape in one place. New seams are not added; the one fixture seam is the highest and only seam.

- **Modules tested.** The Detect-phase behavior (category coverage, severity, allowlist downgrade, skip-of-testbench, report shape) and the Fix-phase behavior (rewrite generation for a specific asked item). The construct reference table (`CONSTRUCTS.md`) is exercised transitively through the fixtures — its rows are not unit-tested directly. Portability (the three wrappers reaching the same shared body) is verified structurally — each wrapper points at the shared body and carries no duplicated logic — rather than per-tool integration tests, since the logic under test lives in the shared body.

- **Prior art.** No existing tests in this repo (it contains no code yet). The skill's own `fixtures/` + manifest is the first test artifact. The expected-Findings manifest format echoes the issue-tracker convention's "one file per ticket" discipline.

- **Allowlist downgrade is covered by the same seam.** At least one fixture includes a construct that appears in a test allowlist, asserted to downgrade to `note`; the same fixture without the allowlist asserts the construct at its base severity. One seam, two configurations.

## Out of Scope

- Testbench/test code linting (`*_tb.sv`, `bench/`, `tb/`) — expected to be behavioral; skipped, not flagged.
- Bulk/auto fix generation — fixes are generated one asked-item at a time on request; the skill never defaults to producing fixes (or per-item why/explanations) for all behavioral codes at once, since that is time- and token-consuming.
- Pre-computing per-item explanations or emulator-config options during Detect — those are produced on demand only for the specific item the user asks about.
- Full AST rewriting / automated in-place patching of files — rewrites are idiom-level, surfaced for human review, one item at a time.
- A tool/synthesis-vendor-specific synthesizable subset as the default — the generic IEEE 1800 subset is the default; vendor subsets are expressed via the per-project allowlist, not built in.
- Standalone CI linter / non-skill automation — the deliverable is a Claude Code skill invoked by name, not a script run in CI.
- Model-invocation / ambient auto-trigger on `.sv` edits — the skill is user-invoked/manual in every tool (Claude Code, Cursor, Copilot) and runs only when explicitly called. The Cursor wrapper is `alwaysApply: false` with no globs — manual only, never auto-attached.
- Coverage of languages beyond `.v`/`.sv`/`.vhd` (e.g. Verilog-A, SPICE) in this iteration.
- Creating a project `CONTEXT.md` or ADRs for this feature — deferred until genuine project-specific language or a hard-to-reverse decision arises.

## Further Notes

- The skill's vocabulary (behavioral, synthesizable, bring-up, Finding) is consistent across its `SKILL.md`, `CONSTRUCTS.md`, output, and this spec — so shared language links the skill to invocation.
- `CONSTRUCTS.md` is the single source of truth: changing a verdict or rewrite is a one-row edit there, and the Detect/Fix behavior follows.
- The allowlist is the only per-project override surface; absent it, the generic subset governs, so the skill is useful immediately with no configuration.
- Re-running `/setup-matt-pocock-skills` is not required — the new `docs/agents/emulation-allowlist.md` is consumed by this skill directly, alongside the existing `issue-tracker.md` / `triage-labels.md` / `domain.md`.

Status: ready-for-agent
