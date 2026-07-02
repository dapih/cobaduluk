# Skills

Canonical skill: [`excel-to-json/SKILL.md`](excel-to-json/SKILL.md)

## Install (recommended)

From your **project root**, one command — skill + Python scripts together. You will be prompted to choose which agent tools to configure (Cursor, Kilo, Codex, …):

```bash
curl -fsSL https://raw.githubusercontent.com/dapih/cobaduluk/main/install.sh | bash
```

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/dapih/cobaduluk/main/install.ps1 | iex
```

See [INSTALL.md](../INSTALL.md) for Claude Code, non-interactive flags, and troubleshooting.

## `npx skills add` alone

`npx skills add` copies only the skill folder, `skills/excel-to-json/`. That folder is self-contained (SKILL.md, scripts, default config, templates, workflow, and cross-job learnings are all inside it), so the pipeline — inspect, schema, parse, validate, data-quality review, and learning from prior jobs — runs from a skill-only install with nothing else needed. One feature still benefits from the full clone: family reuse (`families/`) lives at the project root, not inside the skill folder, so a skill-only install starts without promotable families. The install command above sets up the full clone and is still recommended for the complete experience.

Optional skills.sh page: [skills.sh/dapih/cobaduluk/excel-to-json](https://skills.sh/dapih/cobaduluk/excel-to-json)
