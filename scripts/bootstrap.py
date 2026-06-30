"""
bootstrap.py - one-shot setup after clone (or clone + setup in one go).

Usage (from user project root — recommended):
    python tools/excel-to-json/scripts/bootstrap.py
    python tools/excel-to-json/scripts/bootstrap.py --agents cursor,kilo

Usage (clone + setup):
    python tools/excel-to-json/scripts/bootstrap.py --clone --dest tools/excel-to-json

What it does:
    1. Optional shallow git clone into --dest
    2. pip install -r requirements.txt
    3. Per-agent adapters at project root (OS-aware links; see install_adapters.py)
    4. Plugin-internal dev mirrors when project root == plugin root
    5. verify_install.py

Exit: 0 success, 1 failure.
"""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_adapters import (
    ALL_AGENTS,
    install_plugin_dev_mirrors,
    install_project_adapters,
    logical_plugin_rel_from_script,
    parse_agents,
    plugin_rel_posix,
    run_skills_cli,
)

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
        f"clone {REPO_URL} -> {dest}",
        ["git", "clone", "--depth", "1", REPO_URL, str(dest)],
    )


def bootstrap(
    project_root: Path,
    plugin_root_path: Path,
    agents: list[str],
    *,
    plugin_rel: str | None,
    replace_copies: bool,
    skip_verify: bool,
    with_skills_cli: bool,
) -> None:
    if not is_plugin_root(plugin_root_path):
        raise RuntimeError(f"not a plugin root (missing {MARKER}): {plugin_root_path}")

    req = plugin_root_path / "requirements.txt"
    if not req.is_file():
        raise RuntimeError(f"missing {req}")

    print(f"-> environment: OS={platform.system()} Python={sys.version.split()[0]}")

    run_step(
        "install Python dependencies",
        [sys.executable, "-m", "pip", "install", "-r", str(req)],
    )

    install_project_adapters(
        project_root,
        plugin_root_path,
        agents,
        replace_copies=replace_copies,
        plugin_rel=plugin_rel,
    )

    if project_root.resolve() == plugin_root_path.resolve():
        print("-> plugin dev mirrors (repo checkout)")
        install_plugin_dev_mirrors(plugin_root_path, replace_copies=replace_copies)

    if with_skills_cli:
        print("-> optional skills.sh telemetry")
        run_skills_cli(project_root, agents)

    if not skip_verify:
        run_step(
            "verify install",
            [
                sys.executable,
                str(plugin_root_path / "scripts" / "verify_install.py"),
                "--root",
                str(plugin_root_path),
            ],
        )


def print_next_steps(
    project_root: Path,
    plugin_root_path: Path,
    agents: list[str],
    plugin_rel: str | None,
) -> None:
    rel = plugin_rel or plugin_rel_posix(project_root, plugin_root_path)
    is_windows = platform.system() == "Windows"
    print()
    print("Done. Next steps:")
    if "cursor" in agents:
        print("  Cursor: open this project folder; ask to convert an Excel file to JSON.")
        print("          Or install via Cursor marketplace (see INSTALL.md / .cursor-plugin/).")
    if "kilo" in agents:
        print("  Kilo:   /excel-to-json-run path/to/file.xlsx")
    if "antigravity" in agents:
        print("  Antigravity: run workflow excel-to-json-run with path to .xlsx")
    if any(a in agents for a in ("codex", "opencode", "openclaw")):
        print("  Codex/OpenCode/OpenClaw: ask in natural language to run the excel-to-json pipeline.")
    print()
    print("  Job outputs: docs/<job-id>/ under your project root.")
    print()
    print("Plugin root:")
    print(f"  python {rel}/scripts/resolve_plugin_root.py")
    if is_windows:
        print(f"  $env:EXCEL_TO_JSON_ROOT = '{plugin_root_path}'")
    else:
        print(f"  export EXCEL_TO_JSON_ROOT='{plugin_root_path}'")
    print()
    print("Claude Code: /plugin marketplace add dapih/cobaduluk")
    print("             /plugin install excel-to-json@cobaduluk")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clone (optional) and set up excel-to-json for your project and agents.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="User project root (default: current working directory)",
    )
    parser.add_argument(
        "--root",
        help="Plugin root if already cloned (default: parent of scripts/)",
    )
    parser.add_argument(
        "--dest",
        default=DEFAULT_DEST,
        help=f"Install path relative to project root when using --clone (default: {DEFAULT_DEST})",
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="Shallow-clone the repo into --dest when not already present",
    )
    parser.add_argument(
        "--agents",
        default="auto",
        help=f"Agents to configure: auto, all, or comma-separated ({', '.join(ALL_AGENTS)})",
    )
    parser.add_argument(
        "--replace-copies",
        action="store_true",
        help="Replace existing skill copies (e.g. after npx skills add)",
    )
    parser.add_argument(
        "--with-skills-cli",
        action="store_true",
        help="Optional: also run npx skills add for skills.sh telemetry",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip verify_install.py (not recommended)",
    )
    args = parser.parse_args()

    project_root = (args.project_root or Path.cwd()).resolve()
    plugin_root_path = plugin_root(args.root) if args.root else plugin_root(None)

    if args.clone:
        dest = (project_root / args.dest).resolve()
        clone_shallow(dest)
        plugin_root_path = dest
    elif args.root:
        plugin_root_path = plugin_root(args.root)
    elif not is_plugin_root(plugin_root_path):
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
        agents = parse_agents(args.agents, project_root)
        plugin_rel = logical_plugin_rel_from_script(
            Path(__file__), project_root, plugin_root_path
        )
        bootstrap(
            project_root,
            plugin_root_path,
            agents,
            plugin_rel=plugin_rel,
            replace_copies=args.replace_copies,
            skip_verify=args.skip_verify,
            with_skills_cli=args.with_skills_cli,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print_next_steps(project_root, plugin_root_path, agents, plugin_rel)


if __name__ == "__main__":
    main()
