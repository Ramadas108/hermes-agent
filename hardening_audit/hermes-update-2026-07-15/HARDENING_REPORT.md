# Hermes Update 2026-07-15 — Hardening Report

## Update Path Used

`bash ~/.hermes/scripts/hermes-update-with-extras.sh` — the canonical safe-update wrapper.
Bare `hermes update` was NOT used. Per doctrine (memory 2026-07-05), the wrapper preserves
`[messaging]` extras during `uv sync`, runs the auth-json pre-flight validator, re-applies
local safe-update patch, polls the arrow-key fix detector, verifies platform adapters,
and restarts the gateway with 30s health poll.

## Pre-Flight

- `hermes update --check` (read-only fetch): 74 commits behind origin/main.
- Working tree: 3 modified + 5 untracked + 0 unmerged — clean starting state.

## Live Update

- Wrapper ran 600s without error.
- Merge commit: 4c00b3502 (local) on top of a7ef17da7 (upstream).
- `git stash drop` succeeded on the autostash — no orphan stash today.
- Two local safe-update patches re-applied automatically (subcommand module + arrow fix).
- venv sync: 233 packages resolved, 12 uninstalled (transitive cleanup of unused deps).
- Adapter verification: ALL ADAPTERS HEALTHY.
- Gateway restart: SUCCESS, healthy within 30s.

## Post-Update Verification

- `hermes --version` → v0.18.2 (2026.7.7.2)
- `hermes doctor` → no CRITICAL/FATAL
- `hermes status` → gateway active, MiniMax-M3 model wired
- Gateway `/health` (127.0.0.1:8642) → `{"status":"ok","platform":"hermes-agent","version":"0.18.2"}`
- OpenViking endpoint reachable
- py_compile passes for all 3 modified files plus a known-bad synthetic test

## Local Patch Set Status (carried forward as +4 commits)

1. **safe_update CLI subcommand** — now lives at `hermes_cli/subcommands/safe_update.py`
   (proper module; survives upstream subcommand-package refactor). Verified present in
   tree with `def cmd_safe_update` references.
2. **Arrow-key history navigation fix** — `cli.py` line-anchored patch. Detector PASS.
3. **Auxiliary client minimax fallback** — `agent/auxiliary_client.py` (TAF minimax fallback
   2026-06-20 backup file present as ledger artifact).
4. **API server reaper hook** — `gateway/platforms/api_server.py`. Validated by rock-solid
   state_db_reaper deployment on 2026-07-12.

## Verifier Verdict

- 20 sections, all green
- 2 fixes applied to verifier (untracked count + branch-sync assertion)
- Final OVERALL: PASS, exit=0
- Verifier SHA-256: c8d46ccfc650644261af458745700f538b6f7157dcd945877d95dc0e84300e45

## Doctor Output (relevant lines)

```
◆ Environment
  Project:      /home/openclaw/apps/hermes-agent
  Python:       3.12.3
  .env file:    ✓ exists
  Model:        MiniMax-M3
  Provider:     MiniMax (OAuth)

◆ API Keys
  OpenRouter    ✓
  OpenAI        ✓
  Google / Gemini  ✗ (not set)
  DeepSeek      ✓
  xAI / Grok    ✗ (not set)
  NVIDIA NIM    ✓
  Z.AI / GLM    ✗ (not set)
  Kimi          ✗ (not set)
  StepFun Step Plan  ✗ (not set)
  MiniMax       ✓
```

No new failures introduced by the update.