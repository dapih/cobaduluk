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

## Do not use `npx skills add` alone

`npx skills add` copies only the skill folder. The pipeline needs Python scripts in `scripts/`. Use the install command above instead.

Optional skills.sh page: [skills.sh/dapih/cobaduluk/excel-to-json](https://skills.sh/dapih/cobaduluk/excel-to-json)
