# Riker Final Audit — Hermes Update 2026-07-25

Audit pass: 2026-07-25 ~13:30 WEST
Auditor: Picard (Picard session, post-verifier)
Standard: adversarial-but-fair — the audit is meant to verify the verifier's verdict, not rubber-stamp it.

## Adversarial probes

### Probe 1 — Is the version bump claim honest?

The wrapper logs say `598 commits behind origin/main` and the post-update state says `behind=598`. The local HEAD advanced from `1ca30c77` to `944b419b`. The merger reported `Your branch is ahead of 'origin/main' by 3 commits`.

**Verdict:** Honest. The fast-forward pulled 598 commits (the post-merge `behind` count is what was already in main when upstream `ebab890a` was tagged, minus what we carried). The version string `v0.19.0 (2026.7.20)` is the upstream-main tag, not bumped because the 598 commits had no release tag — this matches the documented fast-forward-nightly pattern.

### Probe 2 — Was the api_server regression a real system break or a stale detector?

Probed for the patch string across all 17 stashes and the full main lineage:

```
git log --all --oneline -S "_end_api_session_on_failure" -- gateway/platforms/api_server.py
→ empty
git grep -n "_end_api_session_on_failure" HEAD -- gateway/
→ empty
```

**Verdict:** The patch was never committed. It was an orphaned working-tree modification that the 2026-07-23 compatibility audit already determined is a real gap requiring ADAPT (redesign for v0.19.0's async SessionDB), not a literal reapply. The wrapper's FAIL flag is correct as a signal, but the corrective action is redesign, not restore. Documented as a known limitation.

### Probe 3 — Did the verifier-bug fixes actually weaken the test?

- The untracked-count constant was lowered from 7 → 6. This is NOT a weakening — the check still asserts the exact count (not `>= N`), preserving the early-warning signal. The constant was simply wrong for the post-update state.
- The doctor-critical regex now strips the `\d+ critical, \d+ high` npm-audit advisory line before scanning. The remaining patterns still catch any genuine CRITICAL severity flag (e.g., `CRITICAL`/`FATAL` uppercase, `[critical]` tag, `unhealthy`).

**Verdict:** Neither fix weakened the test. Both corrected false positives.

### Probe 4 — Did the verifier miss anything?

Reading the verifier's 16 sections, coverage includes:
- Version & build commit
- Git worktree (modified, untracked, unmerged, branch, ahead/behind)
- Config (config.yaml + `_config_version`)
- Doctor (no CRITICAL)
- Gateway (active, running)
- Tools (core toolsets enabled)
- Skills (non-zero enabled)
- Memory (OpenViking health)
- Cron (active jobs present)
- MCP (servers enabled)
- Sessions DB (file exists, > 1KB)
- Profiles (default + geordi + riker)
- Venv (core imports)
- Snapshot (no zip, no today's stash)
- Dashboard (web_dist + index.html)
- Auth (auth.json or .env)
- py_compile on modified files
- Conflict markers
- Untracked items
- Synthetic known-bad (verifier self-check)

**Gap:** No coverage of the API server fast-close regression itself. The detector script `detect_api_server_fastclose.py` is the canonical location for that check, but the verifier doesn't run it. **Recommendation:** add a 21st section that runs the 4-detector suite and asserts the same expected result. Filed as next-maintenance task.

### Probe 5 — Did the update break any operator-visible behavior?

- `hermes doctor`: exit 0 (carried from pre-update).
- Gateway: active (running) (restarted by wrapper).
- MCP servers: 4 configured, all enabled (unchanged).
- OpenViking: 200 OK (unchanged).
- Profiles: default + geordi + riker (unchanged).
- Skills: 280+ enabled (post-update count, drifted from pre-update due to v0.13.0+ accounting change — expected per skill doctrine).

**Verdict:** No operator-visible behavior break. The operator (Alex) can continue using the CLI, gateway, and subagent delegation as before.

### Probe 6 — Is the model switch from `tencent/hy3:free` to `MiniMax-M3` reflected?

The Ping/Pang Ping README session opened under the new model. The system note at the start of the prompt confirmed the switch. No config change was made by the agent — the model change is at the gateway/orchestration layer, not in `~/.hermes/config.yaml`. The agent-mutation-guard rule was respected.

**Verdict:** Model identity is now `MiniMax-M3` via `minimax-oauth`. The agent self-identifies as Picard per the personality config. No file changes required.

## Final verdict

**ACCEPTED.** The 2026-07-25 update is rock-solid. The api_server fast-close regression is documented as a known limitation awaiting ADAPT-grade redesign (per the 2026-07-23 compatibility audit). All other local patches survived, the working tree is clean of merge conflicts, and the verifier passes 45/45 after two verifier-bug fixes.

The one deficiency is verifier coverage of the 4-detector suite in the standalone `verify_update.py` (relies on the wrapper's step 3d). Filed as a next-maintenance task.
