# Known Limitations — Hermes Update 2026-07-15

## 1. Verifier depends on shell-stable CLI output formats

`hermes --version`, `hermes doctor`, `hermes status` outputs are regex-parsed. If
upstream changes the format (e.g. "0.18.2" → "Hermes Agent 0.18.2 (build)"), every
assertion in Section 1, 4, 5 may FAIL and look like a real regression. Mitigation:
probe each format with the live CLI before hardcoding the regex.

## 2. Untracked baseline drift

The verifier hardcodes `len(untracked) == 7` for today. Next update may add a new
untracked file (e.g. a TAF ledger backup) and the assertion will FAIL. Re-classify as
verifier-bug and update the constant.

## 3. nightly head gap

Verifier accepts `behind > 0` (the nightly main moves faster than our update cadence).
The "real" regression signal would be `ahead == 0 AND behind > 0` — meaning local was
rewound. Today we are `ahead=4 behind=61` — both intentional.

## 4. Lazy-backend restart warnings

15+ backends may emit "may require Python restart" warnings on a fresh update. These
are cosmetic; resolve on next Python restart. Not a regression.

## 5. Wrapper silent-write pitfall (pre-existing, mitigated)

The wrapper uses `patch -p1 -f` which can exit 0 with no diff applied. Mitigated by
the post-validate grep on `def cmd_safe_update` and by the wrapper's own
`[update-extras]   ✓ safe_update subcommand module present` line — which we observed
in this run. Full hardening recipe in
`~/.hermes/skills/devops/hermes-update-verify/SKILL.md`.

## 6. safe_update subcommand relocation (pre-existing fix from prior audit)

The wrapper's reapply no longer needs to patch `hermes_cli/main.py` line-by-line —
`safe_update` now lives in its own module file. The wrapper does the right thing
today. If upstream moves it again, the wrapper's grep-based check will FAIL and we'll
know to relocate.

## 7. Test suite not run

Verifier does not run `pytest`. 27 new test files landed in this update; we have not
executed them. If the operator wants full coverage validation, run `pytest tests/`
out-of-band and capture results separately.