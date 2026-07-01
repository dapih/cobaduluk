# Install excel-to-json

Pick **one path** below. You need **Python 3.9+**, **Git**, and (for most agents) a **project folder** where your spreadsheets live.

---

## Which tool do you use?

### Claude Code

No clone. Install inside Claude Code:

```text
/plugin marketplace add dapih/cobaduluk
/plugin install excel-to-json@cobaduluk
```

Then run `/excel-to-json:run path/to/file.xlsx`.

---

### Cursor (marketplace plugin)

This repo includes [`.cursor-plugin/`](.cursor-plugin/) — the **official Cursor plugin manifest** (same role as `.claude-plugin/` for Claude Code). Submit or install via [Cursor marketplace](https://cursor.com/marketplace) when listed.

For local / nested use, run **bootstrap** below — it installs `.cursor/skills/` and `.cursor/rules/` at your **project root**.

---

### Cursor, Codex, Kilo, OpenCode, Antigravity, OpenClaw, Windsurf, …

**One command** from your **project root**:

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/dapih/cobaduluk/main/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/dapih/cobaduluk/main/install.ps1 | iex
```

**Or without curl:**

```bash
git clone --depth 1 https://github.com/dapih/cobaduluk.git excel-to-json
python excel-to-json/scripts/bootstrap.py
```

Bootstrap will:

1. Install Python dependencies (`openpyxl`, `jsonschema`)
2. Detect your OS (Windows junction vs macOS/Linux symlink; copy fallback)
3. Install **per-agent adapters at your project root** (not only inside `excel-to-json/`)
4. Write `.excel-to-json.json` (plugin path for `resolve_plugin_root.py`)
5. Run verification

**Choose agents explicitly (optional):**

```bash
python excel-to-json/scripts/bootstrap.py --agents cursor,kilo,antigravity
python excel-to-json/scripts/bootstrap.py --agents all
```

| Agent | What bootstrap installs at **project root** |
|---|---|
| **Cursor** | `.cursor/skills/excel-to-json/`, `.cursor/rules/excel-to-json.mdc` |
| **Codex / OpenClaw** | `.agents/skills/excel-to-json/` |
| **OpenCode** | `.opencode/skills/excel-to-json/` |
| **Antigravity** | `.agents/skills/` + `.agents/workflows/excel-to-json-run.md` |
| **Kilo** | `.kilo/skills/`, `.kilo/commands/excel-to-json-*.md`, `.kilo/kilo.jsonc` stub |

**Where outputs go:** `docs/<job-id>/` under **your project root**.

---

## Optional: skills.sh (`npx skills`)

Telemetry / skill-only copy — **not sufficient alone** (no Python scripts):

```bash
npx skills add dapih/cobaduluk --skill excel-to-json --agent cursor -y
python excel-to-json/scripts/bootstrap.py --replace-copies
```

Or during bootstrap:

```bash
python excel-to-json/scripts/bootstrap.py --with-skills-cli
```

Use **`skills`** (plural), not `npx skill`.

Listing: [skills.sh/dapih/cobaduluk/excel-to-json](https://skills.sh/dapih/cobaduluk/excel-to-json)

---

## Already cloned?

From **project root** (nested layout):

```bash
python excel-to-json/scripts/bootstrap.py
```

From plugin folder (when workspace is the repo itself):

```bash
python scripts/bootstrap.py --agents all
```

---

## Verify

```bash
python excel-to-json/scripts/verify_install.py
```

---

## Environment overrides

**Windows (PowerShell):**

```powershell
$env:EXCEL_TO_JSON_ROOT = "C:\path\to\my-project\excel-to-json"
```

**macOS / Linux:**

```bash
export EXCEL_TO_JSON_ROOT=/path/to/my-project/excel-to-json
```

Bootstrap writes `.excel-to-json.json` at project root so `resolve_plugin_root.py` finds the plugin automatically.

---

## Troubleshooting

**Skill copies instead of links (after `npx skills add`)**

```bash
python excel-to-json/scripts/bootstrap.py --replace-copies
```

**Upgrading from `tools/excel-to-json/` (older installs)**

Move the folder to project root and re-run bootstrap, or clone fresh:

```bash
git clone --depth 1 https://github.com/dapih/cobaduluk.git excel-to-json
python excel-to-json/scripts/bootstrap.py --agents all
```

Bootstrap still rewrites paths in `.kilo/commands/` from the legacy `tools/excel-to-json` layout when present.

**Junction/symlink failed on Windows**

Bootstrap falls back to copy; or set `EXCEL_TO_JSON_FORCE_COPY=1` to force copy.

**SSH clone fails (Claude Code marketplace)**

```bash
git config --global url."https://github.com/".insteadOf git@github.com:
```

---

## More

- Overview: [README.md](README.md)
- Skill reference: [skills/excel-to-json/SKILL.md](skills/excel-to-json/SKILL.md)
- Cross-tool status: [design/cross-tool-compat.md](design/cross-tool-compat.md)
