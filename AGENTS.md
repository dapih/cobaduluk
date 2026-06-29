## Project context

This repository is the **excel-to-json Claude Code plugin** — a pipeline that converts complex Excel tables into validated, schema-backed JSON. Core principle: **deterministic Python does all row-level work; the model only analyzes structure, authors the schema, writes the parser, and reviews samples.** A 3,000-row table costs the same model tokens as a 30-row table.

Current status (branch `ref1`): the full pipeline is built, tested, and committed. All design decisions listed in `design/reuse.md` are locked.

**Tool compatibility:** this plugin works in Claude Code (slash commands via `.claude-plugin/`), Cursor (`.cursor/rules/excel-to-json.mdc`), Kilo Code (`.kilocode/rules/excel-to-json.md`), and any AGENTS.md-aware CLI (Codex, Opencode, Antigravity — this file). Scripts are tool-agnostic Python. For non-Claude-Code tools, resolve the plugin root with `git rev-parse --show-toplevel`.

**Key docs (read these before developing):**
- `workflows/full-pipeline.md` — canonical step order, gates, and tool assignments
- `design/reuse.md` — same-family reuse system (fingerprint, families, tiers, conformance, learning loop)
- `design/pipeline-token-analysis.md` — which steps are zero-token vs model-involved, and why
- `README.md` — install, commands, layout
- `design/roadmap.md` — future development items and open decisions

**Locked decisions:** manual family promotion · always-ask gate before reuse (never auto-apply) · named families at medium curation · learnings appends only through the generalize-and-confirm gate (`learnings.py --lint`) · reuse never skips validation or row-conservation.

---

## Agent spawning

When asked to spawn agents or perform multi-agent tasks, use the Swarm MCP extension:

- `mcp__Swarm__Spawn` - Spawn agents (codex, cursor, gemini, claude)
- `mcp__Swarm__Status` - Check agent status
- `mcp__Swarm__Read` - Read agent output
- `mcp__Swarm__Stop` - Stop agents

Do NOT use built-in Claude Code agents (Task tool with Explore/Plan subagent_type) when Swarm agents are requested.

---

## Core principles

Bias: caution over speed on non-trivial work.

**Think first** — State assumptions explicitly. Ask rather than guess. Push back when a simpler approach exists. Stop when confused.

**Minimum change** — Touch only what the task requires. No speculative features, no adjacent refactoring, no abstractions for single-use code.

**Code does the work, model supervises** — Use the model for judgment: classification, drafting, extraction. If code can answer, code answers. Never use the model for deterministic transforms or routing. (This plugin's core design: Python processes every row; the model reads only compact reports.)

**Read before you write** — Before adding code, read callers and shared utilities. "Looks orthogonal" is dangerous.

**Checkpoint every significant step** — Summarize what's done, what's verified, what's left. Don't continue from a state you can't describe back.

**Match conventions** — Conformance over taste. If a convention seems harmful, surface it — don't fork silently.

**Fail loud** — "Done" is wrong if anything was skipped silently. Surface uncertainty; never hide it.

## Honesty

- Never claim a symbol, function, or import exists without verifying it (grep or read the file). Never fabricate stack traces or API responses.
- Don't claim a test or build passed unless you ran it in this session.
- "I don't know" is always better than a confident guess.

Before touching a symbol: read the file where it's defined or grep for it. If you skip this, mark the code `# UNVERIFIED`. Plan-then-execute for any task touching more than one file.

---

## Plugin-specific constraints (excel-to-json)

These capture invariants that live inside the pipeline commands and agents, not the general rules above.

### Never read the full table or full JSON into context
The full workbook and the full JSON instance are never passed to the model. Always work from `<job>.inspect.md` (the compact report from `inspect_xlsx.py`). If tempted to read `<job>.xlsx` or `<job>.json` directly — stop. That is the single non-negotiable of this plugin.

### All pipeline gates are mandatory
The following gates may not be skipped without explicit user instruction:
- **Step 2c** — match against families before mapping (advisory; always show result)
- **Step 4b** — run `conformance.py` on a same-family match before schema authoring
- **Step 6** — `validate_json.py` must exit 0 before the DQ step
- **Step 9** — every learnings append goes through `learnings.py --lint`; resolve all WARNs before appending

### Reuse is opt-in, never automatic
A family match (any tier) is advisory. Always present the result and wait for user confirmation before warm-starting, cloning, or applying a canonical. In `--autonomous` mode, default to KEEP (never evolve the canonical).

### Row conservation is non-negotiable
After every parser run, assert `rows_in == entries_out`. A parser that silently drops rows is broken, not "done". Do not mark the parse step complete until this assertion passes.

### Before changing a script in `scripts/`
- Read `workflows/full-pipeline.md` to understand which pipeline steps call it
- Read `design/reuse.md` if the change touches fingerprint, match, conformance, or promote logic
- Run the relevant script against the existing `docs/table-*/` jobs and confirm output is unchanged (or the delta is intentional)
- If the change affects token budget, run `python scripts/measure_tokens.py <job>` before and after

### Before adding to `memory/learnings.md`
Entries must be domain-agnostic and generalizable. Strip column letters, file names, job ids, and language-specific word lists. Run `python scripts/learnings.py --lint --entry '<entry>'` and resolve every WARN. Never append raw without the lint gate.
