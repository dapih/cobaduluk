# Install excel-to-json

Marketplace-first install from **https://github.com/dapih/cobaduluk**.

**Prerequisites:** Python 3.9+ · `pip install openpyxl jsonschema`

The pipeline needs **two things**: the skill (agent instructions) and the **full repo** (Python scripts, workflows, agents). Marketplace installs below pull or link the full package where noted.

---

## Quick pick by tool

| Tool | Add marketplace | Install |
|---|---|---|
| **Claude Code** | `/plugin marketplace add dapih/cobaduluk` | `/plugin install excel-to-json@cobaduluk` |
| **Cursor, Codex, OpenCode, Antigravity, OpenClaw, Kilo, Hermes, 60+** | — | [skills CLI](#skills-sh--npx-skills-add) + [full clone](#full-repo-nested-in-your-project) |
| **Hermes** | `hermes skills tap add dapih/cobaduluk` | `hermes skills install dapih/cobaduluk/excel-to-json` |
| **GitHub Copilot** | — | `gh skill install dapih/cobaduluk --skill excel-to-json` (gh ≥ 2.90) |
| **Manual** | — | [Full repo clone](#full-repo-nested-in-your-project) |

---

## Claude Code (plugin marketplace)

Inside a Claude Code session:

```text
/plugin marketplace add dapih/cobaduluk
/plugin install excel-to-json@cobaduluk
```

Or with a full Git URL:

```text
/plugin marketplace add https://github.com/dapih/cobaduluk.git
/plugin install excel-to-json@cobaduluk
```

**Project-level:** install into `my-project/.claude/plugins/excel-to-json/` and enable in `my-project/.claude/settings.json`:

```json
{ "enabledPlugins": { "excel-to-json@cobaduluk": true } }
```

**SSH clone fails?** Some environments default to SSH for GitHub plugins:

```bash
git config --global url."https://github.com/".insteadOf git@github.com:
```

After install, commands appear as `/excel-to-json:run`, `/excel-to-json:inspect`, etc. Scripts resolve via `${CLAUDE_PLUGIN_ROOT}`.

### Kilo Code

Load skill `excel-to-json` (via `.kilo/skills/` mirror). Slash commands in `.kilo/commands/`:

| Command | Purpose |
|---|---|
| `/excel-to-json-run` | Full pipeline |
| `/excel-to-json-inspect` | Structure report |
| `/excel-to-json-schema` | Schema authoring |
| `/excel-to-json-convert` | Parser + JSON |
| `/excel-to-json-validate` | Schema validation gate |
| `/excel-to-json-review` | Data-quality review |

Config: [`.kilo/kilo.jsonc`](.kilo/kilo.jsonc)

### Antigravity

Workflow: [`.agents/workflows/excel-to-json-run.md`](.agents/workflows/excel-to-json-run.md) — invoke `/excel-to-json-run` with path to `.xlsx`.

---

## skills.sh / npx skills add

Installs the **skill** into each agent’s discovery directory. You still need the **full repo** for Python scripts (see [Full repo](#full-repo-nested-in-your-project)).

```bash
# List skills in this repo
npx skills add dapih/cobaduluk --list

# One agent (project scope)
npx skills add dapih/cobaduluk --skill excel-to-json --agent cursor -y
npx skills add dapih/cobaduluk --skill excel-to-json --agent codex -y
npx skills add dapih/cobaduluk --skill excel-to-json --agent opencode -y
npx skills add dapih/cobaduluk --skill excel-to-json --agent antigravity -y
npx skills add dapih/cobaduluk --skill excel-to-json --agent openclaw -y
npx skills add dapih/cobaduluk --skill excel-to-json --agent kilo -y
npx skills add dapih/cobaduluk --skill excel-to-json --agent hermes-agent -y

# All detected agents
npx skills add dapih/cobaduluk --skill excel-to-json --all -y
```

**skills.sh listing:** after the repo is public, run one install yourself — telemetry adds it to [skills.sh](https://skills.sh). No separate submission form.

Browse skills via the **Skills.sh** VS Code extension (`AbelMak/skills-sh`).

---

## Hermes

```bash
hermes skills tap add dapih/cobaduluk
hermes skills install dapih/cobaduluk/excel-to-json
```

Or install a single skill file from the repo path on GitHub. Pair with a [full clone](#full-repo-nested-in-your-project) for scripts.

---

## Full repo (nested in your project)

Recommended layout when the plugin lives inside your app (not as the workspace root):

```bash
cd my-project
git clone https://github.com/dapih/cobaduluk.git tools/excel-to-json
cd tools/excel-to-json
pip install openpyxl jsonschema
python scripts/link_skill_discovery.py   # skill mirrors for Cursor/Codex/Kilo/OpenCode
```

Job outputs always go under **`my-project/docs/`** (your working directory), not inside the plugin folder.

**Plugin root resolution** (for non–Claude Code tools):

```bash
# From user project (nested clone at tools/excel-to-json):
PLUGIN_ROOT=$(python tools/excel-to-json/scripts/resolve_plugin_root.py)

# Or set explicitly:
export EXCEL_TO_JSON_ROOT=/path/to/my-project/tools/excel-to-json
```

See [`scripts/resolve_plugin_root.py`](scripts/resolve_plugin_root.py) — walks up from CWD and from the script path; Claude Code uses `CLAUDE_PLUGIN_ROOT`.

---

## Validate install

```bash
pip install -r requirements.txt
python scripts/link_skill_discovery.py   # if skill mirrors missing
python scripts/validate_marketplace.py
python scripts/verify_install.py
```

Release tag should match `.claude-plugin/plugin.json` version (currently `0.1.0`).

---

## More

- Pipeline overview: [README.md](README.md)
- Cross-tool migration status: [design/cross-tool-compat.md](design/cross-tool-compat.md)
- Skill reference: [skills/excel-to-json/SKILL.md](skills/excel-to-json/SKILL.md)
