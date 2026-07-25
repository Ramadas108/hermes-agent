# Next Maintenance Checks — Hermes Update 2026-07-25

Prioritized list of follow-ups for the next operator session or cron cycle.

## P1. Implement API-server fast-close (ADAPT path)

**Why:** L1 from KNOWN_LIMITATIONS.md. Real data-hygiene gap that the periodic reaper is currently compensating for. The 2026-07-23 compatibility audit recommended the ADAPT path with full justification.

**Steps:**
1. Author RED tests in `tests/hermes_cli/test_api_server_session_finalization.py` (or similar) that exercise:
   - `_run_agent()` cancellation
   - `_run_agent()` exception
   - `_run_agent()` structured-failure return
   - `/v1/runs` cancellation
   - `/v1/runs` exception
   - `/v1/runs` structured failure
   - `/v1/runs` cooperative stop
   - **Negative test:** successful resumable API turn is NOT prematurely ended
2. Run the RED tests, confirm they fail (no failure finalizer exists).
3. Implement the async, per-profile failure finalizer using `_ensure_session_db_async()`.
4. Verify RED tests pass.
5. Re-run `~/.hermes/scripts/detect_api_server_fastclose.py` — should now PASS.
6. Update `~/.hermes/PATCHES.md` section 5 to reflect the new ADAPT design.

**Effort:** ~2-3 hours of focused engineering. Not a cron task.

## P2. Add 21st section to verify_update.py

**Why:** L2 from KNOWN_LIMITATIONS.md. The standalone verifier should self-run the 4-detector suite so a future investigator reading only the verifier evidence can see the patch state.

**Steps:**
1. Add section 21 to `verify_update.py`:
   ```python
   rc, out = sh("python3 ~/.hermes/scripts/detect_all_local_patches.py 2>&1", timeout=60)
   check("21.local-patches", "4-detector suite runs", rc in (0, 1), f"exit={rc}")
   check("21.local-patches", "all 5 expected patches present (adapt for known api_server regression)",
         "PATCH 5" in out or "api_server" in out.lower(),
         f"out tail: {out.strip().splitlines()[-3:] if out.strip() else '(empty)'}")
   ```
2. Run, confirm exit 0.
3. Commit for future audits.

**Effort:** 10 minutes.

## P3. Compress MEMORY.md

**Why:** L3 from KNOWN_LIMITATIONS.md. At 100% capacity, the `memory` tool will reject new `add` operations.

**Steps:**
1. Run `python3 /home/openclaw/apps/hermes-agent/venv/bin/python3 /home/openclaw/.hermes/scripts/compact_memory.py`.
2. Review the diff, accept or reject proposed removals.
3. Confirm `hermes --version` and a quick `memory` round-trip still work.

**Effort:** 15-30 minutes.

## P4. Compress USER.md

**Why:** L4 from KNOWN_LIMITATIONS.md. At 99%, near capacity.

**Steps:**
1. Run the same compact script with `--target user` (or edit the script's target).
2. Prefer compressing prose-heavy entries; preserve reference-heavy entries (IPs, paths, hex codes).
3. Confirm content integrity.

**Effort:** 15-30 minutes.

## P5. Publish local carries to a remote branch

**Why:** Operator-policy doctrine (per `~/.hermes/scripts/OV_DEPLOYMENT_POLICY.md` Rule 4). The +3 carried commits sit ahead of origin/main and survive only because the merge on every `hermes update` carries them forward. A `git reset --hard origin/main` would silently destroy them.

**Steps:**
1. Verify forks with `git remote -v` and a dry-run push to `fork`/`fork-ssh`.
2. Confirm the operator's GitHub account can push to `Ramadas108/hermes-agent.git` (the personal fork).
3. Run the lens-vs-noise probe: `git diff origin/main..HEAD --stat`.
4. `git checkout -b preserve-$(date +%Y%m%d-%H%M%S)` and `git push fork HEAD:refs/heads/preserve-<ts>`.
5. Record the published branch in MEMORY.md.

**Effort:** 10 minutes if the fork auth is in place; longer if it isn't.

## P6. Decide on safe-update CLI subcommand

**Why:** Informational drift. The wrapper script is the canonical update path on this host, and the `hermes safe-update` CLI subcommand is informational-only. If the operator never plans to upstream it, the obsolete reapply recipe in `~/.hermes/skills/devops/hermes-update-verify/references/known-local-patches-2026-07-14.md` could be retired or annotated.

**Steps:** Operator decision required. Not a cron task.

## Periodic checks (already covered by cron)

- `hermes doctor` health check (cron)
- `system-sentinel` daily reducer
- `subagent_health_gate` before any delegation
- Weekly binary maintenance (cron)
- OpenViking nightly consolidation (cron)
