"""
install_prompt.py - interactive install prompts for bootstrap / install scripts.

Usage (via bootstrap.py --interactive only):
    prompts for agent selection and install scope (project vs global).
"""
from __future__ import annotations

import sys

from install_adapters import ALL_AGENTS

AGENT_CHOICES: list[tuple[str, str]] = [
    ("cursor", "Cursor"),
    ("codex", "Codex (OpenAI)"),
    ("kilo", "Kilo Code (VS Code extension)"),
    ("opencode", "OpenCode"),
    ("antigravity", "Antigravity"),
    ("openclaw", "OpenClaw"),
]


def _read_line(prompt: str, default: str = "") -> str:
    if default:
        text = input(f"{prompt} [{default}]: ").strip()
        return text or default
    return input(f"{prompt}: ").strip()


def prompt_agents() -> str:
    """Return agents spec for parse_agents: 'all' or comma-separated ids."""
    print()
    print("Which agent tools should receive adapters at your project root?")
    for idx, (agent_id, label) in enumerate(AGENT_CHOICES, start=1):
        print(f"  {idx}. {label} ({agent_id})")
    print("  a. All supported agents")
    print()
    print("Examples: 1,3   |   cursor,kilo   |   a   |   Enter for all")
    raw = _read_line("Your choice", "a")
    if not raw or raw.lower() in {"a", "all", "*"}:
        return "all"
    tokens = [t.strip().lower() for t in raw.replace(" ", ",").split(",") if t.strip()]
    picked: list[str] = []
    id_by_num = {str(i): aid for i, (aid, _) in enumerate(AGENT_CHOICES, start=1)}
    for token in tokens:
        if token in id_by_num:
            picked.append(id_by_num[token])
        elif token in ALL_AGENTS:
            picked.append(token)
        else:
            print(f"  WARN: unknown choice {token!r} — skipped", file=sys.stderr)
    if not picked:
        print("  No valid choices; using all agents.", file=sys.stderr)
        return "all"
    return ",".join(dict.fromkeys(picked))


def prompt_scope() -> str:
    """Return 'project' or 'global' (global not implemented yet)."""
    print()
    print("Install scope:")
    print("  1. This project only — clone excel-to-json/ here; .cursor/.kilo/… at project root")
    print("  2. All projects (user-global) — not supported yet")
    print()
    choice = _read_line("Your choice", "1")
    if choice in {"2", "global", "user", "home"}:
        print(
            "  NOTE: User-global install is not implemented yet. Using this project only.",
            file=sys.stderr,
        )
        return "project"
    return "project"


def run_interactive_setup() -> tuple[str, str]:
    """Run prompts; return (agents_spec, scope)."""
    print("=" * 60)
    print("excel-to-json — interactive setup")
    print("=" * 60)
    agents = prompt_agents()
    scope = prompt_scope()
    print()
    print(f"-> agents: {agents}")
    print(f"-> scope:  {scope} (project root adapters + excel-to-json/ clone)")
    print()
    return agents, scope
