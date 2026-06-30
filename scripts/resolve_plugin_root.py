"""
resolve_plugin_root.py - locate the excel-to-json plugin root for nested installs.

Resolution order:
  1. CLAUDE_PLUGIN_ROOT (Claude Code)
  2. EXCEL_TO_JSON_ROOT (explicit override)
  3. Walk upward from current working directory
  4. Walk upward from this script's location (works when invoked as
     python tools/excel-to-json/scripts/resolve_plugin_root.py)
  5. Fail with a pointer to INSTALL.md

Usage:
    python scripts/resolve_plugin_root.py
    python path/to/cobaduluk/scripts/resolve_plugin_root.py

Exit: 0 prints absolute plugin root; 1 not found; 2 misconfigured env path.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

MARKER = Path("workflows") / "full-pipeline.md"
INSTALL_HINT = "See INSTALL.md — set EXCEL_TO_JSON_ROOT or clone into tools/excel-to-json/"


def is_plugin_root(path: Path) -> bool:
    return (path / MARKER).is_file()


def walk_up(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if is_plugin_root(candidate):
            return candidate
    return None


def from_env(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    if is_plugin_root(root):
        return root
    print(
        f"ERROR: {name}={raw!r} is not a plugin root (missing {MARKER.as_posix()}).",
        file=sys.stderr,
    )
    sys.exit(2)


def resolve() -> Path:
    for env_name in ("CLAUDE_PLUGIN_ROOT", "EXCEL_TO_JSON_ROOT"):
        root = from_env(env_name)
        if root is not None:
            return root

    for start in (Path.cwd(), Path(__file__).resolve().parent):
        found = walk_up(start)
        if found is not None:
            return found

    print(
        "ERROR: excel-to-json plugin root not found.\n"
        f"  Looked for {MARKER.as_posix()} walking up from CWD and this script.\n"
        f"  {INSTALL_HINT}",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    print(str(resolve()))


if __name__ == "__main__":
    main()
