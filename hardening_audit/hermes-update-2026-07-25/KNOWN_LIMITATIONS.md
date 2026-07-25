# Known Limitations — Hermes Update 2026-07-25

## L1. API-server fast-close hook is absent (ADAPT / REAL GAP)

**Affected file:** `gateway/platforms/api_server.py`
**Severity:** Medium data hygiene
**Source:** 2026-07-23 compatibility audit Finding 3, detected as a regression by `~/.hermes/scripts/detect_api_server_fastclose.py`.

**Symptom:** API-owned agent runs that fail or are cancelled leave `session_id` rows in `state.db` with `ended_at=NULL` and `end_reason=NULL`. The periodic `state_db_reaper` closes them as `orphaned_no_close` asynchronously, but at request-time there is no durable close.

**Scope:** Two distinct API execution paths:
1. `_run_agent()` (chat/session/responses routes) — `api_server.py:4738-4833`
2. `/v1/runs` `_run_and_close()` — `api_server.py:5030-5230`, which constructs and runs an agent directly and never calls `_run_agent()`.

**Why the old patch must not be pasted back unchanged:**
- v0.19.0 introduced async/per-profile SessionDB initialization (`_ensure_session_db_async`); the old synchronous helper would regress that design.
- The old patch covers `_run_agent()` only. It misses `/v1/runs`, which has its own cancellation/exception/structured-failure/cooperative-stop branches.
- `/v1/runs` can return structured `{failed: true}` without raising — exception-only cleanup misses it.
- Blindly calling `agent.close()` after every successful API turn may end a session intended for continuity.

**Recommended ADAPT path:**
1. Implement an async, per-profile failure finalizer using `_ensure_session_db_async()` and offloaded `get_session/end_session` calls.
2. Cover `_run_agent()`: cancellation, exceptions, structured-failure returns.
3. Cover `/v1/runs`: cancellation, exceptions, structured failures, cooperative stops.
4. Use explicit end reasons and first-reason-wins semantics.
5. Add focused tests using a real temporary `SessionDB` that read the row back after every terminal path.
6. Add a negative test proving successful resumable API turns are NOT prematurely ended.

**Status:** Awaiting scoped engineering task. **Not** in scope for the update ritual.

## L2. Verifier does not self-run the 4-detector suite

**Affected file:** `verify_update.py`
**Severity:** Low (coverage gap, not a regression)

The wrapper's step 3d runs the 4 local-patch detectors and reports results inline. The standalone `verify_update.py` does not re-run them. Consequence: a future investigator reading only the verifier evidence will not see the detector pass/fail state — they have to look at the wrapper output or run the detectors manually.

**Recommended fix:** Add a 21st section to `verify_update.py` that runs `~/.hermes/scripts/detect_all_local_patches.py` and asserts the expected PASS/ADAPT result per detector.

## L3. MEMORY.md at 100% capacity

**Affected file:** `~/.hermes/memories/MEMORY.md`
**Severity:** Low (cascading risk for future saves)

At 8,067 / 8,000 chars, MEMORY.md is at capacity. The `memory` tool will reject new `add` operations until entries are removed or compressed.

**Recommended fix:** Run `python3 /home/openclaw/apps/hermes-agent/venv/bin/python3 /home/openclaw/.hermes/scripts/compact_memory.py` to surgically remove stale entries. The 2026-07-24 doctrine (after the constraint-blocking episode) emphasizes surgical removal of stale entries or compression of prose, not bulk deletion.

## L4. USER.md at 99% capacity

**Affected file:** `~/.hermes/memories/USER.md`
**Severity:** Low (cascading risk for future saves)

At 3,942 / 4,000 chars, USER.md is near capacity. The `memory` tool will reject new `user` operations once it hits 100%.

**Recommended fix:** Same as L3 — targeted compression of prose-heavy entries while preserving reference-heavy entries (IPs, paths, hex codes, etc. are non-negotiable).

## L5. Upstream tag drift

**Affected file:** none (informational)
**Severity:** Informational

`hermes --version` still reports `v0.19.0 (2026.7.20)` after 598 nightly commits were pulled. This is the documented fast-forward-nightly pattern: upstream did not bump `__version__` for the pulled commits. The actual success signal is the gateway becoming active, not the version string changing.

**Recommended fix:** None. Documented as expected behavior.
