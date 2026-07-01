# excel-to-json

Convert one complex Excel table into validated, schema-backed JSON — with a data-quality review and standardized reports. Built for **token frugality**: deterministic Python does all row-level work; the model only analyzes structure, authors the schema, writes the parser, and reviews samples. A 3,000-row table costs about the same model tokens as a 30-row one.

## Why it's different

- **Code does the work, the model supervises.** The full table and the full JSON never enter the context window. The model reads a compact structure report and writes a small parser; Python parses every row.
- **Never drops a row.** The parser proves `rows in → entries out` on every run.
- **Schema-first.** Every conversion is backed by a JSON Schema (Draft 2020-12) and validated to zero errors.
- **Surfaces issues, doesn't silently "fix" them.** Risky cleanups (aggressive de-hyphenation, trimming conjunctions) are opt-in and reported, not applied behind your back.
- **General.** No domain logic baked in — it works on any complex table.

## Install

**Prerequisites:** Python 3.9+ · Git

| Your tool | One step |
|---|---|
| **Claude Code** | `/plugin marketplace add dapih/cobaduluk` then `/plugin install excel-to-json@cobaduluk` |
| **Cursor (marketplace)** | Install from [Cursor marketplace](https://cursor.com/marketplace) when listed (manifest in [`.cursor-plugin/`](.cursor-plugin/)) |
| **Cursor, Codex, Kilo, … (local)** | Run `install.sh` / `install.ps1` from [INSTALL.md](INSTALL.md) (interactive clone + bootstrap) |

Full guide: [INSTALL.md](INSTALL.md)

### One-command install (interactive)

From your **project root** — prompts for which agents to configure (Cursor, Kilo, Codex, …):

**macOS / Linux:** `curl -fsSL https://raw.githubusercontent.com/dapih/cobaduluk/main/install.sh | bash`

**Windows (PowerShell):** `irm https://raw.githubusercontent.com/dapih/cobaduluk/main/install.ps1 | iex`

Non-interactive: `install.ps1 -NonInteractive` or `NON_INTERACTIVE=1 bash install.sh`

### Bootstrap (local / nested install)

For any agent except Claude Code marketplace, clone the repo into your project (default `excel-to-json/`) and run bootstrap once from your **project root**:

```bash
git clone --depth 1 https://github.com/dapih/cobaduluk.git excel-to-json
python excel-to-json/scripts/bootstrap.py --interactive
```

Bootstrap installs Python deps, writes **per-agent adapters at your project root** (not inside the clone), strips duplicate skill mirrors from `excel-to-json/`, and creates `.excel-to-json.json` so `resolve_plugin_root.py` finds the plugin from any subdirectory.

| Flag | Purpose |
|---|---|
| `--interactive` | Prompt for agents and scope (default when using `install.ps1` / `install.sh`) |
| `--non-interactive` | Skip prompts; use `--agents` below |
| `--agents auto` | Detect agents from project layout / PATH (non-interactive default) |
| `--agents all` | Cursor, Codex, OpenCode, Antigravity, Kilo, OpenClaw |
| `--agents cursor,kilo` | Explicit subset (use for Kilo if VS Code extension is not on PATH) |
| `--clone --dest excel-to-json` | Shallow-clone then bootstrap in one step |
| `--replace-copies` | Overwrite existing skill copies (e.g. after `npx skills add`) |
| `--with-skills-cli` | Optional: also run `npx skills add` for skills.sh telemetry |
| `--skip-verify` | Skip `verify_install.py` (not recommended) |

**OS behavior:** Windows uses directory junctions; macOS/Linux use symlinks; copy fallback if linking fails.

| Agent | Bootstrap writes at **project root** |
|---|---|
| Cursor | `.cursor/skills/excel-to-json/`, `.cursor/rules/excel-to-json.mdc` |
| Codex / OpenClaw | `.agents/skills/excel-to-json/` |
| OpenCode | `.opencode/skills/excel-to-json/` |
| Antigravity | `.agents/skills/` + `.agents/workflows/excel-to-json-run.md` |
| Kilo | `.kilo/skills/`, `.kilo/commands/excel-to-json-*.md`, `.kilo/kilo.jsonc` stub |

**User project layout** (after bootstrap):

```
your-project/
  excel-to-json/              plugin clone (scripts, workflows, Python)
  .cursor/  .kilo/  .agents/  agent adapters (project root only)
  .opencode/                  (if selected)
  .excel-to-json.json         plugin path marker
  docs/                       job outputs
```

Agent tools do **not** read dot-folders inside `excel-to-json/` — only at project root. Kilo Code uses `.kilo/` (not `.kilocode/`).

### Plugin manifests

| Tool | Manifest folder | Role |
|---|---|---|
| Claude Code | [`.claude-plugin/`](.claude-plugin/) | Marketplace catalog + plugin metadata |
| Cursor | [`.cursor-plugin/`](.cursor-plugin/) | Same role for Cursor marketplace |

Both point at the repo root (`"source": "."`). Local bootstrap is still recommended for nested clones and multi-agent setups.

Verify after install:

```bash
python excel-to-json/scripts/verify_install.py --root excel-to-json --project-root .
python excel-to-json/scripts/smoke_test_compat.py
```

| Tool | How to run |
|---|---|
| Claude Code | `/excel-to-json:run file.xlsx` |
| Cursor / Codex / OpenCode | Ask: “Convert this Excel to JSON” (natural language; not a `/excel-to-json` slash command) |
| Kilo | `/excel-to-json-run` (select Kilo in the install prompt, or `--agents kilo`) |
| Antigravity | `/excel-to-json-run` workflow |

Job outputs go under `docs/` in your project root.

## The pipeline

```
prepare → inspect → map → schema → parse → validate → data-quality → summary
```

| Step | Tool | What it does |
|---|---|---|
| inspect | `scripts/inspect_xlsx.py` | Compact structure report: sheets, header, column profiles, samples, gaps |
| map | `structure-analyst` agent | Proposes column→field mapping + hierarchy (you confirm) |
| schema | `schema-designer` agent | Authors/refines the Draft 2020-12 schema |
| parse | `parser-builder` agent | Writes `<job>.parser.py` (imports `parser_lib`), iterates to 0 errors |
| validate | `scripts/validate_json.py` | Schema validation gate |
| review | `dq-reviewer` agent | Runs `scripts/dq_check.py`, writes the data-quality report |

## Commands

| Command                              | Purpose                                                                    |                       |
| --------------------------------------| ----------------------------------------------------------------------------| -----------------------|
| `/excel-to-json:run <file.xlsx>`     | Full pipeline (pauses at confirmation gates; `--autonomous` to skip)       |                       |
| `/excel-to-json:new-job <file.xlsx>` | Create the `docs/<job>/` folder and move the input in                      |                       |
| `/excel-to-json:inspect <file\       | job>`                                                                      | Structure report only |
| `/excel-to-json:schema <job>`        | Create / refine / validate a schema (`--from-instance`, `--validate-only`) |                       |
| `/excel-to-json:convert <job>`       | Generate the parser and the JSON instance                                  |                       |
| `/excel-to-json:validate <job>`      | Validate instance vs schema                                                |                       |
| `/excel-to-json:review <job>`        | Data-quality review + report                                               |                       |
| `/excel-to-json:promote <job> [family]` | Promote a clean job to a reusable family (structural match → reuse)      |                       |

Each step is independently runnable — do the whole pipeline or just the part you need (e.g. "make a schema for this existing JSON" → `schema <job> --from-instance`).

## Reuse across same-family tables

Tables that share a structure don't have to be converted from scratch. After inspecting a new table, the pipeline fingerprints it **structurally — not by header text** and matches it against families you've promoted from past jobs:

- **near-duplicate** → offer to clone the family's schema + parser, re-pointing columns;
- **same family** → warm-start the schema from the family canonical, then adapt;
- **no match** → convert from scratch.

Reuse is opt-in (you confirm) and never skips the gates — the parser still proves row conservation and the instance still validates. Promote a finished job with `/excel-to-json:promote <job> [family]`; the store lives in `families/` at your project root. As a family grows, its match key becomes the **centroid** of its members, a **conformance** diff shows how a new table differs from the canonical, and the canonical is **versioned** (`--evolve` to adopt a new standard; members record what they were built against). See [design/reuse.md](design/reuse.md).

## Job folder (in your project root)

```
docs/table-YYYYMMDD-HHMM<am|pm>/
  <job>.xlsx  <job>.inspect.md/.json  <job>.schema.json  <job>.json  <job>.parser.py
  <job>.dq.md/.json
  log-<job>.md  data-quality-<job>.md  summary-<job>.md
```
One table per job. Multiple sheets/tables → multiple jobs.

## Layout (plugin repository)

Paths below are inside the **cobaduluk** checkout (`excel-to-json/` when nested in your project). After bootstrap, agent adapters also appear at **your project root** — see [Install](#install).

```
.claude-plugin/                 Claude Code marketplace (plugin.json + marketplace.json)
.cursor-plugin/                 Cursor marketplace (same layout)
.agents/skills/                 skill mirror (dev checkout; stripped from nested clone)
.agents/workflows/              Antigravity workflow templates
.cursor/skills/                 skill mirror (dev checkout)
.kilo/commands/                 Kilo slash command templates
commands/                       Claude Code slash commands
agents/                         structure-analyst, schema-designer, parser-builder, dq-reviewer
skills/excel-to-json/           canonical SKILL.md + references/
scripts/                        pipeline + bootstrap.py, install_adapters.py, verify_install.py
templates/                      log, data-quality, summary, schema-summary
rules/                          default normalization + DQ configs
workflows/full-pipeline.md      canonical step order
design/                         reuse, roadmap, cross-tool-compat
memory/learnings.md             cross-job learnings
families/                       promoted family canonicals
INSTALL.md                      install guide (start here)
CONTRIBUTING.md                 developer / agent maintainer guide
```

At **user project root** after bootstrap: `excel-to-json/`, `.excel-to-json.json`, `.cursor/`, `.kilo/`, `.agents/`, `.opencode/` (as selected), and `docs/` for job output.

## Scripts (also usable standalone)

```
python scripts/inspect_xlsx.py   <file.xlsx> [--sheet NAME] [--out PREFIX]
python scripts/validate_json.py  <schema.json> <instance.json> [--counts]
python scripts/dq_check.py       <instance.json> [--rules rules.json] [--out PREFIX]
python scripts/fingerprint.py    <job.inspect.json> [--out PREFIX]
python scripts/match_profile.py  <job.inspect.json> [--families DIR] [--top N]
python scripts/promote_family.py <job-id> --name <family> [--force] [--evolve]
python scripts/conformance.py    <job.inspect.json> --name <family> [--job-schema PATH]
python scripts/learnings.py      --tags structure,tooling   # or: --lint --entry '...'
```

## Notes

- `parser_lib.dehyphenate(..., merge_no_space=True)` repairs intra-word line-break hyphens (`pe-nangkap`→`penangkap`) while `protect_reduplication=True` keeps reduplications (`undang-undang`) intact — useful for Indonesian/Malay and other reduplicating languages.
- For many independent tables, run separate jobs in parallel (e.g. via your agent swarm). Within a single table, parsing is deterministic and needs no parallelism.

## License

MIT — see [LICENSE](LICENSE).
