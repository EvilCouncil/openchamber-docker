# Agent Instructions

`openchamber-docker` builds and publishes `ghcr.io/evilcouncil/openchamber-docker`, running **OpenChamber** (`@openchamber/web`) on port `3000` connected to the shared `opencode` server in `EvilCouncil/local_ai_stack`.

## Key Files

| File | Purpose |
|------|---------|
| `Dockerfile` | 4-stage build (`node:24-slim` + `oven/bun:1.4-debian` + `@openchamber/web` + `opencode` CLI) |
| `docker-entrypoint.sh` | Bootstraps SSH keys, normalizes env vars, execs `openchamber serve --foreground` |
| `VERSION` | Pinned `@openchamber/web` version (mirrors `OPENCHAMBER_VERSION`) |
| `update_versions.py` | Queries npm (`@openchamber/web`, `@opencode/cli`) and updates `Dockerfile` + `VERSION` |
| `test_update_versions.py` | Unit tests for `update_versions.py` |
| `check_build.py` | Verifies GHCR tag presence + GitHub Actions status |
| `.github/workflows/build.yml` | Tag-triggered (`v*`): builds `linux/amd64` image, pushes to GHCR, cuts GitHub Release |

## Commands

```bash
make build            # Build openchamber-docker:local
make test             # Run pytest on test_update_versions.py
make update-versions  # Update OPENCHAMBER_VERSION and OPENCODE_VERSION from npm
make check-build      # Check GHCR tag + CI status (TAG=v2.7.2)
```

## Patterns & Gotchas

- **Node 24 + Bun required**: `@openchamber/web` declares `engines.node >= 24.14.0` and uses `bun-pty` when `bun` is present on `PATH`. Do not downgrade the base image to `node:22-slim`.
- **Keep `opencode` binary installed**: OpenChamber's `checkOpenCodeCLI()` throws at startup if `opencode` is missing from `PATH`, even when `OPENCODE_SKIP_START=true` connects to a remote `opencode serve` instance.
- **Foreground execution**: `openchamber` daemonizes by default; `docker-entrypoint.sh` must always pass `serve --foreground` so PID 1 stays attached in Docker.
- **External OpenCode wiring**: Set `OPENCODE_SKIP_START=true`, `OPENCODE_HOST=http://opencode:4096` (origin only, no trailing slash/path), `OPENCODE_SERVER_USERNAME`, and `OPENCODE_SERVER_PASSWORD`.
- **Network UI auth**: Binding to `0.0.0.0` requires `OPENCHAMBER_UI_PASSWORD` (fallback `UI_PASSWORD`).
