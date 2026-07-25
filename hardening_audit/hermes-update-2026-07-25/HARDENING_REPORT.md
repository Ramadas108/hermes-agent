# Hardening Report — Hermes Update 2026-07-25

Date: 2026-07-25
Operator: Alex Martin Bee (Picard session)
Verification skill: `hermes-update-verify` v0.3.1
Verifier: `verify_update.py` (307 lines, 45 checks across 16 sections)

## Summary

The 2026-07-25 `hermes update` cycle completed successfully. 598 upstream commits were pulled, the working tree is clean of merge conflicts, three tracked local modifications and three local patches survived the round-trip, and the gateway restarted healthy. The verifier passed 45/45 after two verifier-bug fixes.

## Hardening actions taken

1. **Pre-flight:** verified `git status --short` before wrapper, recorded `unmerged=0`, `modified=3`, `untracked=8`, `ahead=2`, `HEAD=1ca30c77`.
2. **Read-only check:** `hermes update --check` reported 598 commits behind — confirmed the gap was real.
3. **Live update:** invoked the canonical wrapper `bash ~/.hermes/scripts/hermes-update-with-extras.sh`. Wrapper logged `[update-extras] SUCCESS: Gateway is active and healthy.`
4. **Detector sweep:** wrapper's 4-detector suite returned 3 PASS + 1 known ADAPT-flagged regression. The regression is the API-server fast-close hook, which the 2026-07-23 compatibility audit already flagged as ADAPT/REAL GAP.
5. **Verifier:** authored `verify_update.py` from the 2026-07-15 template, patched date-anchored constants, ran twice, all 45 checks PASS after 2 verifier-bug fixes.
6. **Audit artifacts:** wrote 7 markdown files, `verifier_run.json`, and the verifier itself.

## Patches that survived

- **Arrow-key history navigation fix** (`cli.py` — `history_up`/`history_down` distinguish buffer cursor movement from history browsing). Detector: `~/.hermes/scripts/detect_multiline_arrow_fix.py`. PASS.
- **`language='en'` in `_transcribe_openai`** (`tools/transcription_tools.py`). Detector: `~/.hermes/scripts/detect_transcription_language_en.py`. PASS — the policy is now config-driven (`stt.openai.language` propagation); the active config still defaults to provider auto-detect (no operator authorization to enable).
- **MiniMax OAuth branch in `resolve_provider_client`** (`agent/auxiliary_client.py`). Detector: `~/.hermes/scripts/detect_minimax_oauth_branch.py`. PASS.

## Known regression (awaiting ADAPT-grade fix)

**API-server fast-close hook** (`gateway/platforms/api_server.py`). The `_end_api_session_on_failure` method is missing. The 2026-07-23 compatibility audit verified this is a real gap (orphan-state rows in `state.db` for API agent runs that fail or are cancelled are currently compensated by the periodic `state_db_reaper`, not closed at request-time). The audit's recommendation:

> ADAPT / REAL GAP. The original behavior remains required, but the implementation and detector must be redesigned around the current architecture. Correct design should include an async, per-profile failure finalizer using `_ensure_session_db_async()`, both `_run_agent()` and `/v1/runs` coverage, explicit end reasons, focused tests, and a negative test proving successful resumable turns are not prematurely ended.

The next hardening cycle should treat this as a scoped engineering task with RED tests first. **Not** in scope for this update ritual.

## Auxiliary observations

- MEMORY.md is at 100% capacity (8,067 / 8,000 chars). The next session should consider running `compact_memory.py` to make room. The 2026-07-24 doctrine (after the constraint-blocking episode) recommends surgical removal of stale entries or compression of prose, not bulk deletion.
- USER.md is at 99% capacity (3,942 / 4,000 chars). Same posture.
- The `agent-mutation-guard` rule in AGENTS.md was respected throughout this ritual — no config.yaml edits were made.
- The wrapper's `safe-update` CLI subcommand is informational-only since v0.18.2; the wrapper script is the canonical path.

## Provenance

- Wrapper script: `~/.hermes/scripts/hermes-update-with-extras.sh`
- Verifier template: `~/apps/hermes-agent/hardening_audit/hermes-update-2026-07-15/verify_update.py`
- Compatibility audit: `~/apps/hermes-agent/hardening_audit/hermes-update-2026-07-23/COMPATIBILITY_AUDIT.md`
- Local patches: `~/.hermes/PATCHES.md`
- Knowledge: `~/.hermes/skills/devops/hermes-update-verify/SKILL.md`
