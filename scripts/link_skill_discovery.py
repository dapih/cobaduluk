"""
link_skill_discovery.py - create discovery mirrors to skills/excel-to-json.

Creates directory junctions (Windows) or symlinks (Unix) so agent tools find the
canonical skill at standard paths without duplicating SKILL.md.

Usage:
    python scripts/link_skill_discovery.py [--root PATH] [--dry-run]

Mirrors created (relative to plugin root):
    .agents/skills/excel-to-json
    .cursor/skills/excel-to-json
    .kilo/skills/excel-to-json
    .opencode/skills/excel-to-json
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

MIRRORS = (
    ".agents/skills/excel-to-json",
    ".cursor/skills/excel-to-json",
    ".kilo/skills/excel-to-json",
    ".opencode/skills/excel-to-json",
)
CANONICAL = Path("skills/excel-to-json")


def plugin_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parent.parent


def link_exists(path: Path, target: Path) -> bool:
    if not path.exists():
        return False
    try:
        return path.resolve() == target.resolve()
    except OSError:
        return False


def create_link(link: Path, target: Path, dry_run: bool, replace_copies: bool) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.exists() or link.is_symlink():
        if link_exists(link, target):
            print(f"OK  {link} -> {target}")
            return
        if link.is_dir() and not link.is_symlink():
            if not replace_copies:
                raise RuntimeError(
                    f"{link} exists and is not a link to {target} "
                    f"(re-run with --replace-copies after npx skills add copied into repo)"
                )
            if dry_run:
                print(f"REMOVE copy {link}")
            else:
                shutil.rmtree(link)
        elif not dry_run:
            link.unlink()
    if dry_run:
        print(f"LINK {link} -> {target}")
        return
    if os.name == "nt":
        import subprocess

        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        link.symlink_to(target, target_is_directory=True)
    print(f"OK  {link} -> {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Link skill discovery mirrors.")
    parser.add_argument("--root", help="Plugin root (default: parent of scripts/)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--replace-copies",
        action="store_true",
        help="Remove real directories at mirror paths (e.g. after npx skills add) and recreate links",
    )
    args = parser.parse_args()

    root = plugin_root(args.root)
    target = (root / CANONICAL).resolve()
    skill_md = target / "SKILL.md"
    if not skill_md.is_file():
        print(f"ERROR: canonical skill missing: {skill_md}", file=sys.stderr)
        sys.exit(1)

    for rel in MIRRORS:
        create_link(root / rel, target, args.dry_run, args.replace_copies)


if __name__ == "__main__":
    main()
