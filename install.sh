#!/usr/bin/env bash
# One-command install for Cursor, Codex, Kilo, OpenCode, Antigravity, OpenClaw, etc.
# Usage (from your project root):
#   curl -fsSL https://raw.githubusercontent.com/dapih/cobaduluk/main/install.sh | bash
# Or:
#   bash install.sh [dest]
set -euo pipefail

DEST="${1:-excel-to-json}"
REPO="https://github.com/dapih/cobaduluk.git"

if [[ ! -f "$DEST/scripts/bootstrap.py" ]]; then
    echo "-> clone $REPO -> $DEST"
  git clone --depth 1 "$REPO" "$DEST"
fi

BOOTSTRAP_ARGS=()
if [[ "${NON_INTERACTIVE:-0}" != "1" ]]; then
  BOOTSTRAP_ARGS+=(--interactive)
fi

python "$DEST/scripts/bootstrap.py" "${BOOTSTRAP_ARGS[@]}"
