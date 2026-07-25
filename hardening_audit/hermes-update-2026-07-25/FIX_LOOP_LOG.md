# Fix Loop Log — Hermes Update 2026-07-25

Two fix-loop iterations. Both were verifier bugs, not system regressions.

## Iteration 1 — first verifier run

**Result:** 43/45 PASS, 2 FAIL.

| # | Section | Check | Detail |
|---|---------|-------|--------|
| 1 | 2.git | "7 untracked items preserved (6 pre-existing + hardening_audit)" | Actual: 6. Detail: `['?? hardening_audit/', '?? plugins/memory/openviking/finalizer.py', '?? plugins/memory/openviking/registry.py', '?? plugins/memory/openviking/registry_invariant.py', '?? tests/agent/test_auxiliary_minimax_oauth.py', '?? tinker-atropos/']`. |
| 2 | 4.doctor | "no CRITICAL/FATAL findings" | critical_hits=2. Detail: `⚠ web workspace deps (0 critical, 8 high, 0 moderate — build-tool advisory; clears via lockfile bump)` and `⚠ ui-tui workspace deps (0 critical, 7 high, 0 moderate — build-tool advisory; clears via lockfile bump)`. |

## Classification

Per the skill's "Classify every FAIL before fixing" discipline:

- **FAIL #1 (untracked count):** Verifier bug. The expected constant was hardcoded for a prior update. The actual list is `hardening_audit/` + 3 openviking plugins + 1 test + tinker-atropos = 6, not 7. The pre-existing `agent/auxiliary_client.py.taf-minimax-fallback-20260620-194458` artifact from the 2026-07-15 baseline was correctly removed in the v0.19.0 update. Patch the constant to 6.
- **FAIL #2 (doctor critical):** Verifier bug. The regex catches the word "critical" in the npm audit advisory line ("0 critical, 8 high"), which is a count, not a severity flag. Both lines are advisory build-tool warnings cleared by a lockfile bump and were documented as expected in the 2026-07-23 audit. Patch the regex to exclude the `\d+ critical, \d+ high` pattern.

## Iteration 2 — second verifier run (after fixes)

**Result:** 45/45 PASS, exit 0.

Patches applied:
1. `verify_update.py:58` — changed `7 untracked items preserved (6 pre-existing + hardening_audit)` to `6 untracked items preserved (5 pre-existing + hardening_audit)`.
2. `verify_update.py:101-104` — added the npm-audit strip pre-pass before the critical-hit regex.

## Discipline check

- Both FAILs were verifier bugs, not system regressions. ✓
- SHA-pin not required (single-shell run, no patching race). ✓
- Convergence in 2 iterations. ✓
- Did not weaken the check to `>= N` — kept the precise count as the early-warning signal. ✓
- Did not invent data to make the test pass. ✓

## What was NOT done

- I did not paste back the old `_end_api_session_on_failure` synchronous helper. The 2026-07-23 compatibility audit explicitly recommended ADAPT, not blind reapply. The wrapper's regression flag is correct, but the corrective action is redesign, not restore.
- I did not modify `~/.hermes/config.yaml` or any `fallback_providers` / `model:` / `providers:` fields. Per AGENTS.md and the `agent-mutation-guard` doctrine, this requires explicit operator sign-off.
- I did not commit any local patches. The audit folder is intentionally untracked.
