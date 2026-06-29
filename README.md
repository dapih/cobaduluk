# excel-to-json

Convert one complex Excel table into validated, schema-backed JSON — with a data-quality review and standardized reports. Built for **token frugality**: deterministic Python does all row-level work; the model only analyzes structure, authors the schema, writes the parser, and reviews samples. A 3,000-row table costs about the same model tokens as a 30-row one.

## Why it's different

- **Code does the work, the model supervises.** The full table and the full JSON never enter the context window. The model reads a compact structure report and writes a small parser; Python parses every row.
- **Never drops a row.** The parser proves `rows in → entries out` on every run.
- **Schema-first.** Every conversion is backed by a JSON Schema (Draft 2020-12) and validated to zero errors.
- **Surfaces issues, doesn't silently "fix" them.** Risky cleanups (aggressive de-hyphenation, trimming conjunctions) are opt-in and reported, not applied behind your back.
- **General.** No domain logic baked in — it works on any complex table.

## Prerequisites

- Python 3.9+ on PATH
- `pip install openpyxl jsonschema`

## Install

The plugin root is this folder (the one containing `workflows/full-pipeline.md`). Place it wherever your AI tool can reach it, then follow the per-tool setup below.

**Prerequisites:** Python 3.9+ · `pip install openpyxl jsonschema`

### Claude Code

**Option A — global** (available in all projects): copy the whole folder into the Claude plugins cache and enable it:
```
~/.claude/plugins/cache/local/excel-to-json/0.1.0/
```
Add to `~/.claude/settings.json`: `"enabledPlugins": { "excel-to-json@local": true }`

**Option B — project-level**: copy into `my-project/.claude/plugins/excel-to-json/` and add the same `enabledPlugins` entry to `my-project/.claude/settings.json`.

> If the paths above don't work, open the plugin folder itself as your working directory — Claude Code auto-loads from CWD. Commands appear as `/excel-to-json:<command>`; assets resolve via `${CLAUDE_PLUGIN_ROOT}`.

### Cursor

Copy or clone this folder anywhere inside your project. Cursor reads `.cursor/rules/excel-to-json.mdc` (already included) automatically when you reference Excel/JSON conversion. No further configuration needed.

### Kilo Code

Copy or clone this folder inside your project. Kilo Code reads `.kilocode/rules/excel-to-json.md` (already included). Enable it in Kilo Code's rules panel if required.

### Codex CLI · Opencode · Antigravity CLI

These tools read `AGENTS.md` from the project root. Point them at this folder as the working directory (or copy `AGENTS.md` into your project root). The full pipeline context and constraints are already in `AGENTS.md`.

---

For all non-Claude-Code tools, scripts resolve to `<git rev-parse --show-toplevel>/scripts/`. Job outputs always go into `docs/` in the working directory.

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

## Layout

```
.claude-plugin/plugin.json      manifest
commands/                       8 entry-point commands
agents/                         structure-analyst, schema-designer, parser-builder, dq-reviewer
skills/excel-to-json/           SKILL.md + references/ (patterns, schema, normalization, DQ, conventions, examples)
scripts/                        inspect_xlsx, validate_json, dq_check, parser_lib, fingerprint, match_profile, promote_family, conformance, learnings
templates/                      log, data-quality, summary, schema-summary report templates
rules/                          default normalization + DQ-check configs (tunable per job)
workflows/full-pipeline.md      canonical step order
design/reuse.md                 same-family reuse design (fingerprint, families, tiers)
memory/learnings.md             cross-job, domain-agnostic learnings
families/                       promoted family canonicals (created by /promote)
```

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
