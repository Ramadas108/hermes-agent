# Known Limitations — Hermes Update 2026-07-05

## Documented pre-existing issues (NOT caused by this update)

### 1. Lazy backend refresh warnings (15 of 22)
`hermes update` reported 15 lazy backends with "install reported success
but packages still not importable (may require Python restart)":
- `provider.bedrock`, `provider.vertex`
- `search.firecrawl`
- `stt.faster_whisper`
- `image.fal`
- `memory.hindsight`
- `platform.telegram`, `platform.discord`, `platform.slack`, `platform.matrix`, `platform.teams`
- `skill.google_workspace`
- `tool.dashboard`, `tool.vision`, `tool.computer_use`

The next `hermes update` will retry these. They keep their previously-installed
versions for this session. No data loss; no functional impact unless you
actually invoke one of these backends.

### 2. npm vulnerabilities
Transitive esbuild/vite vulnerabilities exist. Not actionable in this update
cycle. Documented upstream.

### 3. Missing optional API keys
Platforms like Telegram/Discord/Slack/Matrix/Teams are configured but not
actively used here. Their missing keys are expected.

### 4. Untracked files in load-bearing paths
The 3 OpenViking plugin files (`plugins/memory/openviking/{finalizer,registry,registry_invariant}.py`)
plus `tinker-atropos/` and one fallback file are untracked but the system
continues to function. This is a pre-existing condition (per the
2026-06-26 investigation session). A future session should consider committing
the OpenViking files if they are stable.

## Documented by the audit (not fixed in this session)

### 5. Verifier requires a clean shell
The verifier invokes `hermes doctor` and `hermes cron list`. These need
the `hermes` binary on PATH and the venv Python importable. Run from a
normal user shell; do not run from inside a sandbox without PATH.

### 6. H14 (systemd unit references valid paths) marked N/A
This host runs the gateway via the embedded scheduler, not a systemd unit.
The hermes-update-verification-template's H14 was written for systemd-managed
gateways and does not apply here. The replacement check is `hermes gateway
status` returning `active (running)`, which is enforced by Section 5.

## No-fix recommendations

None. The update is clean. Re-run `python3
hardening_audit/hermes-update-2026-07-05/verify_update.py` from any clean
shell to re-verify; the verifier is idempotent.