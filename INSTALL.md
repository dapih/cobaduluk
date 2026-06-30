# Install excel-to-json

Pick **one path** below. You only need Python 3.9+ and Git.

---

## Which tool do you use?

### Claude Code → marketplace (easiest)

No clone. Everything installs in one step inside Claude Code:

```text
/plugin marketplace add dapih/cobaduluk
/plugin install excel-to-json@cobaduluk
```

Then run `/excel-to-json:run path/to/file.xlsx`.

**Project-level plugin** (optional): enable in `.claude/settings.json`:

```json
{ "enabledPlugins": { "excel-to-json@cobaduluk": true } }
```

---

### Cursor, Codex, Kilo, OpenCode, Antigravity, OpenClaw, Windsurf, …

**One command** from your **project root** (where your app or spreadsheets live):

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/dapih/cobaduluk/main/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/dapih/cobaduluk/main/install.ps1 | iex
```

**Or without curl** (same result):

```bash
git clone --depth 1 https://github.com/dapih/cobaduluk.git tools/excel-to-json
python tools/excel-to-json/scripts/bootstrap.py
```

That single flow:

1. Clones the plugin into `tools/excel-to-json/` (scripts, skill, workflows)
2. Installs Python dependencies (`openpyxl`, `jsonschema`)
3. Links the skill for your agent (`.cursor/skills/`, `.agents/skills/`, etc.)
4. Runs a verification check

**You do not need `npx skills add`** when you use this path — the clone already includes the skill.

**Then:** open the project in your agent and say something like *“Convert this Excel file to JSON”* or *“Run the excel-to-json pipeline on `data/report.xlsx`”*.

| Tool | After install |
|---|---|
| **Cursor** | Skill auto-loaded; rule at `.cursor/rules/excel-to-json.mdc` when repo is workspace root, or skill mirror under `tools/excel-to-json/.cursor/skills/` |
| **Codex / OpenCode** | Skill at `tools/excel-to-json/.agents/skills/excel-to-json/` |
| **Kilo** | `/excel-to-json-run`, `/excel-to-json-inspect`, … in `tools/excel-to-json/.kilo/commands/` |
| **Antigravity** | Workflow `tools/excel-to-json/.agents/workflows/excel-to-json-run.md` |

**Where outputs go:** `docs/<job-id>/` under **your project root**, not inside `tools/excel-to-json/`.

---

## Already cloned?

From the plugin folder:

```bash
python scripts/bootstrap.py
```

From your project root (nested layout):

```bash
python tools/excel-to-json/scripts/bootstrap.py
```

---

## Verify

```bash
python tools/excel-to-json/scripts/verify_install.py
```

Should print `OK: install verification passed`.

---

## Optional: skills.sh (`npx skills`)

Use this **only** if you want the skill text in an agent directory **without** cloning the repo.

```bash
npx skills add dapih/cobaduluk --skill excel-to-json --agent cursor -y
```

Important:

- Use **`skills`** (plural), not `npx skill` — that is a different tool.
- Skill-only install **does not include Python scripts**. Conversions will fail until you also run the [one-command install](#cursor-codex-kilo-opencode-antigravity-openclaw-windsurf-) above.
- Listing: [skills.sh/dapih/cobaduluk/excel-to-json](https://skills.sh/dapih/cobaduluk/excel-to-json)

---

## Other tools

| Tool | Install |
|---|---|
| **Hermes** | `hermes skills tap add dapih/cobaduluk` then `hermes skills install dapih/cobaduluk/excel-to-json` — pair with [full install](#cursor-codex-kilo-opencode-antigravity-openclaw-windsurf-) for scripts |
| **GitHub Copilot** | `gh skill install dapih/cobaduluk --skill excel-to-json` (gh ≥ 2.90) + [full install](#cursor-codex-kilo-opencode-antigravity-openclaw-windsurf-) for scripts |

---

## Troubleshooting

**`npx skill` error: “Expected exactly one package specifier”**  
You ran `npx skill` (singular). Use `npx skills` or skip it and use the [one-command install](#cursor-codex-kilo-opencode-antigravity-openclaw-windsurf-).

**Agent can’t find scripts**  
Plugin must live at `tools/excel-to-json/` (or set `EXCEL_TO_JSON_ROOT`):

```bash
export EXCEL_TO_JSON_ROOT=/path/to/my-project/tools/excel-to-json
```

**Skill mirrors missing after clone on Windows**

```bash
python tools/excel-to-json/scripts/link_skill_discovery.py --replace-copies
```

**SSH clone fails (Claude Code marketplace)**

```bash
git config --global url."https://github.com/".insteadOf git@github.com:
```

---

## More

- Overview: [README.md](README.md)
- Skill reference: [skills/excel-to-json/SKILL.md](skills/excel-to-json/SKILL.md)
- Cross-tool status: [design/cross-tool-compat.md](design/cross-tool-compat.md)
