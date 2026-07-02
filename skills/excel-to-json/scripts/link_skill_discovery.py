"""
link_skill_discovery.py - create discovery mirrors to skills/excel-to-json.

Creates directory junctions (Windows) or symlinks (Unix) so agent tools find the
canonical skill at standard paths without duplicating SKILL.md.

Usage:
    python skills/excel-to-json/scripts/link_skill_discovery.py [--root PATH] [--dry-run]

Mirrors created (relative to plugin root):
    .agents/skills/excel-to-json
    .cursor/skills/excel-to-json
    .kilo/skills/excel-to-json
    .opencode/skills/excel-to-json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_adapters import install_plugin_dev_mirrors


def plugin_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description="Link skill discovery mirrors.")
    parser.add_argument("--root", help="Plugin root (default: repo root, auto-detected)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--replace-copies",
        action="store_true",
        help="Remove real directories at mirror paths (e.g. after npx skills add) and recreate links",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN: would link plugin dev mirrors under", plugin_root(args.root))
        return

    root = plugin_root(args.root)
    skill_md = root / "skills/excel-to-json/SKILL.md"
    if not skill_md.is_file():
        print(f"ERROR: canonical skill missing: {skill_md}", file=sys.stderr)
        sys.exit(1)

    install_plugin_dev_mirrors(root, replace_copies=args.replace_copies)


if __name__ == "__main__":
    main()
