# Riker Final Audit — Hermes Update 2026-07-15

## Audit Posture

Adversarial, forensic. Every claim in the audit folder must trace to a tool invocation
or a file in the tree. Verifier assertions are reproducible from a clean shell.

## Cross-Checks Performed

### 1. Version truth

`hermes --version` → v0.18.2 (2026.7.7.2). Gateway `/health` returns `version: 0.18.2`.
Both match. No drift.

### 2. Working tree truth

`git status --short` shows 3 modified + 7 untracked + 0 unmerged. Verifier independently
re-derived the same numbers. The 3 modified files (auxiliary_client.py, api_server.py,
transcription_tools.py) match the +4 carried commit set minus the auto-applied safe_update
and arrow-fix patches. Coherent.

### 3. Carried commit integrity

`git log --oneline -4` shows the local patch commits on top of upstream a7ef17da7. No
force-push happened during the update. No rebases. No reverts. Pure merge.

### 4. Stash lifecycle

`git stash list | grep $(date -I)` → empty. The wrapper's autostash was successfully
dropped after the clean apply. No orphan stash.

### 5. Local patches survived

- `def cmd_safe_update` references in `hermes_cli/main.py` (2) and
  `hermes_cli/subcommands/safe_update.py` (3). Module present.
- `~/.hermes/scripts/detect_multiline_arrow_fix.py cli.py` → PASS.

### 6. Untracked orphans

7 untracked items. All have a known provenance:

- `agent/auxiliary_client.py.taf-minimax-fallback-20260620-194458` — TAF minimax ledger
- `hardening_audit/` — today's audit output (intended)
- `plugins/memory/openviking/finalizer.py`, `registry.py`, `registry_invariant.py` —
  OpenViking plugin modules (pre-existing from prior session)
- `tests/agent/test_auxiliary_minimax_oauth.py` — new since 2026-07-05 baseline
- `tinker-atropos/` — pre-existing

None orphaned by the update.

### 7. Verifier reproducibility

SHA-256 of verifier: `c8d46ccfc650644261af458745700f538b6f7157dcd945877d95dc0e84300e45`.
Re-run from `/tmp/` with a fresh shell invocation: PASS, exit=0.

### 8. Synthetic known-bad test

Section 20 injects a tempfile with `def broken(:` and runs `py_compile`. Verifier reports
the failure as expected (false-positive guard). Confirms the verifier's py_compile
detection is real and not a silent false-pass.

### 9. Conflict marker probe

No `<<<<<<<` in the 3 modified files. Auto-merge succeeded cleanly without manual
intervention.

### 10. Model chain unchanged

`config.yaml` `provider: minimax-oauth` — same as before update. No agent mutation
violation per AGENTS.md rule. Model switched earlier today was operator-initiated (this
session prompt), pre-existing.

## Findings

None. Update is rock-solid.

## Outstanding Items (Not Regressions)

- Behind 61 commits on nightly head — expected; will pull next `hermes update`.
- The 12 uninstalled transitive packages (anthropic 0.87.0, fal-client, etc.) are cleanup
  of stale dependencies; no caller code references them in the tree.
- Lazy-backend "may require Python restart" warnings — cosmetic per doctrine, will
  resolve on next Python restart.

## Verdict

PASS. No rollback required. No patches required. System is in a verified-stable state.