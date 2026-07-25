# Hermes v0.19.0 Local-Patch Compatibility Audit

Date: 2026-07-23
Repository: `/home/openclaw/apps/hermes-agent`
Audited version: Hermes Agent v0.19.0 (`HEAD 8fc278207`, synchronized with `origin/main`)
Scope: three detector failures reported by `detect_all_local_patches.py` after the v0.19.0 update. This audit made no product-code or configuration changes.

## Source-of-truth declaration

Primary sources:
- Current v0.19.0 runtime code in `cli.py`, `tools/transcription_tools.py`, `gateway/platforms/api_server.py`, `run_agent.py`, and `agent/agent_init.py`.
- The actual local patches recovered from stash commit `e793791c0`.
- Current detector scripts under `~/.hermes/scripts/`.
- Current focused tests and direct executable reproductions.

Secondary sources:
- `~/.hermes/PATCHES.md` and `hermes-update-verify/references/known-local-patches-2026-07-14.md` for original intent.
- Git history and blame for upstream architectural changes.
- Live `~/.hermes/state.db` only as corroborating operational evidence; historical reaper activity is not proof of current request behavior.

Excluded:
- No speculative patch reapplication.
- No model/provider/config mutation.
- No full test suite: the audit is compatibility-scoped; focused suites and direct reproductions were used.

## Executive verdict

| Patch | Detector result | Compatibility verdict | Severity | Correct action |
|---|---:|---|---|---|
| Multiline arrow-key navigation | FAIL | **ADAPT** | Medium UX | Do not reapply the old `if buf.text: cursor_up()` block. Replace the stale detector with a behavioral wrapped-line test and design against prompt_toolkit's visual-row abstraction. |
| Forced English OpenAI STT | FAIL | **ADAPT** | High for Alex's voice workflow | Preserve the English-language policy, but implement `stt.openai.language` propagation. The current hardcode is too broad because `_transcribe_openai` is shared with DeepInfra. |
| API-server fast-close | FAIL | **ADAPT / REAL GAP** | High data hygiene | Failure cleanup is still absent. Rework it for v0.19.0's async/per-profile SessionDB architecture and cover both `_run_agent` request paths and the separate `/v1/runs` path. |

Overall verdict: **PARTIAL / DO NOT BLINDLY REAPPLY**. All three detector failures are real signals that their literal historical code is absent, but none of the three old patches is safe to paste back unchanged.

---

## Finding 1 — Multiline arrow-key patch

### Original intent

The historical detector requires:

```python
if buf.text:
    buf.cursor_up()
else:
    buf.auto_up(count=event.arg)
```

The stated bug is that prompt_toolkit uses `Document.cursor_position_row` (logical newline rows), not terminal visual-wrap rows.

### Current architecture

`cli.py:13930-13940` still binds Up/Down to `Buffer.auto_up/auto_down`, now wrapped by `_recall_without_recollapse` for upstream commit `79af472582` (paste-history recall). The upstream commit solved paste-placeholder recall; it did not solve visual wrapped-line navigation.

Current prompt_toolkit implementation was inspected live:

```python
elif self.document.cursor_position_row > 0:
    self.cursor_up(count=count)
elif not self.selection_state:
    self.history_backward(count=count)
```

### Direct reproduction

A non-empty single logical line, positioned in what would be a visual wrapped row, reports logical row 0. Instrumenting `Buffer.auto_up()` produced:

```text
logical_row 0
auto_up_calls [('history_backward', 1)]
```

This confirms the detector's underlying diagnosis: `auto_up()` chooses history because it cannot see visual wrapping.

However, the old remedy is not a complete fix. `Buffer.cursor_up()` also uses the logical `Document.get_cursor_up_position()` path. On a single logical line it cannot move to a previous visual wrap row. The old patch prevents accidental history recall, but it does not deliver the claimed visual cursor movement.

### Verdict

**ADAPT.** The bug class remains, but the old patch is semantically incomplete and now collides with `_recall_without_recollapse` behavior introduced upstream.

### Detector assessment

The detector is stale in two ways:
1. It asserts a literal code shape rather than behavior.
2. It calls `cursor_up()` on non-empty text a complete fix, although that method is still logical-line based.

A replacement detector should execute the actual key-binding path in a narrow prompt_toolkit layout and assert both:
- Up on a wrapped non-empty line does not browse history.
- Cursor position moves to the preceding visual row (or the chosen UX explicitly documents no movement).

### Recommendation and reversibility

- **SOFT:** retire the current literal detector and document it as a known compatibility gap.
- **HARD:** implement a true visual-row-aware binding, with RED tests against the real Application/Window render geometry. This changes user-facing key behavior and should be approved before code mutation.

---

## Finding 2 — Forced-English OpenAI transcription

### Original intent

Alex explicitly chose English-only production transcription on 2026-07-14 to prevent English speech being misdetected as Polish. The old patch inserted `language="en"` directly into `_transcribe_openai`.

The old documentation's claim that Polish voice notes use local faster-whisper is now stale. The live v0.19.0 configuration has one global active provider, `stt.provider: openai`, with `gpt-4o-transcribe`; there is no automatic English/Polish provider routing. Therefore an unconditional shared-backend hardcode would also force any genuinely Polish recording through OpenAI as English. This strengthens the case for explicit provider-scoped configuration rather than restoring the one-line hardcode.

### Current architecture

Current config already contains a natural policy surface:

```yaml
stt:
  provider: openai
  openai:
    model: gpt-4o-transcribe
```

The checked-in default config documents `stt.local.language` and provider-specific languages for ElevenLabs, but `stt.openai.language` is not documented in `DEFAULT_CONFIG` (`hermes_cli/config.py:2221-2247`).

More importantly:
- `_transcribe_openai` is now the shared backend for native OpenAI and OpenAI-compatible providers such as DeepInfra (`tools/transcription_tools.py:1357-1363`).
- `transcribe_audio()` reads `stt.openai.model` but discards `stt.openai.language` (`tools/transcription_tools.py:1767-1770`).
- A direct test with `stt.openai.language: en` showed `language_sent None`.
- A direct `_transcribe_openai` probe likewise sent only `model`, `file`, and `response_format`.

Thus the configuration vocabulary anticipates a provider section with `language`, but the OpenAI runtime path does not propagate it.

### Focused verification

```text
42 passed
```

from:
- `tests/tools/test_transcription.py`
- `tests/tools/test_transcription_deepinfra.py`
- `tests/tools/test_managed_media_gateways.py`

These tests establish that the current provider paths work, but they do not assert language propagation. Existing successful-transcription tests inspect output, not the complete API kwargs.

### Verdict

**ADAPT.** The English policy remains valid for Alex, but the literal global hardcode should not return. Because `_transcribe_openai` serves DeepInfra as well, hardcoding inside the shared backend silently forces English for every compatible provider and every user.

Correct design:
1. Add an optional `language` parameter to `_transcribe_openai`.
2. On native OpenAI dispatch, pass `stt.openai.language` (empty means provider auto-detect).
3. On DeepInfra dispatch, pass `stt.deepinfra.language` independently if supported.
4. Add `language: ""` to the documented OpenAI default config.
5. For this profile, set `stt.openai.language: en` only after explicit config-change approval.

### Detector assessment

Replace the hardcode detector with a behavioral contract:
- Native OpenAI sends configured `stt.openai.language`.
- Empty config omits the kwarg.
- DeepInfra does not inherit OpenAI language unless its own config requests it.
- Known-bad test: configure `language: en` and assert the fake SDK receives exactly `en`.

### Recommendation and reversibility

- **SAFE:** update the detector design and tests in an isolated implementation branch.
- **HARD:** modify runtime STT behavior and active config. This requires explicit approval because it changes externally observable transcription behavior and touches canonical config.

---

## Finding 3 — API-server fast-close

### Original intent

The old patch added `_end_api_session_on_failure` and called it when `_run_agent` raised or was cancelled. It ended only rows whose source was `api_server` and whose `ended_at` was NULL.

### Current architecture

There are now two materially different API execution paths:

1. `_run_agent()` (`api_server.py:4738-4833`) for chat/session/responses routes.
2. The separate `/v1/runs` `_run_and_close()` path (`api_server.py:5030-5230`), which constructs and runs an agent directly and never calls `_run_agent()`.

Current `_run_agent()` has only a `finally` decrement for `_inflight_agent_runs`; it has no failure close and no `agent.close()`.

Upstream commit `b17180d95` added the general `AIAgent.close()` session-finalization contract (`run_agent.py:3836-3849`), and its tests pass. But API server paths do not call `agent.close()`, so that upstream fix does not supersede the local API failure patch.

### Direct reproduction

A fake API agent whose `run_conversation()` created an `api_server` SessionDB row and raised produced:

```text
{'ended_at': None, 'end_reason': None, 'source': 'api_server'}
```

A separate probe showed `_run_agent()` never called the fake agent's `close()`:

```text
raised audit-boom
agent_close_calls 0
```

This is executable proof that a handled API exception can still leave an open row in v0.19.0.

The live database contains no currently open API rows, but 57 API rows in the last 30-day window were later closed as `orphaned_no_close`. That is corroboration that the reaper is compensating; it does not make the request-path cleanup correct.

### Why the old patch must not be pasted back unchanged

1. v0.19.0 introduced async/per-profile SessionDB initialization (`_ensure_session_db_async`) and explicitly offloads SQLite work from the aiohttp event loop. The old synchronous helper would regress that design.
2. The old patch covers `_run_agent()` only. It misses `/v1/runs`, which has its own cancellation, exception, structured-failure, and cooperative-stop branches.
3. `/v1/runs` can return structured `{failed: true}` without raising (`api_server.py:5145-5161`); exception-only cleanup misses it.
4. Blindly calling `agent.close()` after every successful API turn may end a session intended for continuity. The fix must preserve the distinction between failure terminality and successful resumable API conversation state.

### Verdict

**ADAPT / REAL GAP.** The original behavior remains required, but the implementation and detector must be redesigned around the current architecture.

Correct design should include:
- An async, per-profile failure finalizer using `_ensure_session_db_async()` and offloaded `get_session/end_session` calls.
- `_run_agent()` coverage for cancellation and exceptions.
- `/v1/runs` coverage for cancellation, exceptions, structured failures, and terminal cooperative stops.
- Explicit end reasons and first-reason-wins semantics.
- Focused tests using a real temporary `SessionDB` that read the row back after every terminal path.
- A negative test proving successful resumable API turns are not prematurely ended.

### Detector assessment

The existing detector merely searches for a method name and call count. It can pass while `/v1/runs` remains unprotected. Replace it with executable tests over all API agent-owning paths.

### Recommendation and reversibility

- **SAFE:** replace the detector specification and add RED regression tests in isolation.
- **HARD:** implement the runtime finalizer. It changes session lifecycle semantics and should proceed only with an explicit implementation approval after the tests demonstrate the current leak.

---

## Verification evidence

### Repository and runtime

- Hermes v0.19.0.
- `HEAD...origin/main = 0 0` after update.
- No unmerged files.

### Focused tests

```text
42 passed in 1.58s  # transcription/OpenAI/DeepInfra/managed gateways
12 passed in 6.69s  # AIAgent close and resource/session cleanup
10 passed in 0.83s  # CLI paste/history-adjacent behavior
4 passed            # TUI useSubmission/paste-history behavior
```

The first Python test attempt used the wrong interpreter and failed because the new `.venv` lacks pytest. Verification was rerun with the established `venv/bin/python3`, which has pytest; the passing results above are the authoritative runs.

### Known-bad controls

All three gaps were reproduced independently of the legacy string detectors:
- Arrow: `auto_up()` called `history_backward` on a visually wrapped single logical line.
- STT: configured `stt.openai.language: en` did not reach the SDK kwargs.
- API: a raised API agent run left a real temporary SessionDB row open.

These controls prove the audit is not merely repeating stale detector output.

## Cross-source consistency matrix

| Claim | Legacy docs | Current code | Direct execution | Verdict |
|---|---|---|---|---|
| Wrapped-line Up can choose history | Yes | `auto_up` still logical-row based | Reproduced | Confirmed |
| Old cursor_up guard is a full visual fix | Claimed | `cursor_up` also logical-row based | Architecture contradicts claim | Historical docs overstated |
| Alex wants English OpenAI STT | Yes | No propagation | `language_sent None` | Policy valid, implementation absent |
| API failures can leave open rows | Yes | No failure finalizer | Reproduced with temp SessionDB | Confirmed |
| General AIAgent.close supersedes API patch | Not in old docs | close contract exists | API path never calls it | False; not superseded |

## Prioritized recommendations

| Priority | Recommendation | Reversibility |
|---|---|---|
| P0 | Build RED tests and adapt API failure cleanup across `_run_agent` and `/v1/runs` | SAFE tests, HARD runtime fix |
| P1 | Make OpenAI STT language config-driven; then pin this profile to `en` with approval | HARD |
| P2 | Replace arrow literal detector with real visual-layout behavior test; design a complete visual-row fix | HARD UX change |
| P3 | Update `~/.hermes/PATCHES.md`, detector runner text, and update skill only after implementation verdicts are accepted | SOFT canonical documentation |

## Final verdict

**PARTIAL.** The update is healthy, but the compatibility layer is not. One genuine data-hygiene gap remains in API failure cleanup, one user-critical policy is not propagated in OpenAI STT, and the arrow detector protects an incomplete historical remedy rather than the actual visual behavior.

No old patch should be mechanically reapplied. The correct next phase is test-first adaptation, with API cleanup first.
