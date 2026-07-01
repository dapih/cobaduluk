# Contributing to excel-to-json

Developer and agent-maintainer guide. User-facing install and usage: [README.md](README.md), [INSTALL.md](INSTALL.md).

Cross-tool migration status: [design/cross-tool-compat.md](design/cross-tool-compat.md).

---

## Key docs

- `workflows/full-pipeline.md` — canonical step order, gates, tool assignments
- `design/reuse.md` — fingerprint, families, tiers, conformance
- `design/pipeline-token-analysis.md` — zero-token vs model-involved steps
- `design/roadmap.md` — future items and open decisions
- `design/plans/cross-tool-skills-migration.md` — marketplace + multi-tool rollout plan

**Locked decisions:** manual family promotion · always-ask gate before reuse · named families at medium curation · learnings via `learnings.py --lint` only · reuse never skips validation or row-conservation.

---

## Agent spawning (Swarm MCP)

When asked to spawn agents or perform multi-agent tasks, use the Swarm MCP extension:

- `mcp__Swarm__Spawn` — codex, cursor, gemini, claude
- `mcp__Swarm__Status` — check agent status
- `mcp__Swarm__Read` — read agent output
- `mcp__Swarm__Stop` — stop agents

Do NOT use built-in Claude Code Task subagents (Explore/Plan) when Swarm agents are requested.

---

## Core principles

Bias: caution over speed on non-trivial work.

- **Think first** — state assumptions; ask rather than guess.
- **Minimum change** — touch only what the task requires.
- **Code does the work, model supervises** — Python for row-level work; model reads compact reports only.
- **Read before you write** — read callers and shared utilities first.
- **Checkpoint** — summarize done / verified / left at each significant step.
- **Match conventions** — surface harmful conventions; don't fork silently.
- **Fail loud** — never mark done if something was skipped silently.

## Honesty

- Never claim a symbol exists without verifying (grep or read the file).
- Don't claim tests passed unless you ran them in the session.
- Mark unverified code `# UNVERIFIED`. Plan-then-execute for multi-file changes.

---

## Before changing a script in `scripts/`

1. Read `workflows/full-pipeline.md` for pipeline step callers.
2. Read `design/reuse.md` if touching fingerprint, match, conformance, or promote.
3. Re-run against existing `docs/table-*/` jobs; output unchanged unless intentional.
4. If token budget affected: `python scripts/measure_tokens.py <job>` before and after.
5. After structural changes: `python scripts/validate_marketplace.py` and `python scripts/verify_install.py`.

---

## Before adding to `memory/learnings.md`

Entries must be domain-agnostic and generalizable. Strip column letters, file names, job ids, language-specific lists. Run:

```bash
python scripts/learnings.py --lint --entry '<entry>'
```

Resolve every WARN before appending. Never append raw without the lint gate.

---

## Release checklist

```bash
pip install -r requirements.txt
python scripts/link_skill_discovery.py      # if discovery mirrors missing (dev checkout only)
python scripts/validate_marketplace.py
python scripts/verify_install.py
python scripts/smoke_test_compat.py         # includes nested bootstrap gate
```

Nested install smoke (from a temp project):

```bash
python scripts/smoke_test_compat.py
```

Tag releases as `v0.1.0` (match `.claude-plugin/plugin.json` version). See [INSTALL.md](INSTALL.md) for marketplace publish steps.
