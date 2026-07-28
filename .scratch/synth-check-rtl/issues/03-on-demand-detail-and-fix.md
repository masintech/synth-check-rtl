# 03 — On-demand detail and fix for a specific Finding

**What to build:** the per-item path between Detect and file edits. When the user points at a specific Finding (e.g. "explain #3"), the skill loads that construct's reference entry and shows why it's non-synthesizable and the emulator-config/construct option that lets it run as-is — no file edit. When the user asks to fix that item, the skill generates the idiom-level synthesizable rewrite for that one Finding, surfaced for review; no file is edited until the user confirms that rewrite. Fixes are one item at a time — never all at once. A fix-phase fixture set pairs specific behavioral constructs with their expected synthesizable rewrites, requested one item at a time.

**Blocked by:** 02 — Complete the construct table across all four categories.

**Status:** ready-for-agent

- [ ] Asking about a specific Finding loads that construct's reference entry and shows why + emulator-config option, with no file edit.
- [ ] Requesting a fix for a specific Finding generates the synthesizable rewrite for just that item; no file is edited until that rewrite is confirmed.
- [ ] Fixes are one-item-at-a-time; the skill never defaults to fixing all behavioral codes.
- [ ] A fix-phase fixture set pairs specific behavioral constructs with expected synthesizable rewrites, requested one item at a time.
