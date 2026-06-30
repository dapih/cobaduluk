"""
smoke_test_compat.py - structural smoke tests for cross-tool compatibility (M6).

Automates file/discovery/resolver checks per target tool. Runtime tests inside
each agent CLI (Claude session, Cursor chat, etc.) still require manual confirmation.

Usage:
    python scripts/smoke_test_compat.py [--root PATH] [--nested]

Exit: 0 all structural checks pass, 1 failure.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

CANONICAL_SKILL = Path("skills/excel-to-json/SKILL.md")

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
        "paths": (".cursor/skills/excel-to-json/SKILL.md", ".cursor/rules/excel-to-json.mdc"),
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
        "file_must_contain": [("INSTALL.md", "hermes skills tap add")],
    },
}


def root_of(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parent.parent


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


def check_tool(root: Path, tool: str, spec: dict) -> list[str]:
    errors: list[str] = []
    canon = canonical(root)

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
        [sys.executable, str(root / "scripts" / script), *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{script} failed:\n{proc.stdout}\n{proc.stderr}")


def nested_install(root: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "my-app"
        nested = project / "tools" / "excel-to-json"
        nested.parent.mkdir(parents=True)

        # Junction/symlink whole plugin into nested path (Windows junction)
        if sys.platform == "win32":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(nested), str(root)],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            nested.symlink_to(root, target_is_directory=True)

        proc = subprocess.run(
            [sys.executable, str(nested / "scripts" / "resolve_plugin_root.py")],
            cwd=str(project),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0 or Path(proc.stdout.strip()) != root:
            raise RuntimeError(
                f"nested resolver failed from {project}: "
                f"code={proc.returncode} out={proc.stdout!r} err={proc.stderr!r}"
            )


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
        try:
            nested_install(root)
            print("OK  nested install resolver")
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            failures.append(f"nested install: {exc}")
            print(f"FAIL nested install: {exc}")

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
