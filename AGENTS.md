## Project context

This repository is **excel-to-json** — a cross-tool pipeline that converts complex Excel tables into validated, schema-backed JSON. **Deterministic Python does all row-level work;** the model analyzes structure, authors the schema, writes the parser, and reviews samples.

## Install

See **[INSTALL.md](INSTALL.md)** (marketplace-first). Quick start:

```text
/plugin marketplace add dapih/cobaduluk
/plugin install excel-to-json@cobaduluk
```

Or: `npx skills add dapih/cobaduluk --skill excel-to-json --agent cursor -y` plus a full repo clone for scripts.

## Using this in your project

When the user asks to convert Excel to JSON (or any pipeline stage), **load skill `excel-to-json`** from `skills/excel-to-json/SKILL.md` and follow `workflows/full-pipeline.md`.

Resolve plugin root once:

```bash
PLUGIN_ROOT=$(python tools/excel-to-json/scripts/resolve_plugin_root.py)
```

Claude Code sets `${CLAUDE_PLUGIN_ROOT}`. Override: `export EXCEL_TO_JSON_ROOT=/path/to/clone`.

Job outputs go under **`docs/`** in the user's working directory, not inside the plugin folder.

**Tool surfaces:** Claude Code (`commands/`, `/excel-to-json:*`), Cursor (`.cursor/skills/`, rule pointer), Kilo (`.kilo/commands/excel-to-json-*`), Codex/OpenCode/Antigravity (`.agents/skills/`, `.agents/workflows/`). Details: [INSTALL.md](INSTALL.md).

Contributing and script-change rules: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

---

## Plugin constraints (non-negotiable)

### Never read the full table or full JSON into context

Work from `<job>.inspect.md` only. Do not read `<job>.xlsx` or `<job>.json` into the conversation.

### Mandatory gates

Skip only when the user explicitly says so:

- **Step 2c** — show family match; confirm before reuse
- **Step 4b** — `conformance.py` on same-family match
- **Step 6** — `validate_json.py` exit 0 before DQ
- **Step 9** — `learnings.py --lint` before every append

### Reuse is opt-in

Present family matches; wait for confirmation. In `--autonomous`, default to KEEP (never evolve canonical).

### Row conservation

After every parser run: `rows_in == entries_out`. Silent row drops are failures.
