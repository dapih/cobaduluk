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

The model is not just checking its own homework, it is reading the table the way an analyst would, before it writes a single line of code.

The inspect report hands it structural signals, not data: a fill-rate profile for every column, the merged-cell ranges, the blank-row gaps. From those alone, the model reasons out the table's shape. A column that's populated on only one row in every ten, holding a monotonic number? That's an entry boundary. A column with the same low fill rate but a small, repeating set of categorical values? That's a sub-group level sitting between the entry and its details. A text column where some cells start `1.`, others `a.`, others `1)`? That's a numbered tree wearing a spreadsheet disguise, and it gets modeled as a recursive `{teks, sub[]}` node, not three flat, disconnected columns. None of this is domain knowledge about licensing tables or product catalogs, it's structural inference, which is exactly why the same reasoning holds up on the next table, whatever it happens to be about.

That reasoning becomes a JSON Schema, and the schema is written to fail loudly. `additionalProperties: false` turns a stray field the parser emits into an error instead of quiet drift. Codes and IDs are typed as strings with a `pattern`, so a leading zero survives instead of being eaten by "helpful" number coercion. Enums are only used where the inspect report shows a genuinely closed, small set of values, never guessed. And the schema is checked against the JSON Schema meta-schema itself before it's allowed to check anything else, so a malformed schema fails as a schema error, not a confusing pile of instance errors.

Then the guard rails close the loop. Every validation failure is triaged as one of exactly two things: the parser misread the source, or the schema is stricter than the source actually is, never "delete the inconsistent row and move on." And after every run, the parser prints its own accounting: rows seen in, entries and detail items out. If the numbers don't reconcile, that's a bug to fix, not a rounding error to shrug at.

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

Reuse (above) matches tables that share a structure. This is different: it's a running set of heuristics that gets sharper with every job, regardless of what the table is about.

When a job uncovers something worth remembering, for instance that a merged cell only returns its value in the top-left cell of the range, so continuation rows read as blank by design, that observation doesn't die with the job. It's generalized, stripped of anything table-specific (column letters, field names, job IDs), linted for near-duplicates against what's already recorded, confirmed with you, and appended to a plain-text store: `memory/learnings.md`. The next table you convert, however unrelated, benefits from it.

This is not a model fine-tuning itself or weights changing. It's closer to a lab notebook: durable, readable, auditable notes that each agent consults before it starts reasoning, filtered to only what's relevant to its job (the parser-builder reads normalization and structure notes; the schema-designer reads schema and structure notes) so the store can grow for years without bloating any single run's context or breaking the token-frugality promise above.

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
