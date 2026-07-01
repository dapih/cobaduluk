# Contributing to excel-to-json

Developer and agent-maintainer guide. For user-facing install and usage, see [README.md](README.md) and [INSTALL.md](INSTALL.md). Cross-tool migration status is tracked in [design/cross-tool-compat.md](design/cross-tool-compat.md).

## Repository layout

Paths below are inside the **cobaduluk** checkout (which becomes `excel-to-json/` when nested in a user project). After bootstrap, agent adapters also appear at the **user's project root**, see [INSTALL.md](INSTALL.md).

```
.claude-plugin/            Claude Code marketplace (plugin.json, marketplace.json)
.cursor-plugin/            Cursor marketplace (same layout)
.agents/skills/            skill mirror (dev checkout; stripped from nested clone)
.agents/workflows/         Antigravity workflow templates
.cursor/skills/            skill mirror (dev checkout)
.kilo/commands/            Kilo slash-command templates
commands/                  Claude Code slash commands
agents/                    structure-analyst, schema-designer, parser-builder, dq-reviewer
skills/excel-to-json/      canonical SKILL.md and references/
scripts/                   pipeline plus bootstrap.py, install_adapters.py, verify_install.py
templates/                 log, data-quality, summary, schema-summary
rules/                     default normalization and DQ configs
workflows/full-pipeline.md canonical step order
design/                    reuse, roadmap, cross-tool-compat, token analysis
memory/learnings.md        cross-job learnings
families/                  promoted family canonicals
```

The two marketplace manifests both point at the repo root (`"source": "."`). Local bootstrap is still recommended for nested clones and multi-agent setups.

## Standalone scripts

Every pipeline script is runnable on its own:

```
python scripts/inspect_xlsx.py   <file.xlsx> [--sheet NAME] [--out PREFIX]
python scripts/validate_json.py  <schema.json> <instance.json> [--counts]
python scripts/dq_check.py       <instance.json> [--rules rules.json] [--out PREFIX]
python scripts/fingerprint.py    <job.inspect.json> [--out PREFIX]
python scripts/match_profile.py  <job.inspect.json> [--families DIR] [--top N]
python scripts/promote_family.py <job-id> --name <family> [--force] [--evolve]
python scripts/conformance.py    <job.inspect.json> --name <family> [--job-schema PATH]
python scripts/learnings.py      --tags structure,tooling
```

## Key docs

- `workflows/full-pipeline.md` canonical step order, gates, tool assignments
- `design/reuse.md` fingerprint, families, tiers, conformance
- `design/pipeline-token-analysis.md` zero-token versus model-involved steps
- `design/roadmap.md` future items and open decisions
- `design/plans/cross-tool-skills-migration.md` marketplace and multi-tool rollout plan

**Locked decisions:** manual family promotion; always-ask gate before reuse; named families at medium curation; learnings via `learnings.py --lint` only; reuse never skips validation or row-conservation.

## Agent spawning (Swarm MCP)

When asked to spawn agents or perform multi-agent tasks, use the Swarm MCP extension:

- `mcp__Swarm__Spawn` codex, cursor, gemini, claude
- `mcp__Swarm__Status` check agent status
- `mcp__Swarm__Read` read agent output
- `mcp__Swarm__Stop` stop agents

Do NOT use built-in Claude Code Task subagents (Explore, Plan) when Swarm agents are requested.

## Core principles

Bias: caution over speed on non-trivial work.

- **Think first** state assumptions; ask rather than guess.
- **Minimum change** touch only what the task requires.
- **Code does the work, model supervises** Python for row-level work; the model reads compact reports only.
- **Read before you write** read callers and shared utilities first.
- **Checkpoint** summarize done, verified, and left at each significant step.
- **Match conventions** surface harmful conventions; don't fork silently.
- **Fail loud** never mark done if something was skipped silently.

## Honesty

- Never claim a symbol exists without verifying (grep or read the file).
- Don't claim tests passed unless you ran them in the session.
- Mark unverified code `# UNVERIFIED`. Plan, then execute, for multi-file changes.

## Before changing a script in `scripts/`

1. Read `workflows/full-pipeline.md` for pipeline step callers.
2. Read `design/reuse.md` if touching fingerprint, match, conformance, or promote.
3. Re-run against existing `docs/table-*/` jobs; output unchanged unless intentional.
4. If the token budget is affected: run `python scripts/measure_tokens.py <job>` before and after.
5. After structural changes: run `python scripts/validate_marketplace.py` and `python scripts/verify_install.py`.

## Before adding to `memory/learnings.md`

Entries must be domain-agnostic and generalizable. Strip column letters, file names, job ids, and language-specific lists. Run:

```bash
python scripts/learnings.py --lint --entry '<entry>'
```

Resolve every WARN before appending. Never append raw without the lint gate.

## Release checklist

```bash
pip install -r requirements.txt
python scripts/link_skill_discovery.py      # if discovery mirrors missing (dev checkout only)
python scripts/validate_marketplace.py
python scripts/verify_install.py
python scripts/smoke_test_compat.py          # includes nested bootstrap gate
```

Tag releases as `v0.1.x` (matching the version in `.claude-plugin/plugin.json`). See [INSTALL.md](INSTALL.md) for marketplace publish steps.
