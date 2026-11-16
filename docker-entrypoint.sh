#!/usr/bin/env sh
set -eu

HOME="${HOME:-/home/openchamber}"
export HOME

OPENCODE_CONFIG_DIR="${OPENCODE_CONFIG_DIR:-${HOME}/.config/opencode}"
export OPENCODE_CONFIG_DIR
mkdir -p "${OPENCODE_CONFIG_DIR}" 2>/dev/null || true

# Bootstrap SSH keypair if writable (matches upstream OpenChamber container behavior)
SSH_DIR="${HOME}/.ssh"
SSH_KEY="${SSH_DIR}/id_ed25519"
mkdir -p "${SSH_DIR}" 2>/dev/null || true
chmod 700 "${SSH_DIR}" 2>/dev/null || true
if [ ! -f "${SSH_KEY}" ] && [ -w "${SSH_DIR}" ]; then
  ssh-keygen -t ed25519 -N "" -f "${SSH_KEY}" >/dev/null 2>&1 || true
  chmod 600 "${SSH_KEY}" 2>/dev/null || true
  chmod 644 "${SSH_KEY}.pub" 2>/dev/null || true
fi

# Normalize UI password (OPENCHAMBER_UI_PASSWORD canonical, UI_PASSWORD fallback)
if [ -z "${OPENCHAMBER_UI_PASSWORD:-}" ] && [ -n "${UI_PASSWORD:-}" ]; then
  OPENCHAMBER_UI_PASSWORD="${UI_PASSWORD}"
  export OPENCHAMBER_UI_PASSWORD
fi

# Normalize OpenCode Basic Auth credentials for external `opencode serve` connections
OPENCODE_SERVER_USERNAME="${OPENCODE_SERVER_USERNAME:-opencode}"
export OPENCODE_SERVER_USERNAME
if [ -z "${OPENCODE_SERVER_PASSWORD:-}" ] && [ -n "${OPENCODE_PASSWORD:-}" ]; then
  OPENCODE_SERVER_PASSWORD="${OPENCODE_PASSWORD}"
  export OPENCODE_SERVER_PASSWORD
fi

OPENCHAMBER_HOST="${OPENCHAMBER_HOST:-0.0.0.0}"
OPENCHAMBER_PORT="${OPENCHAMBER_PORT:-3000}"
export OPENCHAMBER_HOST OPENCHAMBER_PORT

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec openchamber serve \
  --foreground \
  --host "${OPENCHAMBER_HOST}" \
  --port "${OPENCHAMBER_PORT}"
