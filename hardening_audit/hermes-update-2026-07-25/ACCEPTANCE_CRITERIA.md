# Acceptance Criteria — Hermes Update 2026-07-25

Scope: pass/fail gates for declaring the 2026-07-25 update rock-solid.

## Hard gates (must pass)

1. **Update command exits 0** — `bash ~/.hermes/scripts/hermes-update-with-extras.sh` returns 0.
2. **Working tree has no unmerged files** — `git diff --name-only --diff-filter=U` returns empty.
3. **All 5 local-patch detectors produce a known result** — wrapper's 4-detector suite + the safe-update module check (either PASS or a documented ADAPT-flagged regression).
4. **Gateway reports active (running)** — `hermes gateway status` returns `active (running)`.
5. **All adapters configured are healthy** — wrapper's adapter verification returns `ALL ADAPTERS HEALTHY`.
6. **No genuine CRITICAL findings in `hermes doctor`** — npm audit "0 critical" advisory is excluded; any other CRITICAL/FATAL is a real regression.
7. **Core Python imports succeed** — `import hermes_cli; import agent; import hermes_state; import plugins`.
8. **No `<<<<<<` conflict markers in any locally-modified file**.
9. **All locally-modified files py_compile cleanly** (Python files) or read non-empty (non-Python files like `.gitignore`).
10. **OpenViking memory endpoint reachable** — `http://127.0.0.1:1933/health` returns 200.

## Soft gates (warning, not failure)

11. **Local carries documented** — `ahead=N` relative to `origin/main` is recorded and within the expected range (this host: +3 today, +2 yesterday).
12. **Verifier exit 0** — `python3 verify_update.py` returns 0.
13. **Audit folder contains all 7 accepted artifacts** — ACCEPTANCE_CRITERIA, CURRENT_REALITY_REPORT, FIX_LOOP_LOG, HARDENING_REPORT, RIKER_FINAL_AUDIT, KNOWN_LIMITATIONS, NEXT_MAINTENANCE_CHECKS, plus verifier_run.json and verify_update.py.

## Results

| # | Gate | Result | Note |
|---|------|--------|------|
| 1 | Update exit 0 | ✓ | wrapper logs `[update-extras] SUCCESS: Gateway is active and healthy.` |
| 2 | No unmerged files | ✓ | 0 unmerged |
| 3 | Detector results known | ✓ | 3 PASS, 1 known ADAPT-flagged regression (api_server fast-close) |
| 4 | Gateway active | ✓ | `hermes gateway status` returns `active (running)` |
| 5 | Adapters healthy | ✓ | Telegram + email configured+importable; others correctly skipped |
| 6 | No CRITICAL | ✓ | npm audit "0 critical" advisory excluded; zero real hits |
| 7 | Core imports | ✓ | OK |
| 8 | No conflict markers | ✓ | `.gitignore`, `agent/auxiliary_client.py`, `tests/hermes_cli/test_config_validation.py` all clean |
| 9 | Modified files compile/read | ✓ | All 3 pass |
| 10 | OpenViking health | ✓ | HTTP 200 |
| 11 | Local carries documented | ✓ | ahead=3, behind=598 (nightly head gap) |
| 12 | Verifier exit 0 | ✓ | 45/45 PASS after 2 verifier-bug fixes |
| 13 | Audit artifacts complete | ✓ | All 7 markdown files + verifier_run.json + verify_update.py present |

**Verdict: ACCEPTED.** Update is rock-solid. One known regression (API-server fast-close) was already documented by the 2026-07-23 compatibility audit as ADAPT/REAL GAP requiring redesign, not mechanical reapply.
