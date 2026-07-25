# Current Reality Report — Permission Gate

Date: 2026-06-15
Repo: /home/openclaw/apps/hermes-agent (git root)

## Working Directory
/home/openclaw

## Git Status
Permission gate files changed:
  M agent/file_safety.py          # Our P0 plugin denylist fix
  M hermes_cli/_parser.py         # Our -M/--tool-mode CLI flag
  M hermes_cli/config.py          # Our config schema + mode:off removal
  M hermes_cli/main.py            # Our gate initialization
  M hermes_cli/plugins.py         # Our gate_check hook
  M model_tools.py                # Our gate wiring in tool dispatch
 ?? tools/permission_gate.py      # Our NEW module (untracked)

Pre-existing dirty files (baseline, not our changes):
  M apps/bootstrap-installer/package.json
  M package-lock.json, package.json
  M plugins/memory/openviking/__init__.py
 A plugins/memory/openviking/finalizer.py
 A plugins/memory/openviking/registry.py
 A plugins/memory/openviking/registry_invariant.py
  M tools/transcription_tools.py
  M ui-tui/package.json, ui-tui/packages/hermes-ink/package.json
  M web/package.json

## Key Files — Summary
- tools/permission_gate.py: 544 lines, new module
- model_tools.py: gate check inserted after arg coercion (line ~920)
- hermes_cli/config.py: _validate_approvals_config() rejects mode:off
- hermes_cli/plugins.py: gate_check added to VALID_HOOKS
- hermes_cli/_parser.py: --tool-mode / -M flag on top-level + chat parser
- hermes_cli/main.py: ToolPermissionGate.init_instance() in cmd_chat()
- agent/file_safety.py: plugins/ added to write denylist

## Live Config
~/.hermes/config.yaml — approvals.mode: supervised, with deny/allow rules

## Python Version
Python 3.12.3
