"""
smoke_test_compat.py - structural smoke tests for cross-tool compatibility (M6).

Automates file/discovery/resolver checks per target tool. Runtime tests inside
each agent CLI (Claude session, Cursor chat, etc.) still require manual confirmation.

Usage:
    python skills/excel-to-json/scripts/smoke_test_compat.py [--root PATH] [--nested]

Exit: 0 all structural checks pass, 1 failure.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

CANONICAL_SKILL = Path("skills/excel-to-json/SKILL.md")
SCRIPTS = Path("skills/excel-to-json/scripts")
NESTED_PLUGIN_REL = "excel-to-json"
BOOTSTRAP_AGENTS = ("cursor", "codex", "opencode", "antigravity", "kilo", "openclaw")

TOOL_CHECKS: dict[str, dict] = {
    "claude-code": {
        "paths": (
            ".claude-plugin/marketplace.json",
            ".claude-plugin/plugin.json",
            "commands/run.md",
        ),
        "min_commands": 8,
    },
    "cursor": {
        "paths": (
            ".cursor/skills/excel-to-json/SKILL.md",
            ".cursor/rules/excel-to-json.mdc",
            ".cursor-plugin/marketplace.json",
            ".cursor-plugin/plugin.json",
        ),
        "rule_max_lines": 20,
        "rule_must_contain": "load skill",
    },
    "codex": {
        "paths": (".agents/skills/excel-to-json/SKILL.md", "AGENTS.md"),
        "file_must_contain": [("AGENTS.md", "excel-to-json")],
    },
    "opencode": {
        "paths": (".opencode/skills/excel-to-json/SKILL.md", ".agents/skills/excel-to-json/SKILL.md"),
    },
    "antigravity": {
        "paths": (
            ".agents/skills/excel-to-json/SKILL.md",
            ".agents/workflows/excel-to-json-run.md",
        ),
    },
    "openclaw": {
        "paths": ("skills/excel-to-json/SKILL.md", ".agents/skills/excel-to-json/SKILL.md"),
    },
    "kilo": {
        "paths": (
            ".kilo/skills/excel-to-json/SKILL.md",
            ".kilo/kilo.jsonc",
            ".kilo/commands/excel-to-json-run.md",
        ),
        "min_kilo_commands": 6,
    },
    "hermes": {
        "paths": ("skills/excel-to-json/SKILL.md", "INSTALL.md"),
        "file_must_contain": [("INSTALL.md", "npx skills add")],
    },
}


# Paths bootstrap.py writes at the *user project root* (--agents all).
PROJECT_BOOTSTRAP_CHECKS: dict[str, dict] = {
    "cursor": {
        "paths": (
            ".cursor/skills/excel-to-json/SKILL.md",
            ".cursor/rules/excel-to-json.mdc",
            ".cursor/agents/structure-analyst.md",
            ".cursor/agents/schema-designer.md",
            ".cursor/agents/parser-builder.md",
            ".cursor/agents/dq-reviewer.md",
        ),
        "rule_max_lines": 20,
        "rule_must_contain": "load skill",
    },
    "codex": {"paths": (".agents/skills/excel-to-json/SKILL.md",)},
    "opencode": {"paths": (".opencode/skills/excel-to-json/SKILL.md",)},
    "antigravity": {
        "paths": (
            ".agents/skills/excel-to-json/SKILL.md",
            ".agents/workflows/excel-to-json-run.md",
        ),
    },
    "openclaw": {"paths": (".agents/skills/excel-to-json/SKILL.md",)},
    "kilo": {
        "paths": (
            ".kilo/skills/excel-to-json/SKILL.md",
            ".kilo/kilo.jsonc",
            ".kilo/commands/excel-to-json-run.md",
        ),
        "min_kilo_commands": 6,
    },
}


def root_of(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parents[3]


def canonical(root: Path) -> Path:
    return (root / CANONICAL_SKILL).resolve()


def resolve_same(path: Path, target: Path) -> bool:
    if not path.is_file():
        return False
    try:
        return path.resolve() == target
    except OSError:
        return False


def read_skill_frontmatter(root: Path) -> tuple[str, str]:
    text = (root / CANONICAL_SKILL).read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise RuntimeError("SKILL.md missing YAML frontmatter")
    end = text.find("---", 3)
    if end < 0:
        raise RuntimeError("SKILL.md frontmatter not closed")
    block = text[3:end]
    name = re.search(r"^name:\s*(.+)$", block, re.M)
    desc = re.search(r"^description:\s*(.+)$", block, re.M)
    if not name or not desc:
        raise RuntimeError("SKILL.md missing name or description")
    return name.group(1).strip(), desc.group(1).strip()


def check_tool(
    root: Path,
    tool: str,
    spec: dict,
    *,
    canon_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    canon = canonical(canon_root or root)

    for rel in spec.get("paths", ()):
        p = root / rel
        if rel.endswith("SKILL.md"):
            if not resolve_same(p, canon):
                errors.append(f"{tool}: {rel} missing or not linked to canonical skill")
        elif not p.is_file():
            errors.append(f"{tool}: missing {rel}")

    if "min_commands" in spec:
        cmds = list((root / "commands").glob("*.md"))
        if len(cmds) < spec["min_commands"]:
            errors.append(f"{tool}: expected >={spec['min_commands']} commands, got {len(cmds)}")

    if "min_kilo_commands" in spec:
        cmds = list((root / ".kilo" / "commands").glob("excel-to-json-*.md"))
        if len(cmds) < spec["min_kilo_commands"]:
            errors.append(f"{tool}: expected >={spec['min_kilo_commands']} kilo commands, got {len(cmds)}")

    rule = root / ".cursor/rules/excel-to-json.mdc"
    if "rule_max_lines" in spec and rule.is_file():
        lines = rule.read_text(encoding="utf-8").splitlines()
        if len(lines) > spec["rule_max_lines"]:
            errors.append(f"{tool}: cursor rule too long ({len(lines)} lines); should be skill pointer only")
        if spec.get("rule_must_contain") and spec["rule_must_contain"] not in rule.read_text(encoding="utf-8").lower():
            errors.append(f"{tool}: cursor rule missing '{spec['rule_must_contain']}'")

    for rel, needle in spec.get("file_must_contain", ()):
        text = (root / rel).read_text(encoding="utf-8")
        if needle not in text:
            errors.append(f"{tool}: {rel} missing expected text {needle!r}")

    resolver_paths = (".kilo/commands/", ".agents/workflows/")
    for rel in spec.get("paths", ()):
        if any(rel.startswith(prefix) for prefix in resolver_paths):
            p = root / rel
            if p.is_file() and "resolve_plugin_root.py" not in p.read_text(encoding="utf-8"):
                errors.append(f"{tool}: {rel} must reference resolve_plugin_root.py")

    return errors


def run_subprocess(root: Path, script: str, *args: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(root / SCRIPTS / script), *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{script} failed:\n{proc.stdout}\n{proc.stderr}")


def link_plugin_into_project(project: Path, nested: Path, plugin_root: Path) -> None:
    """Simulate user install with a real directory copy (not junction to plugin repo)."""
    nested.parent.mkdir(parents=True, exist_ok=True)
    if nested.exists():
        import shutil
        shutil.rmtree(nested)
    import shutil
    shutil.copytree(
        plugin_root,
        nested,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "debug-*.log"),
    )


def nested_bootstrap_smoke(plugin_root: Path) -> list[str]:
    """Simulate nested install (junction/symlink) + bootstrap --agents all.

    Validates:
      - .excel-to-json.json pluginRoot is the logical nested path (not a resolved relpath)
      - per-agent adapters at the simulated project root
      - resolve_plugin_root.py from the project cwd
    """
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "my-app"
        nested = project / NESTED_PLUGIN_REL
        link_plugin_into_project(project, nested, plugin_root)

        proc = subprocess.run(
            [
                sys.executable,
                str(nested / SCRIPTS / "bootstrap.py"),
                "--agents",
                "all",
                "--skip-verify",
            ],
            cwd=str(project),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            errors.append(
                f"nested bootstrap failed (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
            )
            return errors

        marker = project / ".excel-to-json.json"
        if not marker.is_file():
            errors.append("nested bootstrap: missing .excel-to-json.json")
        else:
            try:
                data = json.loads(marker.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"nested bootstrap: invalid .excel-to-json.json: {exc}")
                data = {}
            if data.get("pluginRoot") != NESTED_PLUGIN_REL:
                errors.append(
                    f"nested bootstrap: pluginRoot={data.get('pluginRoot')!r} "
                    f"!= {NESTED_PLUGIN_REL!r}"
                )
            installed = sorted(data.get("agents") or [])
            if installed != sorted(BOOTSTRAP_AGENTS):
                errors.append(
                    f"nested bootstrap: agents={installed!r} != {sorted(BOOTSTRAP_AGENTS)!r}"
                )

        for tool, spec in PROJECT_BOOTSTRAP_CHECKS.items():
            errors.extend(check_tool(project, tool, spec, canon_root=nested))

        if (nested / ".cursor/skills").exists():
            errors.append(
                "nested bootstrap: excel-to-json/.cursor/skills should not exist "
                "(adapters belong at project root only)"
            )

        resolver = subprocess.run(
            [sys.executable, str(nested / SCRIPTS / "resolve_plugin_root.py")],
            cwd=str(project),
            capture_output=True,
            text=True,
        )
        if resolver.returncode != 0:
            errors.append(
                f"nested resolver failed: code={resolver.returncode} err={resolver.stderr!r}"
            )
        elif Path(resolver.stdout.strip()) != nested.resolve():
            errors.append(
                f"nested resolver: {resolver.stdout.strip()!r} != {nested.resolve()!r}"
            )

    return errors


def probe_cli(name: str) -> str | None:
    import shutil

    path = shutil.which(name)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-tool structural smoke tests.")
    parser.add_argument("--root", help="Plugin root")
    parser.add_argument("--nested", action="store_true", default=True)
    parser.add_argument("--no-nested", action="store_false", dest="nested")
    args = parser.parse_args()

    root = root_of(args.root)
    failures: list[str] = []

    name, _ = read_skill_frontmatter(root)
    if name != "excel-to-json":
        failures.append(f"SKILL name {name!r} != folder excel-to-json")

    print(f"OK  SKILL frontmatter name={name}")

    for tool, spec in TOOL_CHECKS.items():
        errs = check_tool(root, tool, spec)
        if errs:
            failures.extend(errs)
            print(f"FAIL {tool}")
            for e in errs:
                print(f"      {e}")
        else:
            print(f"OK  {tool} (structural)")

    try:
        run_subprocess(root, "validate_marketplace.py", "--root", str(root))
        print("OK  validate_marketplace.py")
    except RuntimeError as exc:
        failures.append(str(exc))
        print(f"FAIL validate_marketplace.py: {exc}")

    try:
        run_subprocess(root, "resolve_plugin_root.py")
        print("OK  resolve_plugin_root.py")
    except RuntimeError as exc:
        failures.append(str(exc))

    if args.nested:
        nested_errors = nested_bootstrap_smoke(root)
        if nested_errors:
            failures.extend(nested_errors)
            print("FAIL nested bootstrap")
            for e in nested_errors:
                print(f"      {e}")
        else:
            print("OK  nested bootstrap (project adapters + resolver)")

    for cli in ("hermes", "codex", "cursor", "npx"):
        found = probe_cli(cli)
        if found:
            print(f"NOTE {cli} CLI found at {found} (runtime test manual)")
        else:
            print(f"NOTE {cli} CLI not on PATH (structural only)")

    if failures:
        print(f"\nFAIL: {len(failures)} check(s)", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(1)

    print("\nOK: structural smoke tests passed (8 tools)")
    print(textwrap.dedent("""
        Manual runtime checks still recommended:
          Claude Code  /plugin marketplace add + /excel-to-json:inspect
          Cursor       natural-language trigger in Agent mode
          Codex        $excel-to-json or skill picker
          OpenCode     skill tool lists excel-to-json
          Antigravity  /excel-to-json-run
          OpenClaw     skill load
          Kilo         /excel-to-json-run
          Hermes       hermes skills tap add dapih/cobaduluk
    """).strip())


if __name__ == "__main__":
    main()
