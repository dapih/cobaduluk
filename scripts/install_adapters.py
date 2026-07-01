"""
install_adapters.py - OS-aware agent adapter install for excel-to-json.

Installs skill mirrors and tool-specific entry points at the *user project root*
(not only inside the plugin clone). Used by bootstrap.py.

Usage:
    python scripts/install_adapters.py --project-root PATH --plugin-root PATH \\
        [--agents cursor,codex] [--replace-copies]

Also exposes link_directory() for plugin-internal dev mirrors (link_skill_discovery.py).
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

CANONICAL_SKILL = Path("skills/excel-to-json")
MARKER_FILE = ".excel-to-json.json"
DEFAULT_PLUGIN_REL = "excel-to-json"
LEGACY_PLUGIN_RELS = ("tools/excel-to-json",)

# skill mirror path relative to project root -> agent id
SKILL_TARGETS: dict[str, str] = {
    "cursor": ".cursor/skills/excel-to-json",
    "codex": ".agents/skills/excel-to-json",
    "opencode": ".opencode/skills/excel-to-json",
    "antigravity": ".agents/skills/excel-to-json",
    "kilo": ".kilo/skills/excel-to-json",
    "openclaw": ".agents/skills/excel-to-json",
}

ALL_AGENTS = ("cursor", "codex", "opencode", "antigravity", "kilo", "openclaw")

CURSOR_RULE_NAME = "excel-to-json.mdc"
KILO_COMMAND_GLOB = "excel-to-json-*.md"
ANTIGRAVITY_WORKFLOW = Path(".agents/workflows/excel-to-json-run.md")

CURSOR_RULE_TEMPLATE = """---
description: Excel to JSON conversion pipeline. Activate when the user wants to parse an xlsx file, convert a spreadsheet to JSON, create a JSON Schema for tabular data, or run any stage of the pipeline (inspect, schema, convert, validate, data-quality review).
alwaysApply: false
---

# excel-to-json

For Excel/xlsx -> JSON tasks, **load skill `excel-to-json`** and follow `{plugin_rel}/workflows/full-pipeline.md`.

- Skill: `{plugin_rel}/skills/excel-to-json/SKILL.md` (also at `.cursor/skills/excel-to-json/SKILL.md` after bootstrap)
- Plugin root: `python {plugin_rel}/scripts/resolve_plugin_root.py` (or `EXCEL_TO_JSON_ROOT`; Claude Code uses `${{CLAUDE_PLUGIN_ROOT}}`)
- **Never** read the full `.xlsx` or `.json` into context — only the inspect report
- All gates in the workflow are mandatory unless the user explicitly skips them
"""

KILO_JSONC_STUB = """{{
  "$schema": "https://app.kilo.ai/config.json",
  "instructions": [".kilo/rules/excel-to-json.md"],
  "skills": {{
    "paths": ["{plugin_rel}/skills", ".kilo/skills"]
  }}
}}
"""


def find_plugin_rel_in_project(project_root: Path, plugin_root: Path | None = None) -> str | None:
    """Locate plugin checkout under project by matching resolved paths (junction-safe).

    Walks only shallow directories under project_root (depth <= 3). Never rglob's
    through a junction into the full plugin tree (which is slow and fragile).
    """
    project = project_root.resolve()
    target = plugin_root.resolve() if plugin_root is not None else None
    if target is not None and target == project:
        return "."

    def walk(base: Path, prefix: list[str], depth: int) -> str | None:
        if depth > 3:
            return None
        try:
            entries = list(base.iterdir())
        except OSError:
            return None
        for child in entries:
            if not child.is_dir():
                continue
            parts = prefix + [child.name]
            rel = "/".join(parts)
            if target is not None:
                try:
                    if child.resolve() == target:
                        return rel
                except OSError:
                    pass
            elif (child / "workflows/full-pipeline.md").is_file():
                return rel
            found = walk(child, parts, depth + 1)
            if found:
                return found
        return None

    return walk(project, [], 0)


def logical_plugin_rel_from_script(
    script_file: Path,
    project_root: Path,
    plugin_root: Path | None = None,
) -> str | None:
    """Nested path e.g. excel-to-json when bootstrap lives under project."""
    found = find_plugin_rel_in_project(project_root, plugin_root)
    if found:
        return found

    project = project_root.resolve()

    argv0 = Path(sys.argv[0])
    if not argv0.is_absolute():
        argv0 = Path.cwd() / argv0
    nested = argv0.parent.parent
    try:
        if nested.resolve().is_relative_to(project):
            return nested.relative_to(project).as_posix()
    except (ValueError, OSError):
        pass

    for candidate in (argv0, script_file):
        cand_str = str(candidate).replace("\\", "/")
        proj_str = str(project).replace("\\", "/").rstrip("/")
        if not cand_str.lower().startswith(proj_str.lower() + "/"):
            continue
        remainder = cand_str[len(proj_str) + 1 :]
        parts = remainder.split("/")
        if len(parts) >= 3 and parts[-2] == "scripts" and parts[-1] == "bootstrap.py":
            return "/".join(parts[:-2])

    return None


def plugin_rel_posix(project_root: Path, plugin_root: Path) -> str:
    rel = os.path.relpath(plugin_root.resolve(), project_root.resolve())
    return Path(rel).as_posix()


def link_exists(link: Path, target: Path) -> bool:
    if not link.exists() and not link.is_symlink():
        return False
    try:
        return link.resolve() == target.resolve()
    except OSError:
        return False


def copy_tree_replace(src: Path, dest: Path, replacements: dict[str, str]) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)

    if not replacements:
        return
    for path in dest.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".mdc", ".json", ".jsonc", ".txt"}:
            text = path.read_text(encoding="utf-8")
            new = text
            for old, new_val in replacements.items():
                new = new.replace(old, new_val)
            if new != text:
                path.write_text(new, encoding="utf-8")


def link_directory(link: Path, target: Path, *, replace_copies: bool, method: str = "auto") -> str:
    """Link or copy link -> target. Returns 'link', 'copy', or 'ok'."""
    link.parent.mkdir(parents=True, exist_ok=True)
    target = target.resolve()

    if link.exists() or link.is_symlink():
        if link_exists(link, target):
            print(f"OK  {link} -> {target}")
            return "ok"
        if link.is_dir() and not link.is_symlink():
            if not replace_copies:
                raise RuntimeError(
                    f"{link} exists and is not a link to {target} "
                    f"(re-run with --replace-copies)"
                )
            shutil.rmtree(link)
        elif link.is_symlink() or link.is_file():
            link.unlink()

    use_copy = method == "copy"
    if method == "auto":
        use_copy = platform.system() == "Windows" and os.environ.get("EXCEL_TO_JSON_FORCE_COPY") == "1"

    if not use_copy:
        try:
            if os.name == "nt":
                proc = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                _ = proc
            else:
                link.symlink_to(target, target_is_directory=True)
            print(f"OK  {link} -> {target}")
            return "link"
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"WARN link failed ({exc}); copying instead", file=sys.stderr)
            use_copy = True

    if use_copy:
        copy_tree_replace(target, link, {})
        print(f"OK  {link} (copy of {target})")
        return "copy"
    return "ok"


def install_skill_mirror(
    project_root: Path,
    plugin_root: Path,
    agent: str,
    *,
    replace_copies: bool,
) -> None:
    if agent not in SKILL_TARGETS:
        raise ValueError(f"unknown agent: {agent}")
    skill_src = (plugin_root / CANONICAL_SKILL).resolve()
    if not (skill_src / "SKILL.md").is_file():
        raise RuntimeError(f"canonical skill missing: {skill_src / 'SKILL.md'}")
    link = project_root / SKILL_TARGETS[agent]
    link_directory(link, skill_src, replace_copies=replace_copies)


def install_kilo_rules_stub(project_root: Path, plugin_root: Path, plugin_rel: str | None = None) -> None:
    """Optional pointer rule if not present."""
    dest = project_root / ".kilo/rules/excel-to-json.md"
    if dest.is_file():
        print(f"OK  {dest} (exists)")
        return
    src = plugin_root / ".kilo/rules/excel-to-json.md"
    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"OK  {dest} (copied)")
        return
    rel = plugin_rel or plugin_rel_posix(project_root, plugin_root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        f"# excel-to-json\n\nLoad skill `excel-to-json` from `{rel}/skills/excel-to-json/SKILL.md`.\n",
        encoding="utf-8",
    )
    print(f"OK  {dest} (stub)")


def write_project_marker(
    project_root: Path,
    plugin_root: Path,
    agents: list[str],
    *,
    plugin_rel: str | None = None,
) -> None:
    rel = plugin_rel or plugin_rel_posix(project_root, plugin_root)
    marker = {
        "version": 1,
        "pluginRoot": rel,
        "agents": sorted(set(agents)),
    }
    path = project_root / MARKER_FILE
    path.write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    print(f"OK  {path}")


def detect_agents(project_root: Path) -> list[str]:
    detected: list[str] = []
    if (project_root / ".cursor").exists() or shutil.which("cursor"):
        detected.append("cursor")
    if shutil.which("codex") or (project_root / ".agents").exists():
        detected.extend(["codex", "antigravity", "openclaw"])
    if (project_root / ".opencode").exists():
        detected.append("opencode")
    if (project_root / ".kilo").exists() or shutil.which("kilo"):
        detected.append("kilo")
    if not detected:
        detected = ["cursor", "codex", "opencode", "kilo", "antigravity", "openclaw"]
    return list(dict.fromkeys(detected))


def parse_agents(raw: str | None, project_root: Path) -> list[str]:
    if raw is None or raw == "auto":
        return detect_agents(project_root)
    if raw == "all":
        return list(ALL_AGENTS)
    agents = [a.strip().lower() for a in raw.split(",") if a.strip()]
    unknown = set(agents) - set(ALL_AGENTS)
    if unknown:
        raise ValueError(f"unknown agent(s): {', '.join(sorted(unknown))}")
    return agents


def install_project_adapters(
    project_root: Path,
    plugin_root: Path,
    agents: list[str],
    *,
    replace_copies: bool = False,
    plugin_rel: str | None = None,
) -> None:
    project_root = project_root.resolve()
    plugin_root = plugin_root.resolve()
    system = platform.system()
    print(f"-> install adapters (OS={system}, project={project_root}, plugin={plugin_root})")
    print(f"   agents: {', '.join(agents)}")

    rel_for_paths = plugin_rel or plugin_rel_posix(project_root, plugin_root)

    # Deduplicate shared skill paths (codex / antigravity / openclaw -> .agents/skills/...)
    seen_targets: set[str] = set()
    for agent in agents:
        if agent not in SKILL_TARGETS:
            continue
        target_key = SKILL_TARGETS[agent]
        if target_key in seen_targets:
            continue
        seen_targets.add(target_key)
        install_skill_mirror(project_root, plugin_root, agent, replace_copies=replace_copies)

    for agent in agents:
        install_agent_extras_with_rel(
            agent, project_root, plugin_root, rel_for_paths, replace_copies=replace_copies
        )

    write_project_marker(project_root, plugin_root, agents, plugin_rel=rel_for_paths)


def install_agent_extras_with_rel(
    agent: str,
    project_root: Path,
    plugin_root: Path,
    plugin_rel: str,
    *,
    replace_copies: bool,
) -> None:
    if agent == "cursor":
        install_cursor_rule_with_rel(project_root, plugin_rel, replace_copies=replace_copies)
    elif agent == "kilo":
        install_kilo_commands_with_rel(project_root, plugin_root, plugin_rel, replace_copies=replace_copies)
        install_kilo_jsonc_with_rel(project_root, plugin_rel)
        install_kilo_rules_stub(project_root, plugin_root, plugin_rel)
    elif agent == "antigravity":
        install_antigravity_workflow_with_rel(
            project_root, plugin_root, plugin_rel, replace_copies=replace_copies
        )


def install_cursor_rule_with_rel(
    project_root: Path, plugin_rel: str, *, replace_copies: bool
) -> None:
    rule_path = project_root / ".cursor/rules" / CURSOR_RULE_NAME
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    content = CURSOR_RULE_TEMPLATE.format(plugin_rel=plugin_rel)
    if rule_path.is_file() and not replace_copies:
        existing = rule_path.read_text(encoding="utf-8")
        if "excel-to-json" in existing and plugin_rel in existing:
            print(f"OK  {rule_path} (unchanged)")
            return
        if "excel-to-json" in existing:
            print(f"OK  {rule_path} (exists; use --replace-copies to overwrite)")
            return
    rule_path.write_text(content, encoding="utf-8")
    print(f"OK  {rule_path}")


def plugin_rel_replacements(plugin_rel: str) -> dict[str, str]:
    """Replace default and legacy nested paths when copying command templates."""
    reps: dict[str, str] = {}
    for old in (DEFAULT_PLUGIN_REL, *LEGACY_PLUGIN_RELS):
        reps[old] = plugin_rel
        reps[old.replace("/", "\\")] = plugin_rel
    return reps


def install_kilo_commands_with_rel(
    project_root: Path,
    plugin_root: Path,
    plugin_rel: str,
    *,
    replace_copies: bool,
) -> None:
    src_dir = plugin_root / ".kilo/commands"
    dest_dir = project_root / ".kilo/commands"
    dest_dir.mkdir(parents=True, exist_ok=True)
    replacements = plugin_rel_replacements(plugin_rel)
    for src in sorted(src_dir.glob(KILO_COMMAND_GLOB)):
        dest = dest_dir / src.name
        if dest.is_file() and not replace_copies:
            print(f"OK  {dest} (exists)")
            continue
        text = src.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        dest.write_text(text, encoding="utf-8")
        print(f"OK  {dest}")


def install_kilo_jsonc_with_rel(project_root: Path, plugin_rel: str) -> None:
    path = project_root / ".kilo/kilo.jsonc"
    if path.is_file():
        print(f"OK  {path} (exists; not modified)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(KILO_JSONC_STUB.format(plugin_rel=plugin_rel), encoding="utf-8")
    print(f"OK  {path} (created stub)")


def install_antigravity_workflow_with_rel(
    project_root: Path,
    plugin_root: Path,
    plugin_rel: str,
    *,
    replace_copies: bool,
) -> None:
    src = plugin_root / ANTIGRAVITY_WORKFLOW
    dest = project_root / ANTIGRAVITY_WORKFLOW
    if not src.is_file():
        raise RuntimeError(f"missing workflow template: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and not replace_copies:
        print(f"OK  {dest} (exists)")
        return
    text = src.read_text(encoding="utf-8")
    for old, new in plugin_rel_replacements(plugin_rel).items():
        text = text.replace(old, new)
    dest.write_text(text, encoding="utf-8")
    print(f"OK  {dest}")


def install_plugin_dev_mirrors(plugin_root: Path, *, replace_copies: bool = False) -> None:
    """Skill mirrors under plugin root (junction/symlink to canonical skill).

    Git checkouts ship duplicate skill trees; replace them so validate_marketplace
    and agents see a single canonical skill path.
    """
    target = (plugin_root / CANONICAL_SKILL).resolve()
    for rel in (
        ".agents/skills/excel-to-json",
        ".cursor/skills/excel-to-json",
        ".kilo/skills/excel-to-json",
        ".opencode/skills/excel-to-json",
    ):
        link = plugin_root / rel
        force = replace_copies
        if not force and link.exists() and not link_exists(link, target):
            force = True
        link_directory(link, target, replace_copies=force)


def run_skills_cli(project_root: Path, agents: list[str]) -> None:
    if not shutil.which("npx"):
        print("WARN npx not on PATH; skipping optional skills.sh install", file=sys.stderr)
        return
    for agent in agents:
        agent_flag = "hermes-agent" if agent == "hermes" else agent
        if agent not in ALL_AGENTS:
            continue
        cmd = [
            "npx",
            "skills",
            "add",
            "dapih/cobaduluk",
            "--skill",
            "excel-to-json",
            "--agent",
            agent_flag,
            "-y",
        ]
        print(f"-> optional: {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=str(project_root))
        if proc.returncode != 0:
            print(f"WARN skills add for {agent} exited {proc.returncode}", file=sys.stderr)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Install excel-to-json agent adapters.")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--plugin-root", type=Path, required=True)
    parser.add_argument(
        "--agents",
        default="auto",
        help="Comma-separated agents, 'auto', or 'all' "
        f"({', '.join(ALL_AGENTS)})",
    )
    parser.add_argument("--replace-copies", action="store_true")
    parser.add_argument("--plugin-dev-mirrors", action="store_true")
    parser.add_argument("--with-skills-cli", action="store_true")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    plugin_root = args.plugin_root.resolve()

    try:
        agents = parse_agents(args.agents, project_root)
        install_project_adapters(
            project_root,
            plugin_root,
            agents,
            replace_copies=args.replace_copies,
        )
        if args.plugin_dev_mirrors or project_root == plugin_root:
            install_plugin_dev_mirrors(plugin_root, replace_copies=args.replace_copies)
        if args.with_skills_cli:
            run_skills_cli(project_root, agents)
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
