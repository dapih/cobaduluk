"""
bootstrap.py - one-shot setup after clone (or clone + setup in one go).

Usage (already cloned — run from plugin root or pass --root):
    python scripts/bootstrap.py

Usage (from your project root — clone if missing, then set up):
    python tools/excel-to-json/scripts/bootstrap.py --clone --dest tools/excel-to-json

What it does:
    1. Optional shallow git clone into --dest
    2. pip install -r requirements.txt
    3. link_skill_discovery.py (Cursor/Codex/Kilo/OpenCode skill mirrors)
    4. verify_install.py

Exit: 0 success, 1 failure.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_DEST = "tools/excel-to-json"
REPO_URL = "https://github.com/dapih/cobaduluk.git"
MARKER = Path("scripts/resolve_plugin_root.py")


def plugin_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parent.parent


def is_plugin_root(path: Path) -> bool:
    return (path / MARKER).is_file()


def run_step(label: str, cmd: list[str], cwd: Path | None = None) -> None:
    print(f"-> {label}", flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {proc.returncode})")


def clone_shallow(dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not is_plugin_root(dest):
        raise RuntimeError(f"{dest} exists but is not a cobaduluk checkout")
    if is_plugin_root(dest):
        print(f"OK  already cloned at {dest}")
        return
    run_step(
        f"clone {REPO_URL} → {dest}",
        ["git", "clone", "--depth", "1", REPO_URL, str(dest)],
    )


def bootstrap(root: Path, skip_verify: bool) -> None:
    if not is_plugin_root(root):
        raise RuntimeError(f"not a plugin root (missing {MARKER}): {root}")

    req = root / "requirements.txt"
    if not req.is_file():
        raise RuntimeError(f"missing {req}")

    run_step("install Python dependencies", [sys.executable, "-m", "pip", "install", "-r", str(req)])
    run_step(
        "link skill discovery mirrors",
        [sys.executable, str(root / "scripts" / "link_skill_discovery.py"), "--root", str(root)],
    )
    if not skip_verify:
        run_step(
            "verify install",
            [sys.executable, str(root / "scripts" / "verify_install.py"), "--root", str(root)],
        )


def print_next_steps(root: Path, project_root: Path) -> None:
    rel = root
    try:
        rel = root.relative_to(project_root)
    except ValueError:
        pass
    rel_posix = rel.as_posix()
    print()
    print("Done. Next steps:")
    print(f"  1. Open your project in Cursor / Codex / Kilo / etc.")
    print(f"  2. Ask: \"Convert this Excel file to JSON\" (point at a .xlsx)")
    print(f"  3. Job outputs land in docs/ under your project root (not inside the plugin).")
    print()
    print("Plugin root (for scripts):")
    print(f"  python {rel_posix}/scripts/resolve_plugin_root.py")
    print()
    print("Claude Code users: skip clone; use /plugin marketplace add dapih/cobaduluk")
    print("  then /plugin install excel-to-json@cobaduluk")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clone (optional) and set up excel-to-json in one step.",
    )
    parser.add_argument(
        "--root",
        help="Plugin root if already cloned (default: parent of scripts/)",
    )
    parser.add_argument(
        "--dest",
        default=DEFAULT_DEST,
        help=f"Install path relative to cwd when using --clone (default: {DEFAULT_DEST})",
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="Shallow-clone the repo into --dest when not already present",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip verify_install.py (not recommended)",
    )
    args = parser.parse_args()

    project_root = Path.cwd().resolve()
    root = plugin_root(args.root) if args.root else plugin_root(None)

    if args.clone:
        dest = (project_root / args.dest).resolve()
        clone_shallow(dest)
        root = dest
    elif args.root:
        root = plugin_root(args.root)
    elif not is_plugin_root(root):
        print(
            "ERROR: run from a cloned checkout, or pass --clone --dest tools/excel-to-json",
            file=sys.stderr,
        )
        print(
            "  One-liner from your project root:\n"
            f"  git clone --depth 1 {REPO_URL} {DEFAULT_DEST} && "
            f"python {DEFAULT_DEST}/scripts/bootstrap.py",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        bootstrap(root, args.skip_verify)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print_next_steps(root, project_root)


if __name__ == "__main__":
    main()
