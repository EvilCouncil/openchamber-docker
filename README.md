# 🐳 openchamber-docker

Container image bundling **`@openchamber/web`** (Node 24 + Bun + OpenCode v2 CLI) designed to run in foreground mode against a shared **`opencode serve`** container (`OPENCODE_SKIP_START=true`, `OPENCODE_HOST=http://opencode:4096`).

📦 **Image:** `ghcr.io/evilcouncil/openchamber-docker`

## ✨ What's inside

- 🟢 Node 24 (`node:24-slim`) + Bun (`oven/bun:1.4-debian`) for `bun-pty` terminal performance
- 🏛️ `@openchamber/web` (`openchamber serve --foreground --host 0.0.0.0 --port 3000`)
- 🤖 `opencode` v2 CLI binary (required by OpenChamber's startup check and terminal tooling)
- 🔑 Automatic `~/.ssh/id_ed25519` generation on startup when writable

## 🚀 Connecting to an external `opencode serve` instance

```bash
docker run -d \
  --name openchamber \
  -p 3000:3000 \
  -e OPENCHAMBER_UI_PASSWORD=your-ui-password \
  -e OPENCODE_SKIP_START=true \
  -e OPENCODE_HOST=http://opencode:4096 \
  -e OPENCODE_SERVER_USERNAME=opencode \
  -e OPENCODE_SERVER_PASSWORD=your-opencode-password \
  -v /srv/opencode:/workspace:z \
  -v /srv/openchamber:/home/openchamber/.config/openchamber:z \
  ghcr.io/evilcouncil/openchamber-docker:latest
```

## 🔧 Dev & Release Commands

```bash
make test             # Run pytest on test_update_versions.py
make update-versions  # Query npm latest → update Dockerfile + VERSION
make build            # Build openchamber-docker:local
git tag v2.7.2 && git push origin v2.7.2
```
