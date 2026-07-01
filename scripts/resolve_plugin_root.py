"""
resolve_plugin_root.py - locate the excel-to-json plugin root for nested installs.

Resolution order:
  1. CLAUDE_PLUGIN_ROOT (Claude Code)
  2. EXCEL_TO_JSON_ROOT (explicit override)
  3. .excel-to-json.json pluginRoot walking up from CWD
  4. Walk upward from current working directory
  5. Walk upward from this script's location (works when invoked as
     python excel-to-json/scripts/resolve_plugin_root.py)
  6. Fail with a pointer to INSTALL.md

Usage:
    python scripts/resolve_plugin_root.py
    python path/to/cobaduluk/scripts/resolve_plugin_root.py

Exit: 0 prints absolute plugin root; 1 not found; 2 misconfigured env path.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

MARKER = Path("workflows") / "full-pipeline.md"
MARKER_FILE = ".excel-to-json.json"
INSTALL_HINT = "See INSTALL.md — run bootstrap.py or set EXCEL_TO_JSON_ROOT"


def is_plugin_root(path: Path) -> bool:
    return (path / MARKER).is_file()


def walk_up(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if is_plugin_root(candidate):
            return candidate
    return None


def from_project_marker(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        marker_path = candidate / MARKER_FILE
        if not marker_path.is_file():
            continue
        try:
            data = json.loads(marker_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rel = data.get("pluginRoot")
        if not isinstance(rel, str) or not rel.strip():
            continue
        root = (candidate / rel).resolve()
        if is_plugin_root(root):
            return root
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

    marker_root = from_project_marker(Path.cwd())
    if marker_root is not None:
        return marker_root

    for start in (Path.cwd(), Path(__file__).resolve().parent):
        found = walk_up(start)
        if found is not None:
            return found

    print(
        "ERROR: excel-to-json plugin root not found.\n"
        f"  Looked for {MARKER.as_posix()} and {MARKER_FILE} walking up from CWD.\n"
        f"  {INSTALL_HINT}",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    print(str(resolve()))


if __name__ == "__main__":
    main()
