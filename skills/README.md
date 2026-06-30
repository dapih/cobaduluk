# Skills

This repo ships one Agent Skills–compatible skill:

| Skill | Path | Install |
|---|---|---|
| **excel-to-json** | [`excel-to-json/SKILL.md`](excel-to-json/SKILL.md) | See [INSTALL.md](../INSTALL.md) |

Use `npx skills add dapih/cobaduluk --skill excel-to-json` for agent discovery directories, or install the full plugin via Claude Code marketplace (`/plugin marketplace add dapih/cobaduluk`).

The skill describes the workflow; Python scripts in `scripts/` require the **full repository** clone.

After clone on Windows (or if mirrors are missing), run:

```bash
python scripts/link_skill_discovery.py
```

This links `.agents/skills/`, `.cursor/skills/`, `.kilo/skills/`, and `.opencode/skills/` to the canonical skill.
