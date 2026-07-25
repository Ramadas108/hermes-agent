# Next Maintenance Checks — Hermes Update 2026-07-05

Run from any clean shell, no setup required.

## Daily (or whenever the operator runs `hermes update`)
```bash
python3 ~/apps/hermes-agent/hardening_audit/hermes-update-2026-07-05/verify_update.py
```
Expect 45/45 PASS, exit 0. SHA-pin the verifier beforehand if you want
discipline-level confirmation:
```bash
EXPECTED=$(sha256sum ~/apps/hermes-agent/hardening_audit/hermes-update-2026-07-05/verify_update.py | awk '{print $1}')
# save this; compare after any future run
```

## Weekly
```bash
hermes doctor
hermes cron list
git -C ~/apps/hermes-agent status --short
```
Expect: doctor clean, cron list shows expected jobs, git status matches the
baseline of `3 modified + 6 untracked` (or `4 modified` if you touched one of
the working files; the verifier's count check is the live source of truth).

## Before the next `hermes update`
1. Confirm OpenViking health: `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:1933/health` — expect `200`.
2. Confirm gateway is healthy: `hermes gateway status` — expect `active (running)`.
3. Run the verifier once to record pre-state.
4. After update, re-run the verifier; expect the same PASS count (or close to it; new checks may be added by future audit sessions).

## If a verifier check ever flips FAIL
1. Read the section in the report output — section name + check name is unambiguous.
2. Cross-check by hand: the verifier's command is right above the `check()` call; copy-paste and inspect.
3. If the system genuinely regressed: file a bug, revert the affected commit, retry.
4. If the verifier is wrong (false negative): patch the verifier, document why in `FIX_LOOP_LOG.md`, re-run.

## If you want to retire this audit
- This audit captures a single point-in-time verification. The verifier stays
  useful as a future check — the format/CLI assumptions are documented in
  `verify_update.py` comments. Update the version references in
  `ACCEPTANCE_CRITERIA.md` if you re-run on a different date.
- The 22 criteria + 16 sections are stable for any hermes update; only the
  untracked-count assertion and the dashboard dist path may need updating if
  the repo layout changes.