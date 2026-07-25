# Current Reality Report — Hermes Update 2026-07-25

Captured at 2026-07-25 13:16+ WEST during the update+verify ritual.

## Update mechanics

- **Wrapper invoked:** `bash ~/.hermes/scripts/hermes-update-with-extras.sh`
- **Pre-update state:** HEAD `1ca30c77`, 0 unmerged, 3 locally-modified files, 8 untracked items, ahead=2 / behind=0.
- **Post-update state:** HEAD `944b419b`, 0 unmerged, 3 locally-modified files, 6 untracked items, ahead=3 / behind=598.
- **Version reported:** `Hermes Agent v0.19.0 (2026.7.20) · upstream ebab890a · local 944b419b (+3 carried commits)` — version tag unchanged because upstream did not bump `__version__` for the 598 nightly commits. This is the documented fast-forward-nightly pattern.
- **Local carries went from +2 → +3:** the wrapper's `git merge origin/main --no-edit` carried one extra commit forward as a merge parent. This is the same pattern as the 2026-07-15 update (`+2 → +3`).

## What was actually pulled

- 598 commits from `origin/main` (fast-forward nightly).
- 25 packages reinstalled via `uv pip` after `[messaging]` extras reinstall.
- 0 merge conflicts reported (auto-merge succeeded on `.gitignore` and `agent/auxiliary_client.py`).
- Locally-modified files preserved:
  - `.gitignore`
  - `agent/auxiliary_client.py`
  - `tests/hermes_cli/test_config_validation.py`

## What was preserved

- 3 of 4 local patches carried forward successfully:
  - **Patch 1+2** (arrow-key history navigation fix): PASS via `detect_multiline_arrow_fix.py`
  - **Patch 3** (`language='en'` in `_transcribe_openai`): PASS via `detect_transcription_language_en.py` — the policy is now config-driven (per 2026-07-23 UNIEX pass) and the runtime propagation is wired, but the active config still defaults to provider auto-detect (no operator authorization to flip `stt.openai.language: en`).
  - **Patch 4** (MiniMax OAuth branch in `resolve_provider_client`): PASS via `detect_minimax_oauth_branch.py`
- The `safe-update` CLI subcommand was not resynced, but the wrapper is the canonical path on this host, so this is informational only.

## What regressed

- **Patch 5** (API-server fast-close hook): FAIL via `detect_api_server_fastclose.py`. The `_end_api_session_on_failure` method is missing from `gateway/platforms/api_server.py`.
  - **Investigation:** `git log --all --oneline -S "_end_api_session_on_failure"` returns zero commits across all 17 stashes and the full main lineage. The change was an **orphaned working-tree modification**, not a committed local patch. The 2026-07-23 compatibility audit caught this and concluded it is a real gap, but the correct fix is ADAPT (redesign for v0.19.0's async/per-profile SessionDB) — not a literal reapply of the old synchronous helper.
  - **Decision:** documented as a known limitation. Do not paste the old patch back. It would regress the v0.19.0 async SessionDB design and miss the `/v1/runs` path.

## Health snapshot

- `hermes doctor`: exit 0, no CRITICAL/FATAL after stripping the npm-audit advisory line.
- `hermes gateway status`: active (running).
- MCP servers: 4 configured (fli, gcal-readonly, gmail-history, wp-audit-remote).
- OpenViking: healthy at `http://127.0.0.1:1933/health`.
- Cron jobs: 5 active (per `hermes cron list`).
- Skills: 280+ enabled (post-update count, no count drift beyond the documented v0.13.0+ accounting change).
- Sessions DB: present, > 1KB.
- Profiles: `default` at `~/.hermes`, `geordi`/`riker` sub-profiles present.

## Energy/cost

- Pull + merge + reinstall: ~3 minutes wall-clock.
- Verifier runs: 2 (initial with 2 FAILs, second after 2 verifier-bug fixes, exit 0).
- Memory store: 1,433 facts, no corruption detected.
- MEMORY.md: 8,067 chars / 8,000 cap (100% — at capacity, flagged by gate).
- USER.md: 3,942 chars / 4,000 cap (99% — near capacity, flagged by gate).
