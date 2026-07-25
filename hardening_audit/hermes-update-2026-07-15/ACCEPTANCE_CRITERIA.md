# Hermes Update 2026-07-15 — Acceptance Criteria

## Update Mechanics

- [x] Wrapper script `~/.hermes/scripts/hermes-update-with-extras.sh` exits 0
- [x] `git status` after update: 0 unmerged files (UU/AA)
- [x] Pre-existing stash list: no autostash survives (clean merge)
- [x] 3 locally-modified files preserved across update:
  - `agent/auxiliary_client.py`
  - `gateway/platforms/api_server.py`
  - `tools/transcription_tools.py`
- [x] 6 pre-existing untracked items preserved (plus hardening_audit/)
- [x] safe_update subcommand module present at `hermes_cli/subcommands/safe_update.py`
- [x] Arrow-key history navigation fix detected as PASS by
  `~/.hermes/scripts/detect_multiline_arrow_fix.py`

## System Health

- [x] `hermes --version` reports v0.18.2 (2026.7.7.2)
- [x] Upstream HEAD a7ef17da7; local HEAD 4c00b3502 (merge commit); +4 carried local commits
- [x] Branch is `main`, HEAD attached, not detached
- [x] Branch ahead=4 behind=61 (nightly head gap; expected — wrapper run started at 61)
- [x] `hermes doctor` — no CRITICAL/FATAL findings
- [x] `hermes status` reports gateway active, model MiniMax-M3 via MiniMax OAuth
- [x] Gateway `/health` returns `{"status":"ok","platform":"hermes-agent","version":"0.18.2"}` on 127.0.0.1:8642
- [x] Adapter verification: ALL ADAPTERS HEALTHY (telegram + email active; rest skipped-not-configured)
- [x] OpenViking endpoint reachable
- [x] Core hermes modules import
- [x] py_compile passes for `agent/error_classifier.py`, `agent/transports/chat_completions.py`, `tools/transcription_tools.py`
- [x] No conflict markers (<<<<<<<) in modified files
- [x] venv sync with [messaging] extras — resolved 233 packages, 12 uninstalled (expected transitive cleanup)

## Verifier Pass

- [x] `verify_update.py` runs end-to-end, exits 0
- [x] OVERALL: PASS — all 20 sections green
- [x] Known-bad synthetic test (Section 20) confirms verifier detects broken py_compile — no silent false-pass
- [x] Verifier SHA-256: c8d46ccfc650644261af458745700f538b6f7157dcd945877d95dc0e84300e45