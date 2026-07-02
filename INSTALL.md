# Installing excel-to-json

You need **Python 3.9 or newer**, **Git**, and (for every agent except Claude Code) a **project folder** where your spreadsheets live.

## Pick your path

| If you use...                                   | Do this                                             |
|-------------------------------------------------|-----------------------------------------------------|
| **Claude Code**                                 | Two commands, no clone. See [Claude Code](#claude-code). |
| **Cursor, Codex, Kilo, OpenCode, Antigravity, others** | One install command from your project root. See [Other agents](#other-agents). |
| **Cursor marketplace (when listed)**            | Install from the Cursor marketplace. See [Cursor marketplace](#cursor-marketplace). |

## Claude Code

No clone. Run these inside Claude Code:

```text
/plugin marketplace add dapih/cobaduluk
/plugin install excel-to-json@cobaduluk
```

Then convert a file:

```text
/excel-to-json:run path/to/file.xlsx
```

## Other agents

One command from your **project root**. It prompts you for which agents to configure.

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/dapih/cobaduluk/main/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/dapih/cobaduluk/main/install.ps1 | iex
```

Prefer to see the steps? Clone and bootstrap by hand instead:

```bash
git clone --depth 1 https://github.com/dapih/cobaduluk.git excel-to-json
python excel-to-json/scripts/bootstrap.py --interactive
```

Once installed, ask your agent in plain language: "Convert this Excel to JSON." (Kilo and Antigravity also expose `/excel-to-json-run`.) Outputs land in `docs/<job-id>/` under your project root.

### What the installer does

1. Installs the Python dependencies (`openpyxl`, `jsonschema`).
2. Prompts for which agents and scope to configure (skip with `--non-interactive`).
3. Detects your OS: Windows uses directory junctions, macOS and Linux use symlinks, with a copy fallback if linking fails.
4. Writes the per-agent adapters **at your project root**, not inside the clone.
5. Removes duplicate skill mirrors that older installs left inside the clone.
6. Writes `.excel-to-json.json` at your project root so the plugin can be found from any subfolder.
7. Runs verification.

### Where each agent's files land

All adapters are written at your **project root**, never inside the `excel-to-json/` clone.

| Agent                | Files written at project root                                              |
|----------------------|----------------------------------------------------------------------------|
| Cursor               | `.cursor/skills/excel-to-json/`, `.cursor/rules/excel-to-json.mdc`         |
| Codex / OpenClaw     | `.agents/skills/excel-to-json/`                                            |
| OpenCode             | `.opencode/skills/excel-to-json/`                                          |
| Antigravity          | `.agents/skills/` plus `.agents/workflows/excel-to-json-run.md`           |
| Kilo                 | `.kilo/skills/`, `.kilo/commands/excel-to-json-*.md`, `.kilo/kilo.jsonc`  |

Agent tools read dot-folders at your project root only. Kilo Code uses `.kilo/`, not `.kilocode/`.

### Choosing agents without the prompt

```bash
# skip the menu, name the agents you want
python excel-to-json/scripts/bootstrap.py --non-interactive --agents cursor,kilo

# or configure everything
python excel-to-json/scripts/bootstrap.py --agents all
```

Select **kilo** explicitly (the VS Code extension is not detected from PATH):

```bash
python excel-to-json/scripts/bootstrap.py --agents kilo,cursor
```

## Cursor marketplace

This repo ships [`.cursor-plugin/`](.cursor-plugin/), the official Cursor plugin manifest (the same role `.claude-plugin/` plays for Claude Code). Install it from the [Cursor marketplace](https://cursor.com/marketplace) when listed. For local or nested use, run the bootstrap above instead.

## Optional: skills.sh (`npx skills`)

`npx skills add` copies only the skill folder, so it is **not enough on its own**, the pipeline needs the Python scripts. Pair it with bootstrap:

```bash
npx skills add dapih/cobaduluk --skill excel-to-json --agent cursor -y
python excel-to-json/scripts/bootstrap.py --replace-copies
```

Or let bootstrap run it for you: `python excel-to-json/scripts/bootstrap.py --with-skills-cli`. Use `skills` (plural), not `skill`. Listing: [skills.sh/dapih/cobaduluk/excel-to-json](https://skills.sh/dapih/cobaduluk/excel-to-json).

## Verify

Bootstrap runs this automatically; run it yourself any time:

```bash
python excel-to-json/scripts/verify_install.py --root excel-to-json --project-root .
```

## Environment overrides

Bootstrap writes `.excel-to-json.json` at your project root so the plugin is found automatically. To point at it explicitly:

```powershell
# Windows (PowerShell)
$env:EXCEL_TO_JSON_ROOT = "C:\path\to\my-project\excel-to-json"
```

```bash
# macOS / Linux
export EXCEL_TO_JSON_ROOT=/path/to/my-project/excel-to-json
```

## Troubleshooting

**Cursor shows the skill twice.** Older installs left mirrors inside the clone. Remove them and reload Cursor:

```powershell
Remove-Item -Recurse -Force excel-to-json\.cursor\skills -ErrorAction SilentlyContinue
python excel-to-json/scripts/bootstrap.py --interactive
```

**Kilo Code not detected after install.** Re-run with Kilo selected and confirm `.kilo/kilo.jsonc` exists at your project root, then reload VS Code:

```bash
python excel-to-json/scripts/bootstrap.py --agents kilo,cursor
```

**Skill was copied instead of linked (after `npx skills add`).**

```bash
python excel-to-json/scripts/bootstrap.py --replace-copies
```

**Upgrading from an old `tools/excel-to-json/` layout.** Move the folder to your project root and re-run bootstrap, or clone fresh:

```bash
git clone --depth 1 https://github.com/dapih/cobaduluk.git excel-to-json
python excel-to-json/scripts/bootstrap.py --agents all
```

**Junction or symlink failed on Windows.** Bootstrap falls back to copy automatically; to force it, set `EXCEL_TO_JSON_FORCE_COPY=1`.

**SSH clone fails (Claude Code marketplace).**

```bash
git config --global url."https://github.com/".insteadOf git@github.com:
```

## More

- Overview: [README.md](README.md)
- Skill reference: [skills/excel-to-json/SKILL.md](skills/excel-to-json/SKILL.md)
- Cross-tool status: [design/cross-tool-compat.md](design/cross-tool-compat.md)
