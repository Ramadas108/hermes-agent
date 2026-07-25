# Next Maintenance Checks — Hermes Update 2026-07-15

## Tomorrow (or on next hermes invocation)

- [ ] Verify the operator's manual probes (if any) match the verifier verdict.
- [ ] If the operator asks "what was the update?" — point to
      `~/apps/hermes-agent/hardening_audit/hermes-update-2026-07-15/HARDENING_REPORT.md`.

## Next hermes update

- [ ] Re-run `bash ~/.hermes/scripts/hermes-update-with-extras.sh` when the gap
      grows beyond ~80 commits OR when operator says "hermes update".
- [ ] Update the verifier's `untracked count` constant if the untracked set changes.
- [ ] Run `pytest tests/` out-of-band if operator wants test coverage validation.

## Pre-flight before next update

```bash
# Working tree clean?
cd ~/apps/hermes-agent
git status --short
git diff --name-only --diff-filter=U | wc -l   # must be 0

# How far behind?
hermes update --check

# Local patches still alive?
/usr/bin/python3 ~/.hermes/scripts/detect_multiline_arrow_fix.py ~/apps/hermes-agent/cli.py
ls ~/apps/hermes-agent/hermes_cli/subcommands/safe_update.py
```

## Verifier lifecycle

- SHA-256: c8d46ccfc650644261af458745700f538b6f7157dcd945877d95dc0e84300e45
- Authoring: copy this folder as the next `hermes-update-<date>/` and run.
- Patches: if CLI formats drift, edit `verify_update.py` (sections 1, 4, 5) and
  document the change in `FIX_LOOP_LOG.md`.