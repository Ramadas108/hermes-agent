# Known Limitations — Permission Gate

1. **No bubble trust mode** — deferred to Phase 3. Subagents use `restricted` + `escalate`.
2. **Time-based rules not implemented** — deferred to Phase 2/3 via `gate_check` plugin hook.
3. **gate_check hook registered but no reference plugin** — reference implementation needed.
4. **Gate is opt-in** — sessions without gate initialization have no gate check.
5. **Per-tool mode validation** — invalid mode strings silently default with warning.
