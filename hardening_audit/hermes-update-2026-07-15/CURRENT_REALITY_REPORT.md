# Hermes Update 2026-07-15 — Current Reality

## Version State

```
Hermes Agent v0.18.2 (2026.7.7.2)
  upstream: a7ef17da7
  local:    4c00b3502  (Merge remote-tracking branch 'origin/main')
  ahead:    4 carried local commits
  behind:   61 commits (nightly main head)
Python:    3.12.3
OpenAI SDK: 2.31.0
Install:   /home/openclaw/apps/hermes-agent  (git)
```

The +4 carried commits are the local patch set: arrow-key history fix, safe-update
subcommand relocation (now a proper module at `hermes_cli/subcommands/safe_update.py`),
auxiliary client minimax fallback, and the api_server reaper hook.

## Working Tree

Modified (3, all pre-existing local patches — preserved):

- `agent/auxiliary_client.py`
- `gateway/platforms/api_server.py`
- `tools/transcription_tools.py`

Untracked (7 — preserved):

- `agent/auxiliary_client.py.taf-minimax-fallback-20260620-194458` (TAF minimax fallback ledger)
- `hardening_audit/` (today's audit folder; new today)
- `plugins/memory/openviking/finalizer.py`
- `plugins/memory/openviking/registry.py`
- `plugins/memory/openviking/registry_invariant.py`
- `tests/agent/test_auxiliary_minimax_oauth.py`  ← new untracked since 2026-07-05 baseline
- `tinker-atropos/`

## Runtime

- **Gateway**: running on 127.0.0.1:8642 (REST) and 10.43.145.84:8642 (LAN/telethon webhook)
  - Health: `{"status":"ok","platform":"hermes-agent","version":"0.18.2"}`
- **Model**: MiniMax-M3 via MiniMax (OAuth) provider — operator switched earlier today
- **Active credentials**: OpenRouter, OpenAI, DeepSeek, NVIDIA NIM, MiniMax
- **Adapters**: telegram + email configured/healthy; discord/slack/whatsapp/signal/matrix/sms/feishu/dingtalk skipped (env vars not set)
- **OpenViking**: endpoint reachable on 127.0.0.1:1933
- **Stash**: empty for today's date — success signal (clean apply)

## What Changed in This Update

74 commits pulled (wrapper initial check showed 74; final state shows 61 = nightly head
grew during the run, expected). Notable upstream changes touching our surface area:

- 94 files changed, +7,057 / −2,975 lines
- New: `apps/desktop/src/components/assistant-ui/tool/fallback.test.ts`
- Deleted: `apps/desktop/src/lib/remend-tail.test.ts`, `remend-tail.ts`
- New: `optional-mcps/blender/manifest.yaml`
- Substantial test coverage expansion: 27 new test files covering MOA reasoning effort,
  async delegation, WAL checkpoint, channel context consume, MCP server transport,
  slack gateway, MoA config, etc.
- `tools/async_delegation.py` (+17/-x), `tools/delegate_tool.py` (+14)
- `tools/environments/base.py` (+167/-x) — large environment abstraction rework
- 12 transitive packages uninstalled during venv sync (cleanup of moved/unused deps):
  anthropic 0.87.0, docstring-parser, eval-type-backport, fal-client, httpx-sse,
  importlib-metadata, jsonpath-python, mistralai, msgpack, opentelemetry-api,
  opentelemetry-semantic-conventions, zipp.

## Verifier Verdict

OVERALL: PASS. 20 sections, all green. Exit code 0.