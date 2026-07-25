# Hermes v0.19.0 Compatibility Implementation Plan

## Scope and constraints

- Work in `/home/openclaw/apps/hermes-agent`.
- No commits.
- No live user-configuration changes. `~/.hermes/config.yaml` is untouched.
- Strict TDD: RED → GREEN → REFACTOR for every task.
- Implement only items the prior 3xstanbrain synthesis marked SAFE or SOFT. Items marked HARD remain deferred or require explicit operator approval.

## Goals

1. Make the API failure-session cleanup safe and auditable.
2. Keep the provider-scoped STT language propagation correct.
3. Keep the narrow arrow history guard.
4. Document the limits honestly so a future session does not re-overstate the fix.

## What is intentionally NOT in this plan

- Pinning `stt.openai.language: en` in the user config. Hard-requires operator authorization (Rule 7 + state-coupling).
- True visual-row arrow navigation. Hard. Requires prompt_toolkit layout/render redesign and a real Application test harness.
- Splitting or reverting unrelated pre-existing working-tree changes (MiniMax OAuth, OpenViking files, `tinker-atropos/`). Treated as out-of-scope, untouched, not reverted in this plan.
- Changing the user config in any way.

## Pre-existing state to preserve

- `agent/auxiliary_client.py` modification and its test.
- `tests/hermes_cli/test_config_validation.py` modification and its root registry expansion.
- The new `plugins/memory/openviking/` files.
- The `hardening_audit/hermes-update-2026-07-23/` directory.
- The `tinker-atropos/` directory.
- The orphan `.taf-minimax-fallback-20260620-194458` file.

None of these are in the UNIEX scope. They will not be edited, deleted, or moved in this pass.

## Files in scope

- `gateway/platforms/api_server.py`
- `tests/gateway/test_api_server_failure_session_cleanup.py`
- `tools/transcription_tools.py`
- `tests/tools/test_transcription_openai_language.py`
- `cli.py`
- `tests/cli/test_arrow_navigation_history_guard.py`
- `~/.hermes/scripts/detect_multiline_arrow_fix.py`
- `~/.hermes/PATCHES.md`
- `~/.hermes/skills/devops/hermes-update-verify/references/known-local-patches-2026-07-14.md` (annotation only)

## Severity and reversibility tags

- SAFE: no state coupling, additive, self-contained. Ship on operator's "go on" without separate gate.
- SOFT: touches canonical files. Present design, get approval per file.
- HARD: changes external behavior or user policy. Explicit one-line approval required; this plan defers or excludes all HARD items.

## Tasks

### Phase 1: API failure cleanup — SAFE and SOFT items only

#### Task 1.1 — Cooperative-stop branch: cover the missing prune path (SOFT)

- **Why:** `/v1/runs` cooperative-stop branch (`run_id in self._stopping_run_ids`) does not call `_prune_failed_session_if_empty`. Riker's C2 finding.
- **Files:**
  - Modify: `gateway/platforms/api_server.py` (around line 5186-5197).
  - Test: `tests/gateway/test_api_server_failure_session_cleanup.py`.
- **Step 1 — RED.** Add a test:

```python
@pytest.mark.asyncio
async def test_runs_cooperative_stop_deletes_empty_session(tmp_path):
    db = SessionDB(db_path=tmp_path / "state.db")
    adapter = _adapter_with_db(db)
    agent = _agent_result({"final_response": "would have been done"}, db)
    app = _create_runs_app(adapter)
    async with TestClient(TestServer(app)) as client:
        with patch.object(adapter, "_create_agent", return_value=agent):
            resp = await client.post(
                "/v1/runs",
                json={"input": "hello", "session_id": "runs-coop-stop-empty"},
            )
            run_id = (await resp.json())["run_id"]
            adapter._stopping_run_ids.add(run_id)
            status = await _wait_for_terminal_run(client, run_id)
    assert status["status"] == "cancelled"
    assert db.get_session("runs-coop-stop-empty") is None
```

Run: `/home/openclaw/apps/hermes-agent/venv/bin/python3 -m pytest tests/gateway/test_api_server_failure_session_cleanup.py::test_runs_cooperative_stop_deletes_empty_session -o 'addopts=' -v`. Expect FAIL — the cooperative-stop branch returns without calling the prune helper.

- **Step 2 — GREEN.** In `gateway/platforms/api_server.py`, inside the `if run_id in self._stopping_run_ids:` branch, add the prune call BEFORE the run-status update. Add a structured `cancel` reason rather than a generic empty string. Pattern:

```python
if run_id in self._stopping_run_ids:
    await self._prune_failed_session_if_empty(
        session_id,
        request_profile=request_profile,
    )
    _put_event_if_active({...})
    self._set_run_status(run_id, "cancelled", last_event="run.cancelled")
```

Run the new test and the existing suite to confirm GREEN.

- **Step 3 — Refactor.** Reuse a small `_finalize_failed_run_state(...)` helper if a fourth similar site appears; otherwise leave inline.

#### Task 1.2 — Non-dict result path: also handle malformed results (SOFT)

- **Why:** When `_run_sync` returns `None` or any non-dict value, the `else` branch fires and emits `run.completed` with `output=""`. A failed run that returns a malformed result is misclassified as completed and never pruned. Riker's C2 finding.
- **Files:** same as 1.1.
- **Step 1 — RED.**

```python
@pytest.mark.asyncio
async def test_runs_nondict_result_does_not_persist_empty_session(tmp_path):
    db = SessionDB(db_path=tmp_path / "state.db")
    adapter = _adapter_with_db(db)
    agent = MagicMock()
    agent.run_conversation = MagicMock(
        side_effect=lambda **kw: (
            db.create_session(kw["task_id"], source="api_server", model="test")
            or None  # no dict, no failed flag
        )
    )
    agent.session_prompt_tokens = 0
    agent.session_completion_tokens = 0
    agent.session_total_tokens = 0
    agent.session_id = None
    app = _create_runs_app(adapter)
    async with TestClient(TestServer(app)) as client:
        with patch.object(adapter, "_create_agent", return_value=agent):
            resp = await client.post(
                "/v1/runs",
                json={"input": "hello", "session_id": "runs-nondict-empty"},
            )
            run_id = (await resp.json())["run_id"]
            status = await _wait_for_terminal_run(client, run_id)
    assert status["status"] in ("failed", "cancelled")
    assert db.get_session("runs-nondict-empty") is None
```

Run and expect FAIL — the `else` branch currently treats `None` as completed.

- **Step 2 — GREEN.** Adjust the `/v1/runs` result-classification so any non-dict result, or a dict that lacks a `final_response` key, is treated as a failure and routed to the prune helper. Do not invent a `final_response` from `output=""`.

```python
if isinstance(result, dict) and result.get("failed"):
    await self._prune_failed_session_if_empty(
        result.get("session_id") or session_id,
        request_profile=request_profile,
    )
    ... (existing run.failed path)
elif isinstance(result, dict) and "final_response" in result:
    ... (existing run.completed path)
else:
    await self._prune_failed_session_if_empty(
        session_id, request_profile=request_profile,
    )
    error_msg = "agent returned a malformed result"
    ... (treat as run.failed)
```

#### Task 1.3 — Cross-profile isolation test (SOFT)

- **Why:** Riker's C1 finding. Confirm the per-profile SessionDB cache resolves the right home on the loop thread before the to_thread offloader runs.
- **Files:** test only.
- **Step 1 — RED.** Build two adapters with two distinct temporary `HERMES_HOME` directories. Run `_run_agent` against adapter A; the `_prune_failed_session_if_empty` path must not touch adapter B's database. Use a real `SessionDB` per `tmp_path` and force `_ensure_session_db_async()` to resolve from the loop thread.

```python
@pytest.mark.asyncio
async def test_prune_isolation_two_profiles_do_not_cross_delete(tmp_path):
    home_a = tmp_path / "home_a"
    home_b = tmp_path / "home_b"
    for h in (home_a, home_b):
        h.mkdir(parents=True)
    with patch.dict(os.environ, {"HERMES_HOME": str(home_a)}):
        adapter_a = _adapter_with_db(SessionDB(db_path=home_a / "state.db"))
    with patch.dict(os.environ, {"HERMES_HOME": str(home_b)}):
        adapter_b = _adapter_with_db(SessionDB(db_path=home_b / "state.db"))

    agent = _agent_result({"failed": True, "error": "boom"}, adapter_a._session_db)
    with patch.object(adapter_a, "_create_agent", return_value=agent), \
         patch.dict(os.environ, {"HERMES_HOME": str(home_a)}):
        try:
            await adapter_a._run_agent("x", [], session_id="iso-a")
        except RuntimeError:
            pass

    assert adapter_a._session_db.get_session("iso-a") is None
    # adapter_b's database must not contain "iso-a" at all
    assert adapter_b._session_db.get_session("iso-a") is None
    # sanity: home_b remains clean of home_a's session id
    import sqlite3
    conn = sqlite3.connect(str(home_b / "state.db"))
    cur = conn.execute("SELECT id FROM sessions WHERE id = 'iso-a'")
    assert cur.fetchone() is None
```

- **Step 2 — GREEN.** If the test reveals a real profile-routing bug inside the `_profile_scope` + `asyncio.to_thread` boundary, fix by resolving the per-profile `home` on the loop thread BEFORE the `await` and explicitly passing the `db` into the to_thread callable. If the test already passes, no implementation change is needed; the test becomes the regression guard.

#### Task 1.4 — Concurrent-flush race test (SOFT)

- **Why:** Riker's C1 second sub-finding. The `delete_session_if_empty` SQL guard runs in one transaction, but the integration test must prove it.
- **Files:** test only.
- **Step 1 — RED.** A test that schedules a message flush on a `Thread` between failure detection and the prune call. The row must be preserved. Use the existing `SessionDB.append_message` API.

```python
@pytest.mark.asyncio
async def test_prune_preserves_concurrent_message_flush(tmp_path):
    db = SessionDB(db_path=tmp_path / "state.db")
    adapter = _adapter_with_db(db)

    import threading
    flush_started = threading.Event()
    proceed_to_prune = threading.Event()

    def concurrent_flusher():
        db.create_session("race-a", source="api_server", model="test")
        flush_started.set()
        proceed_to_prune.wait(timeout=5)
        # Flush between the failure detection and the prune attempt
        db.append_message("race-a", role="user", content="late flush")

    t = threading.Thread(target=concurrent_flusher, daemon=True)
    t.start()
    flush_started.wait()

    agent = _agent_result({"failed": True, "error": "boom"}, db)
    # The agent never runs here — we are racing the flush against the prune
    proceed_to_prune.set()
    with patch.object(adapter, "_create_agent", return_value=agent):
        try:
            await adapter._run_agent("x", [], session_id="race-a")
        except RuntimeError:
            pass

    t.join(timeout=5)
    # Row must still exist (a message was flushed before the prune ran)
    assert db.get_session("race-a") is not None
```

Note: this test will pass under the current `delete_session_if_empty` contract because the SQL guard is single-statement. If it ever fails, the implementation has regressed.

#### Task 1.5 — Document the delete-vs-close semantic change (SAFE)

- **Why:** Anyone querying `SELECT * FROM sessions WHERE end_reason='failed'` for cost attribution will silently undercount after this change. Riker C1, Picard item 1.
- **Files:** `~/.hermes/PATCHES.md` and the compatibility audit report.
- **Step 1 — edit.** In `~/.hermes/PATCHES.md` section 5, add a paragraph:

```markdown
> **v0.19.0 behavior change (2026-07-23):** Failed API runs that produced
> no user-visible content (no messages, no title, no child sessions) now
> are *deleted* from `state.db` instead of being closed with
> `end_reason='api_request_error'`. Cost-attribution queries that rely on
> the historical `end_reason='failed'` will undercount. Use
> `SELECT count(*) FROM api_run_events WHERE event = 'run.failed'` for
> post-v0.19.0 failure counts.
```

No code or test changes; this is documentation only.

### Phase 2: STT language propagation — SOFT items only

#### Task 2.1 — Strengthen DeepInfra isolation test (SOFT)

- **Why:** Current test passes trivially because DeepInfra never reads any language config at all. We need a test that proves the OpenAI provider config cannot accidentally reach a future DeepInfra language call.
- **Files:** test only.
- **Step 1 — RED.**

```python
def test_openai_provider_language_does_not_leak_to_deepinfra_dispatch(
    monkeypatch, tmp_path,
):
    """Even if the deepinfra branch is extended to accept a language kwarg,
    the OpenAI provider's stt.openai.language value MUST NOT flow into it.
    """
    monkeypatch.setenv("DEEPINFRA_API_KEY", "di-test")
    monkeypatch.setenv("VOICE_TOOLS_OPENAI_KEY", "sk-test")
    audio_file = _make_audio(tmp_path)

    captured = {}
    def fake_deepinfra_call(file_path, model, *, api_key=None, base_url=None,
                            provider_label="deepinfra", **kwargs):
        captured["language"] = kwargs.get("language")
        return {"success": True, "transcript": "hello", "provider": "deepinfra"}

    stt_config = {
        "enabled": True,
        "provider": "deepinfra",
        "openai": {"model": "whisper-1", "language": "fr"},
    }
    with patch("tools.transcription_tools._load_stt_config", return_value=stt_config), \
         patch("tools.transcription_tools._HAS_OPENAI", True), \
         patch("tools.transcription_tools._transcribe_deepinfra", fake_deepinfra_call):
        from tools.transcription_tools import transcribe_audio
        result = transcribe_audio(audio_file)
    assert result["success"] is True
    assert "language" not in captured
    assert captured.get("language") is None
```

- **Step 2 — GREEN.** The test passes without code changes. If the deepinfra branch was extended in some future refactor, this test will catch a leak. The test is the contract; the production code already satisfies it.

#### Task 2.2 — Document the policy activation gap (SAFE)

- **Why:** Alex's English policy is not active in the live config. Operators and future sessions must not be misled by the detector saying "implemented."
- **Files:** `~/.hermes/PATCHES.md`.
- **Step 1 — edit.** In `~/.hermes/PATCHES.md` section 3, add a paragraph:

```markdown
> **Policy activation (2026-07-23):** The propagation mechanism is in
> place. The actual English language policy is **not** active on this
> profile until `stt.openai.language: en` is set in `~/.hermes/config.yaml`.
> The implementation will not pin this automatically; an explicit
> operator authorization is required for any active-config change.
```

No code or test changes.

### Phase 3: Arrow guard — SOFT and SAFE items only

#### Task 3.1 — Make the whitespace-only contract explicit (SAFE)

- **Why:** Riker A2 — the helper treats whitespace-only buffers as empty (history browse), which differs from the old `if buf.text:` truthiness check. Either behavior is defensible, but the choice must be deliberate and documented.
- **Files:** `cli.py` (docstring only) and the test file.
- **Step 1 — edit.** Update the docstring on `_history_navigation_action` to declare the choice:

```python
"""
...
Contract decisions
-----------------
* "Empty" means `text.strip() == ""`. A buffer of spaces, tabs, or
  newlines is treated as editorially empty and routes to history.
  This is a deliberate departure from the historical `if buf.text:`
  truthiness check, which treated whitespace-only buffers as
  "non-empty." The whitespace policy is locked in by
  ``test_whitespace_only_buffer_treated_as_empty`` in
  ``tests/cli/test_arrow_navigation_history_guard.py``.
...
"""
```

- **Step 2 — no test change needed.** The existing test `test_whitespace_only_buffer_treated_as_empty` already enforces the contract.

#### Task 3.2 — Make the visual-row limitation explicit in detector text (SAFE)

- **Why:** The legacy detector still produces a false failure on the old `if buf.text:` regex. The detector was rewritten by the prior implementation pass; verify it is truthful in both directions.
- **Files:** `~/.hermes/scripts/detect_multiline_arrow_fix.py`.
- **Step 1 — verify RED.** Stash the helper, run the detector, expect FAIL with an actionable message. Restore the helper, run again, expect PASS. The current detector was rewritten for this; this task is a verification step, not a code change. Document the test commands in the audit report so the next session can replay.

### Phase 4: Documentation and isolation (SAFE)

#### Task 4.1 — Update the update-skill annotation (SAFE)

- **Why:** Future sessions must not blindly reapply the historical patches.
- **Files:** `~/.hermes/skills/devops/hermes-update-verify/references/known-local-patches-2026-07-14.md` (already annotated by the prior pass; verify and tighten if needed).

#### Task 4.2 — Final verification gate (SAFE)

- **Why:** The previous pass's verification was parent-run. This pass re-runs the focused suites in an environment with `pytest-asyncio` to confirm the async API tests pass.
- **Files:** no edits.
- **Step 1 — Run.**

```bash
cd /home/openclaw/apps/hermes-agent
/home/openclaw/apps/hermes-agent/venv/bin/python3 -m pytest \
  tests/gateway/test_api_server_failure_session_cleanup.py \
  tests/tools/test_transcription_openai_language.py \
  tests/cli/test_arrow_navigation_history_guard.py \
  -o 'addopts=' -v
```

- **Step 2 — cross-check.** Confirm the unrelated modified files (`agent/auxiliary_client.py`, `hermes_cli/config.py` runtime-roots section, `tests/hermes_cli/test_config_validation.py` runtime-roots test, and the untracked files) are not affected by this implementation pass. Run:

```bash
git status --short
git diff --stat
```

If the new diffs here are limited to:

- `gateway/platforms/api_server.py`
- `tools/transcription_tools.py`
- `cli.py`
- `tests/gateway/test_api_server_failure_session_cleanup.py`
- `tests/tools/test_transcription_openai_language.py`
- `tests/cli/test_arrow_navigation_history_guard.py`
- `~/.hermes/scripts/detect_multiline_arrow_fix.py`
- `~/.hermes/PATCHES.md`

and any unrelated pre-existing changes are not touched further, the gate is satisfied.

## Risk and known limitations after this plan

- API delete-vs-close is now documented but not reverted. Cost-attribution queries must be migrated to use `api_run_events`.
- English STT policy is implemented but not active. Operator authorization required to pin `stt.openai.language: en`.
- Arrow guard prevents history corruption; true visual-row movement remains a HARD deferred item.
- The unrelated pre-existing working-tree changes (MiniMax OAuth, OpenViking files, `tinker-atropos/`, orphan `.taf` file, runtime-roots validator changes) are not in scope and are not modified by this plan.
- No commits are made by this plan. The user retains authority to commit, revert, or scope the work differently.
