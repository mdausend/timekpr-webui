# Contributing

Guide for developers working on the Guardian (timekpr-webui) repository.

## Repository layout

| Path | Purpose |
|------|---------|
| `server/` | Flask app, APIs, WebSocket hub, worker, tests |
| `agent/` | Rust Linux/Windows agent |
| `android-agent/` | Kotlin Android agent |
| `scripts/` | Installers and release helpers |
| `docs/` | MkDocs documentation source |

## Essential commands

Set up the development environment as described in [Local development](local-dev.md).

```bash
# Verify development toolchain
./scripts/verify-dev-environment.sh

# Server tests
source .env
cd server
TESTING=True ./.venv/bin/python -m pytest -q -n auto

# Rust agent
cargo check --manifest-path agent/Cargo.toml

# Android native library and bindings
./scripts/android-native-build.sh

# Android APK
cd android-agent && ./gradlew assembleDebug --no-daemon

# Docs
.venv-docs/bin/mkdocs build --strict
```

## Architecture conventions

- **Outbound WebSocket** at `/ws` with HMAC auth after approval
- **Blueprints** in `server/src/blueprints/` — register in `__init__.py`
- **Timezone-aware** datetimes everywhere; avoid naive UTC
- **Logging** via `logging` module, not `print`
- **Agent protocol** changes must stay backward compatible; update Rust, Android, and debug agent together

## Extending safely

1. **New API/UI** — add blueprint + template; use `url_for('bp.endpoint')` or global fallback handler
2. **Database** — update `database.py`, add Alembic migration under `server/migrations/`
3. **Background work** — add toggle in `BackgroundTaskManager` with `TIMEKPR_TASKS_*` env flag
4. **Alerts** — extend `ALLOWED_AGENT_ALERT_TYPES` and normalization in `agent_helper.py`

## Testing

Pytest fixtures live in `server/tests/conftest.py`; WebSocket tests use in-memory stubs. Run the full server suite before PRs using the project virtual environment:

```bash
cd server
TESTING=True ./.venv/bin/python -m pytest -q -n auto
```

## Documentation

Update relevant pages under `docs/` when changing user-visible behavior. Build locally:

```bash
mkdocs build --strict
```

See [Local development](local-dev.md) and [AGENTS.md](https://github.com/pantherale0/timekpr-webui/blob/master/AGENTS.md) for AI/agent contributor notes.

## Related

- [CI & releases](ci-release.md)
- [WebSocket protocol](../reference/websocket-protocol.md)
