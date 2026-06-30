#!/usr/bin/env bash
# One-command install for Cursor, Codex, Kilo, OpenCode, Antigravity, OpenClaw, etc.
# Usage (from your project root):
#   curl -fsSL https://raw.githubusercontent.com/dapih/cobaduluk/main/install.sh | bash
# Or:
#   bash install.sh [dest]
set -euo pipefail

DEST="${1:-tools/excel-to-json}"
REPO="https://github.com/dapih/cobaduluk.git"

if [[ ! -f "$DEST/scripts/bootstrap.py" ]]; then
    echo "-> clone $REPO -> $DEST"
  git clone --depth 1 "$REPO" "$DEST"
fi

python "$DEST/scripts/bootstrap.py"
