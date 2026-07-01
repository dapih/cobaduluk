# excel-to-json

An AI agent skill that converts large, complex Excel tables into clean, validated JSON, and refines the result with a data-quality review, all while spending model tokens frugally.

The trick: your AI agent never reads the spreadsheet. It reads a compact structure report, writes a small Python parser, and lets that parser process every row. A 3,000-row table costs about the same in model tokens as a 30-row one.

Works in Claude Code, Cursor, Codex, Kilo, OpenCode, Antigravity, and other agents that support skills.

## Why it's different

- **Code does the work, the model supervises.** The full table and the full JSON never enter the context window. The model reads a compact report and writes a small parser; Python parses every row.
- **Never drops a row.** The parser proves `rows in` equals `entries out` on every run.
- **Schema-first.** Every conversion is backed by a JSON Schema (Draft 2020-12) and validated to zero errors.
- **Surfaces issues instead of silently "fixing" them.** Risky cleanups (aggressive de-hyphenation, trimming conjunctions) are opt-in and reported, never applied behind your back.
- **General.** No domain logic baked in, so it works on any complex table.

## Quickstart

**Prerequisites:** Python 3.9 or newer, and Git.

**Claude Code** (no clone needed):

```text
/plugin marketplace add dapih/cobaduluk
/plugin install excel-to-json@cobaduluk
/excel-to-json:run path/to/your-file.xlsx
```

**Any other agent** (Cursor, Codex, Kilo, OpenCode, Antigravity), run once from your project root:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/dapih/cobaduluk/main/install.sh | bash
```

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/dapih/cobaduluk/main/install.ps1 | iex
```

Then ask your agent, in plain language: "Convert this Excel to JSON." Full options, flags, and troubleshooting are in [INSTALL.md](INSTALL.md).

## Example

A complex table is rarely a neat grid. Header cells are filled only on the first row of each entry, sub-rows continue the one above, and notes carry their own numbered sub-levels:

| No | Code | Name          | Tier     | Region | Note                 |
|----|------|---------------|----------|--------|----------------------|
| 1  | 001  | Sample Widget | standard | North  | 1. Assembly required |
|    |      |               |          | South  | a. Tools included    |
|    |      |               | premium  | North  | 1. Pre-assembled     |

The pipeline turns that into hierarchical, validated JSON, grouping variants under each item and nesting the numbered notes:

```json
{
  "items": [
    {
      "id": "001",
      "name": "Sample Widget",
      "variants": [
        {
          "tier": "standard",
          "regions": ["North", "South"],
          "notes": [
            {
              "teks": "1. Assembly required",
              "sub": [{ "teks": "a. Tools included" }]
            }
          ]
        },
        { "tier": "premium", "regions": ["North"], "notes": [{ "teks": "1. Pre-assembled" }] }
      ]
    }
  ]
}
```

A runnable, synthetic schema-and-instance pair lives in [skills/excel-to-json/references/examples/](skills/excel-to-json/references/examples/).

## What it costs (real measured run)

A regulatory licensing table with **1,392 rows** converted into **94 entries, 145 risk-groups, and 243 authority-groups**, none dropped. The resulting `instance.json` was **380 kB (about 95,000 tokens)**, and **none of it ever entered the model context**.

| Metric                        | Value                    |
|-------------------------------|--------------------------|
| Source rows                   | 1,392                    |
| Output JSON size              | 380 kB (about 95k tokens)|
| JSON tokens seen by the model | 0                        |
| Total model tokens for the run| about 32k                |

Row count is not the cost driver, parser complexity is. See [design/pipeline-token-analysis.md](design/pipeline-token-analysis.md).

## How it works

Before the model writes any code, it studies the inspect report: a fill-rate profile per column and the merged-cell ranges. That's enough to work out the table's shape without reading a single row of data. A column with a low fill rate and a monotonic number usually marks a new entry. One with a similarly low fill rate but a small, repeating set of values usually marks a sub-group sitting between the entry and its details. A text column mixing `1.`, `a.`, and `1)` prefixes is a numbered tree, modeled as a recursive `{teks, sub[]}` node rather than three unrelated columns. That's structural inference, and it transfers cleanly to a completely different table next time.

That reasoning becomes a JSON Schema built to fail loudly. Setting `additionalProperties: false` turns a stray field from the parser into a hard error instead of silent drift. Codes and IDs are typed as strings with a `pattern`, so a leading zero survives instead of being eaten by automatic number coercion. Enums only appear where the inspect report shows a small, genuinely closed set of values. The schema itself gets checked against the JSON Schema meta-schema first, so a malformed schema shows up as a schema error rather than a wall of confusing instance errors.

Every validation failure gets triaged: the parser misread the source, or the schema is stricter than the source actually allows, and the fix targets whichever is true rather than dropping the offending row. Each run also prints its own accounting: rows seen in, entries and details out. When the numbers don't reconcile, the parser has a bug and needs fixing.

```mermaid
flowchart LR
  prepare --> inspect --> map --> schema --> parse --> validate --> dq[data-quality] --> summary
```

| Step         | Done by                    | What it does                                                        |
|--------------|----------------------------|---------------------------------------------------------------------|
| inspect      | `scripts/inspect_xlsx.py`  | Compact structure report: sheets, header, column profiles, samples  |
| map          | `structure-analyst` agent  | Proposes column-to-field mapping plus hierarchy (you confirm)       |
| schema       | `schema-designer` agent    | Authors or refines the Draft 2020-12 schema                         |
| parse        | `parser-builder` agent     | Writes `<job>.parser.py`, then iterates to zero errors              |
| validate     | `scripts/validate_json.py` | Schema-validation gate                                              |
| data-quality | `dq-reviewer` agent        | Runs `scripts/dq_check.py`, writes the data-quality report          |

## Commands

| Command                                  | Purpose                                                              |
|------------------------------------------|----------------------------------------------------------------------|
| `/excel-to-json:run <file.xlsx>`         | Full pipeline; pauses at confirmation gates (`--autonomous` to skip) |
| `/excel-to-json:new-job <file.xlsx>`     | Create the `docs/<job>/` folder and move the input in                |
| `/excel-to-json:inspect <file or job>`   | Structure report only                                                |
| `/excel-to-json:schema <job>`            | Create, refine, or validate a schema                                 |
| `/excel-to-json:convert <job>`           | Generate the parser and the JSON instance                            |
| `/excel-to-json:validate <job>`          | Validate instance against schema                                     |
| `/excel-to-json:review <job>`            | Data-quality review plus report                                      |
| `/excel-to-json:promote <job> [family]`  | Promote a clean job to a reusable family                             |

Each step is independently runnable. Do the whole pipeline, or just the part you need (for example, "make a schema for this existing JSON" with `schema <job> --from-instance`). In agents other than Claude Code, ask in plain language instead of using slash commands.

## Reuse across similar tables

Tables that share a structure do not have to be converted from scratch. After inspecting a new table, the pipeline fingerprints it **structurally, not by header text**, and matches it against families you have promoted from past jobs:

- **near-duplicate:** offer to clone the family's schema and parser, re-pointing columns;
- **same family:** warm-start the schema from the family canonical, then adapt;
- **no match:** convert from scratch.

Reuse is opt-in and never skips the gates: the parser still proves row conservation and the instance still validates. Details in [design/reuse.md](design/reuse.md).

## It learns from every table, not just the ones like it

Reuse, described above, matches tables that share a structure. This section covers something separate: a set of heuristics that sharpens with every job, regardless of the table's subject.

Take one example: a merged cell returns its value only in the top-left cell of the range, so continuation rows read as blank by design. That observation gets generalized, stripped of column letters, field names, and job IDs, then checked against existing entries for near-duplicates. Once you confirm it, it's appended to a plain-text file: `memory/learnings.md`. The next table you convert starts already knowing it.

Each entry is plain text you can open and edit yourself, added only through an explicit approval step. Every agent reads just the slice tagged for its role before it starts reasoning: the parser-builder pulls normalization and structure notes, the schema-designer pulls schema and structure notes. That keeps the store useful for years without bloating any single run's context, so token-frugality holds even as history accumulates.

Details in [memory/README.md](memory/README.md).

## Output: the job folder

Every conversion lives in one self-contained folder under `docs/` in your project root:

```
docs/table-YYYYMMDD-HHMMam/
  table.xlsx            source table
  table.inspect.md      structure report (and .json)
  table.schema.json     JSON Schema (Draft 2020-12)
  table.json            the converted instance
  table.parser.py       generated parser (reproduces the instance)
  table.dq.md           data-quality findings (and .json)
  summary-table.md      human-readable summary and field map
```

One table per job. Multiple sheets or tables become multiple jobs.

## Learn more

- [INSTALL.md](INSTALL.md) install for every supported agent, flags, troubleshooting
- [CONTRIBUTING.md](CONTRIBUTING.md) repository layout, standalone scripts, developer workflow
- [skills/excel-to-json/SKILL.md](skills/excel-to-json/SKILL.md) the skill the agent actually reads

## License

MIT, see [LICENSE](LICENSE).
