# Permission Gate — Acceptance Criteria

## What was built
A `ToolPermissionGate` class implementing a 5-stage graduated trust pipeline,
inspired by Claude Code's architecture (arXiv:2604.14228 — 98.4% deterministic infrastructure).

Files: `tools/permission_gate.py`, `model_tools.py`, `hermes_cli/config.py`,
`hermes_cli/_parser.py`, `hermes_cli/main.py`, `hermes_cli/plugins.py`

## Acceptance Criteria

### AC1: 5-stage pipeline works
- [ ] Hardline blocks catastrophic patterns (rm -rf /, shutdown, reboot, mkfs, dd to /dev/)
- [ ] DENY rules block matched tool calls in ALL modes (autonomous, yolo, cron)
- [ ] ASK rules mark `requires_approval=True` on matched calls
- [ ] ALLOW rules auto-approve matched calls in all modes
- [ ] MODE fallback correctly gates by tool reversibility classification

### AC2: All 5 modes work correctly
- [ ] `plan` — allows read tools, denies writes/catastrophic
- [ ] `supervised` — requires approval on every tool call
- [ ] `cautious` — auto-allow reads, ask on writes
- [ ] `autonomous` — auto-allow everything (except hardline/deny)
- [ ] `plan_terminal_reads` config — safe terminal commands allowed in plan mode

### AC3: Deny rules are mode-immune
- [ ] DENY rules survive `yolo` mode
- [ ] DENY rules survive `autonomous` mode
- [ ] DENY rules survive `cron` context

### AC4: Backward compatibility
- [ ] `manual` mode maps to `supervised` with deprecation warning
- [ ] `smart` mode maps to `cautious` with deprecation warning
- [ ] `off` mode maps to `autonomous` with deprecation warning
- [ ] No gate instance = gate check skipped (backward compat for existing sessions)

### AC5: terminate tool blocked in all modes
- [ ] `terminate` tool blocked even in autonomous mode (hardline gate)
- [ ] Closes the `mode:off` bypass path

### AC6: Gate initializes from config
- [ ] Singleton pattern works via `init_instance()` / `get_instance()`
- [ ] Config schema validates and rejects `mode: off` with clear error
- [ ] CLI `-M tool=mode` flag merges with config `per_tool_mode`

### AC7: Plugin integration
- [ ] `gate_check` hook in VALID_HOOKS
- [ ] `get_gate_check_block_message()` function exists and returns None with no plugins

### AC8: No compilation errors
- [ ] All 6 modified files pass `py_compile`
- [ ] Permission gate module imports without errors
