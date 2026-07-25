# Next Maintenance Checks — Permission Gate

- **When deploying**: Verify `hermes_cli/main.py::cmd_chat()` calls
  `ToolPermissionGate.init_instance()` before starting the agent loop.
- **When adding new tools**: Add reversibility classification to
  `_DEFAULT_CLASSIFICATIONS` in `tools/permission_gate.py`.
- **When implementing bubble trust**: Design JWT capability token scheme
  before writing code. See `hardening_audit/permission-gate-2026-06-15/PICARD_Q_SYNTHESIS.md`.
- **One command to re-check**: `python3 ~/apps/hermes-agent/hardening_audit/permission-gate-2026-06-15/verify.py`
