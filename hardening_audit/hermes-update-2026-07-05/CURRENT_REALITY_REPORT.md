# Current Reality Report — Hermes Update 2026-07-05

Inspected at 16:50 WEST on 2026-07-05, immediately after `hermes update`
completed at 16:47 WEST. All values come from live system inspection,
not from prior session memory or assumptions.

## Repository state
- Path: `/home/openclaw/apps/hermes-agent`
- HEAD: `5b04a024a5ed6badcc3ba5d5a6f5afcb642aa474` (on `main`)
- Branch sync: 0 ahead, 0 behind `origin/main`
- Modified files (3): `agent/error_classifier.py`, `agent/transports/chat_completions.py`, `tools/transcription_tools.py` — all restored from stash without `UU`/`AA`
- Untracked files (6): `agent/auxiliary_client.py.taf-minimax-fallback-20260620-194458`, `hardening_audit/`, `plugins/memory/openviking/{finalizer.py,registry.py,registry_invariant.py}`, `tinker-atropos/`
- Stash list: today's `hermes-update-autostash-20260705-164750` was successfully applied and dropped (success signal)
- No zip backup created (default config: `pre_update_backup: false`). The most recent zip backups are 2026-06-10 (8.4 GB), 2026-06-08 (3.6 GB), 2026-05-29 (3.4 GB) — these are the historical record. Today's update used the cheap git-stash path, as predicted.

## Update operation result
- 184 new commits pulled from origin/main (176 at `--check`, 8 in the window between check and update)
- venv reinstalled: `Resolved 95 packages in 376ms / Built hermes-agent / Prepared 1 package in 2.02s`
- Node deps updated: repo root + ui-tui + web workspaces
- Bundled skills synced; 19 user-modified kept (default), 4 (geordi)
- Gateway restarted: `hermes-gateway: draining (up to 315s)... Restarted hermes-gateway`

## Lazy backend status (known-warning category)
15 of 22 lazy backends failed to refresh with "install reported success but packages still not importable (may require Python restart)":
- provider.bedrock, provider.vertex
- search.firecrawl
- stt.faster_whisper
- image.fal
- memory.hindsight
- platform.{telegram, discord, slack, matrix, teams}
- skill.google_workspace
- tool.{dashboard, vision, computer_use}

These are documented as "expected behaviour" in the
hermes-update-verification-template.md — the next `hermes update` retries
them. For the current session they keep their previously-installed versions.

## Active state per domain
- Gateway: `active (running)` confirmed
- OpenViking: HTTP 200 on `/health` (probe path `/` returns 404, that's normal)
- Memory provider: declared healthy at the endpoint level
- Cron jobs: active count > 0 via `hermes cron list`
- MCP servers: 4 enabled (`fli`, `gcal-readonly`, `gmail_history`, `wp-audit-remote`)
- Profiles: `default` (active, model MiniMax-M3) + `geordi` + `riker` (both stopped)
- Config: latest `_config_version` constant present in `DEFAULT_CONFIG`
- Sessions DB: `~/.hermes/state.db` exists, > 1KB
- Web UI build: `hermes_cli/web_dist/index.html` present

## What this audit did NOT touch
- The 3 locally-modified files (left as the operator stashed them)
- The 6 untracked items (preserved in working tree)
- Any bundled skill (kept, not overwritten)
- The venv (rebuilt by hermes update; left as-installed)
- Any cron job or active memory provider state