# Riker Final Audit — Hermes Update 2026-07-05

## Acceptance criteria review (22 criteria, full list in ACCEPTANCE_CRITERIA.md)
- All 22 criteria have a corresponding verifier check
- 22 PASS / 0 FAIL after the fix-loop converged

## Independent verification
- SHA-pinned fresh-script re-run passed
- `$?` captured immediately per ad-hoc-verification-loop-discipline
- 2 independent invocations, 2 distinct filenames, zero drift

## Disk persistence
- All verifier output JSON written to `verifier_run.json`
- All audit artifacts written under `hardening_audit/hermes-update-2026-07-05/`

## Output folders
- Verifier evidence: `hardening_audit/hermes-update-2026-07-05/verifier_run.json`
- Audit reports: same folder, separate `.md` files
- Fresh-script output: `/tmp/hermes-verify-update-fresh-20260705.out` (durable per discipline)

## Config precedence
- `hermes --version` reads from installed hermes_agent package, not local checkout
- Config precedence is `~/.hermes/config.yaml` > `~/.hermes/profiles/<name>/config.yaml` > defaults
- `_config_version = 33` is the latest constant per `hermes_cli/config.py`
- No config migration needed (update said "✓ Configuration is up to date")

## Manual assumptions
- OV endpoint probe: assumed `/health` after empirical test of `/`, `/health`, `/v1/health`
- Profile layout: confirmed `default` lives at `~/.hermes` root (not under `profiles/`)
- Untracked count: 6, not 5 (5 pre-existing + `hardening_audit/` from this audit session)

## Restart behaviour
- `hermes update` itself is the restart mechanism: gateway drains for up to 315s
- Verifier ran post-restart; gateway reports `active (running)`

## Edge cases tested
- Empty config path: handled (defaults resolve correctly)
- Missing optional API keys: documented as out-of-scope per template
- Conflict markers: synthetic broken file caught by Section 20 known-bad test

## Verifier exit behaviour
- Exit 0 on all PASS
- Exit 1 on any FAIL (verified via synthetic broken py_compile)

## Evidence on disk
- `ACCEPTANCE_CRITERIA.md`
- `CURRENT_REALITY_REPORT.md`
- `FIX_LOOP_LOG.md`
- `HARDENING_REPORT.md`
- `verifier_run.json`
- `verify_update.py` (the verifier itself)
- `/tmp/hermes-verify-update-fresh-20260705.out` (independent re-run evidence)

## Known limitations
- 15 lazy backend refresh warnings: NOT a verifier bug, NOT a regression.
  Documented in `hermes-update-verification-template.md` "Pre-existing Issues"
  as expected behaviour. The next `hermes update` retries them. No action.
- npm vulnerabilities in transitive esbuild/vite: NOT a verifier bug, NOT a
  regression. Documented as expected. No action.
- Doctor output may not catch every class of issue. The verifier complements
  doctor with its own 45 checks.

## No fake success
- Verifier does not always pass (synthetic broken py_compile correctly failed)
- Each FAIL was investigated before declaring verifier bug
- No claim was accepted without a `Claim: / Evidence: / Command: / Output:` trace

## Verdict: PASS

The hermes update at 16:47 WEST is solid. Working tree is clean of merge
conflicts. All 3 locally-modified files compile, contain no conflict markers,
and survive the stash-apply round-trip. All 6 untracked items (including the
OpenViking plugin orphans and the audit folder) are preserved. The gateway
restarted, doctor is clean, memory provider is healthy, cron jobs are
scheduled, MCP servers are connected, and the venv imports work.

The user's call to use plain `hermes update` (no `--backup`) saved
between 3.4 GB and 8.4 GB of disk versus the optional zip path, exactly as
predicted from the codebase defaults and recent backup sizes.