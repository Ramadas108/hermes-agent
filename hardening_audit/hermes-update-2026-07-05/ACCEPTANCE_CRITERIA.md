# Acceptance Criteria — Hermes Update 2026-07-05

Scope: post-update verification of `hermes update` completed at 16:47 WEST
on 2026-07-05. Pulled 184 commits from origin/main, stashed 3 locally-modified
files, restored them, restarted the gateway. Built on the
`hermes-update-verification-template.md` precedent (22 criteria).

## Hard scope (what must pass)
1. Version: hermes reports the new vX.Y.Z.
2. Git worktree: 0 unmerged files, branch on `main`, HEAD attached, all 3
   locally-modified files restored without `UU`/`AA` markers.
3. Pre-update snapshot exists at the documented path.
4. Stash created and applied without conflict.
5. All 5 untracked items (3 OpenViking plugins + `hardening_audit/` + `tinker-atropos/`)
   still present after the update.
6. Config version matches latest, no migration needed.
7. `hermes doctor` exits clean.
8. Gateway `active (running)`, restarted post-update.
9. All `hermes tools list` core toolsets enabled.
10. Memory provider (OpenViking) healthy.
11. Cron jobs preserved, scheduler operational.
12. MCP servers connected.
13. Sessions DB intact (count > 0).
14. All profiles intact.
15. Python core imports work.
16. Bundled skills synced; 19 user-modified skills preserved.
17. The 3 locally-modified `.py` files pass `py_compile` (template #22).
18. No conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) in any
   locally-modified file's text content.
19. Auth credentials intact, validator passes.
20. Node deps (web UI) built and importable.

## Soft scope (documented, not blocking)
- 15 lazy-backend warnings ("may require Python restart"). Known post-update
  state per template's "Pre-existing Issues" section.
- npm vulnerabilities (esbuild/vite) — transitive, not blocking.
- Missing optional API keys for unconfigured platforms — out of scope.

## Out of scope
- Touching the 3 modified files or 5 untracked items (preservation is the goal).
- Any change to git config, venv, or skills.
- Future update verification (this is the post-update check, not a CI).

## "Rock solid" means here
After this verifier passes, the next session that touches `~/apps/hermes-agent/`
can do so with the same confidence as before the 184-commit pull — no hidden
conflicts, no broken imports, no silent gateway death, no config drift.

## Risks most likely to materialise
1. Conflict markers hidden inside one of the 3 modified files that
   `git diff` masks (template #22's primary concern).
2. Gateway appears running but is degraded.
3. Memory provider health degraded (today's OV auth issue is unresolved).
4. Cron jobs that reference paths or models no longer valid in the new version.
5. A bundled-skill sync that silently overwrote a user-modified skill.

## Convergence guard
- MAX_ITERATIONS: 3 fix-loop iterations.
- MAX_TOOL_CALLS: 200.
- DID NOT CONVERGE if 3 consecutive iterations make zero net progress.