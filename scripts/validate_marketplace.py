"""
validate_marketplace.py - check Claude Code marketplace manifest and plugin layout.

Usage:
    python scripts/validate_marketplace.py [--root PATH]

Exit: 0 ok, 1 validation error, 2 IO/parse error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_MARKETPLACE_KEYS = ("name", "description", "plugins")
REQUIRED_PLUGIN_KEYS = ("name", "description", "version", "source")
REQUIRED_DIRS = ("commands", "skills", "scripts", "workflows", "agents")
SKILL_PATH = Path("skills/excel-to-json/SKILL.md")
DISCOVERY_MIRRORS = (
    ".agents/skills/excel-to-json",
    ".cursor/skills/excel-to-json",
    ".kilo/skills/excel-to-json",
    ".opencode/skills/excel-to-json",
)
KILO_COMMANDS = (
    ".kilo/commands/excel-to-json-run.md",
    ".kilo/commands/excel-to-json-inspect.md",
    ".kilo/commands/excel-to-json-schema.md",
    ".kilo/commands/excel-to-json-convert.md",
    ".kilo/commands/excel-to-json-validate.md",
    ".kilo/commands/excel-to-json-review.md",
)
AGENTS_WORKFLOWS = (".agents/workflows/excel-to-json-run.md",)
CURSOR_PLUGIN = Path(".cursor-plugin/plugin.json")
CURSOR_MARKETPLACE = Path(".cursor-plugin/marketplace.json")


def plugin_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(2)


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def validate_marketplace(root: Path) -> None:
    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    plugin_path = root / ".claude-plugin" / "plugin.json"

    if not marketplace_path.is_file():
        fail(f"missing {marketplace_path.relative_to(root)}")
    if not plugin_path.is_file():
        fail(f"missing {plugin_path.relative_to(root)}")

    marketplace = load_json(marketplace_path)
    plugin_manifest = load_json(plugin_path)

    for key in REQUIRED_MARKETPLACE_KEYS:
        if key not in marketplace:
            fail(f"marketplace.json missing required key: {key}")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        fail("marketplace.json plugins must be a non-empty array")

    catalog_names = set()
    for idx, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            fail(f"plugins[{idx}] must be an object")
        for key in REQUIRED_PLUGIN_KEYS:
            if key not in entry:
                fail(f"plugins[{idx}] missing required key: {key}")
        name = entry["name"]
        if name in catalog_names:
            fail(f"duplicate plugin name in marketplace: {name}")
        catalog_names.add(name)

        if entry["name"] != plugin_manifest.get("name"):
            fail(
                f"plugin.json name {plugin_manifest.get('name')!r} "
                f"!= marketplace plugin name {entry['name']!r}"
            )
        if entry["version"] != plugin_manifest.get("version"):
            fail(
                f"plugin.json version {plugin_manifest.get('version')!r} "
                f"!= marketplace plugin version {entry['version']!r}"
            )

        source = entry["source"]
        if source not in (".", "./"):
            src_path = root / source
            if not src_path.is_dir():
                fail(f"plugins[{idx}] source not found: {source}")

    for dirname in REQUIRED_DIRS:
        path = root / dirname
        if not path.is_dir():
            fail(f"missing required directory: {dirname}/")

    if not (root / SKILL_PATH).is_file():
        fail(f"missing canonical skill: {SKILL_PATH.as_posix()}")

    if not (root / CURSOR_PLUGIN).is_file():
        fail(f"missing Cursor plugin manifest: {CURSOR_PLUGIN.as_posix()}")
    if not (root / CURSOR_MARKETPLACE).is_file():
        fail(f"missing Cursor marketplace manifest: {CURSOR_MARKETPLACE.as_posix()}")
    cursor_plugin = load_json(root / CURSOR_PLUGIN)
    if cursor_plugin.get("name") != plugin_manifest.get("name"):
        fail(
            f".cursor-plugin/plugin.json name {cursor_plugin.get('name')!r} "
            f"!= plugin.json name {plugin_manifest.get('name')!r}"
        )

    canonical = (root / SKILL_PATH).resolve()
    for mirror in DISCOVERY_MIRRORS:
        mirror_skill = root / mirror / "SKILL.md"
        if not mirror_skill.is_file():
            fail(f"missing discovery mirror: {mirror}/SKILL.md (run scripts/link_skill_discovery.py)")
        try:
            if mirror_skill.resolve() != canonical:
                fail(f"discovery mirror does not point to canonical skill: {mirror}")
        except OSError as exc:
            fail(f"cannot resolve discovery mirror {mirror}: {exc}")

    for cmd in KILO_COMMANDS:
        if not (root / cmd).is_file():
            fail(f"missing Kilo command: {cmd}")
        text = (root / cmd).read_text(encoding="utf-8")
        if "resolve_plugin_root.py" not in text:
            fail(f"Kilo command must reference resolve_plugin_root.py: {cmd}")

    for wf in AGENTS_WORKFLOWS:
        if not (root / wf).is_file():
            fail(f"missing Antigravity workflow: {wf}")
        text = (root / wf).read_text(encoding="utf-8")
        if "resolve_plugin_root.py" not in text:
            fail(f"workflow must reference resolve_plugin_root.py: {wf}")

    print(f"OK: marketplace valid ({marketplace['name']}, {len(plugins)} plugin(s))")
    print(f"    plugin: {plugin_manifest['name']}@{plugin_manifest['version']}")
    print(f"    discovery mirrors: {len(DISCOVERY_MIRRORS)} linked")
    print(f"    kilo commands: {len(KILO_COMMANDS)}, agents workflows: {len(AGENTS_WORKFLOWS)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Claude Code marketplace manifest.")
    parser.add_argument(
        "--root",
        help="Plugin root (default: parent of scripts/)",
    )
    args = parser.parse_args()
    validate_marketplace(plugin_root(args.root))


if __name__ == "__main__":
    main()
