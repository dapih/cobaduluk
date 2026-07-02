---
name: Skill self-containment migration
overview: Move scripts/, skill-rules/, templates/, workflows/, memory/, and the operative half of design/reuse.md inside skills/excel-to-json/, so a generic "grab the SKILL.md folder" installer (npx skills add / skills.sh) produces a fully working skill, not a stub.
todos:
  - id: preflight
    content: "Confirm Claude Code's plugin loader tolerates extra subfolders under skills/<name>/; snapshot baseline verify_install.py / validate_marketplace.py / smoke_test_compat.py output"
    status: completed
  - id: move-scripts
    content: Move scripts/ into skills/excel-to-json/scripts/; update resolve_plugin_root.py MARKER and every $PLUGIN_ROOT/scripts/... reference
    status: completed
  - id: move-rules
    content: Move skill-rules/ into skills/excel-to-json/skill-rules/; update dq_check.py / parser_lib.py default-path references
    status: completed
  - id: move-templates
    content: Move templates/ into skills/excel-to-json/templates/; update job-conventions.md and new-job command references
    status: completed
  - id: move-workflows
    content: Move workflows/full-pipeline.md into skills/excel-to-json/workflows/; update resolve_plugin_root.py MARKER and every link
    status: completed
  - id: split-reuse
    content: Split design/reuse.md - operative sections to skills/excel-to-json/references/reuse.md, historical/decision-log sections stay in design/reuse.md
    status: completed
  - id: memory-optional
    content: "Move memory/ into skills/excel-to-json/memory/; update learnings.py path + references"
    status: completed
  - id: verify-mirrors
    content: Confirm install_adapters.py mirrors (which already link the whole skills/excel-to-json/ tree per agent) pick up the new subfolders with no code change
    status: completed
  - id: acceptance-test
    content: "New smoke-test mode: copy ONLY skills/excel-to-json/ into a scratch project (no bootstrap, no other repo folders) and run the pipeline end-to-end"
    status: completed
  - id: docs-and-release
    content: Update README/CONTRIBUTING layout sections, bump plugin manifests, tag/release
    status: "partial: layout docs done, manifest bump/tag deferred pending user go-ahead"
isProject: false
---

# Skill self-containment migration

## Why

`skills.sh` (`npx skills add`) and similar generic skill indexers only capture the folder containing `SKILL.md`, here `skills/excel-to-json/`. Everything the pipeline needs to actually *run* (`skills/excel-to-json/scripts/`, `skill-rules/`, `templates/`, `workflows/`) currently lives outside that folder, at the repo root. A plain `npx skills add` install therefore produces a skill that can describe the pipeline but can't execute it. This is already a known, documented gap (`INSTALL.md` and `skills/README.md` both warn "not sufficient alone"); this plan fixes the root cause instead of warning around it.

The earlier objection to nesting everything ("it'll duplicate the engine into every agent's mirrored folder") doesn't hold up. `install_adapters.py` links (`link_directory`, symlink/junction, copy only as fallback) the *whole* `skills/excel-to-json/` tree per agent already, so nesting `skills/excel-to-json/scripts/` etc. inside it costs nothing under the normal bootstrap install: a junction is just another path to the same files. The only place it has a real cost is the copy-fallback path and the `npx skills add` path, and making the latter actually work is the entire point.

## What moves in

| Folder | Destination | Why |
|---|---|---|
| `skills/excel-to-json/scripts/` | `skills/excel-to-json/skills/excel-to-json/scripts/` | Load-bearing at execution time; the skill can't run without it regardless of install method |
| `skill-rules/` | `skills/excel-to-json/skill-rules/` | Two small JSON configs scripts load at runtime; same reasoning as skills/excel-to-json/scripts/ |
| `templates/` | `skills/excel-to-json/templates/` | Filled in by the orchestrator during every job; needed to run the pipeline |
| `workflows/full-pipeline.md` | `skills/excel-to-json/workflows/full-pipeline.md` | Canonical step order the model and commands both reference mid-task |
| `design/reuse.md` (operative half only) | `skills/excel-to-json/references/reuse.md` (new) | Already treated by `SKILL.md` as a just-in-time reference alongside the other `references/*.md` files |
| `memory/` | `skills/excel-to-json/memory/` | Mutable per-install state, not skill definition, but the Phase 8 acceptance test found `learnings.py` fails hard on a skill-only install without it; moved to close that gap |

## What stays at repo root

- **`agents/`, `commands/`**: Claude Code's own plugin-root conventions. Its loader expects these at the plugin root, not nested inside a skill folder; moving them fixes nothing for skills.sh and breaks Claude Code.
- **`design/`** (minus the reuse.md split): `roadmap.md`, `pipeline-token-analysis.md`, `cross-tool-compat.md`, `measured-tokens-table-*.md`, `plans/` are maintainer-only. Not needed for the skill to function; keeping them out of the portable skill folder is correct, not an oversight.
- **`families/`, `output/`**: user-project-local runtime state, not plugin distribution content. Never touched by this migration.
- **`.claude-plugin/`, `.cursor-plugin/`**: marketplace manifests, fixed at repo root by spec.
- **`.agents/`, `.cursor/`, `.kilo/`, `.opencode/`**: per-tool mirror dot-folders. Structurally unaffected; they'll just mirror a bigger `skills/excel-to-json/` subtree afterward.

## The `$PLUGIN_ROOT` invariant (read before touching anything)

`resolve_plugin_root.py` resolves to the **repo root**, not to `skills/excel-to-json/`, and that can't change: on Claude Code, `${CLAUDE_PLUGIN_ROOT}` is set by the host to the plugin's manifest root (where `.claude-plugin/` lives) and we have no way to redefine that. `resolve_plugin_root.py` exists purely to compute the same value for tools that don't set the env var.

That means every reference changes from `$PLUGIN_ROOT/skills/excel-to-json/scripts/...` to `$PLUGIN_ROOT/skills/excel-to-json/skills/excel-to-json/scripts/...`; the root itself doesn't move, a path segment gets inserted. The walk-up fallback in `resolve_plugin_root.py` (`MARKER = Path("workflows") / "full-pipeline.md"`) needs exactly one change: `MARKER = Path("skills/excel-to-json/workflows") / "full-pipeline.md"`. Its walk-up logic isn't depth-sensitive (it checks each ancestor for the marker), so no other change is needed there.

## Migration scope (found by grep, 2026-07-02)

Files referencing a `skills/excel-to-json/scripts/...` path that need updating:

```
.agents/workflows/excel-to-json-run.md          agents/parser-builder.md
.kilo/commands/excel-to-json-*.md (6 files)      agents/schema-designer.md
AGENTS.md                                        agents/structure-analyst.md
CONTRIBUTING.md                                  commands/inspect.md
README.md                                        commands/promote.md
agents/dq-reviewer.md                            commands/run.md
                                                  commands/schema.md
                                                  commands/validate.md
design/reuse.md                                  templates/data-quality.md
memory/README.md                                 workflows/full-pipeline.md
skills/excel-to-json/SKILL.md
skills/excel-to-json/references/data-quality-checks.md
skills/excel-to-json/references/examples/README.md
skills/excel-to-json/references/parsing-patterns.md
```

Plus tooling that isn't a plain grep hit but has path assumptions baked in:

- `skills/excel-to-json/scripts/resolve_plugin_root.py`: the `MARKER` constant (see above)
- `skills/excel-to-json/scripts/bootstrap.py`, `skills/excel-to-json/scripts/install_adapters.py`: verify, don't assume, that no code hardcodes `skills/excel-to-json/scripts/`/`skill-rules/`/`templates/`/`workflows/` as repo-root-relative outside of what moving `CANONICAL_SKILL`'s contents already handles
- `skills/excel-to-json/scripts/verify_install.py`, `skills/excel-to-json/scripts/validate_marketplace.py`, `skills/excel-to-json/scripts/smoke_test_compat.py`: required-directory checks need their expected paths updated
- `install.sh`, `install.ps1`: any inline path examples in output/prompts
- The `sys.path.insert(0, r"<PLUGIN_ROOT>/scripts")` snippet baked into `SKILL.md` and `parsing-patterns.md` as instructional boilerplate for parser generation, becomes `<PLUGIN_ROOT>/skills/excel-to-json/scripts`

This list is not exhaustive by construction (grep finds strings, not intent). Re-grep before each phase's commit as a final check.

## Phases

Run the full checklist (`validate_marketplace.py`, `verify_install.py`, re-inspect both sample jobs in `output/table-2026*`) after **every** phase, not just at the end. Path-reference sprawl means a missed file fails silently (wrong-but-plausible path) rather than loudly.

### Phase 0 — Preflight
- Confirm Claude Code's plugin loader has no issue with extra subfolders under `skills/<name>/` (check Claude Code plugin docs, or test by adding a throwaway nested folder and running the plugin).
- Record current `verify_install.py` / `validate_marketplace.py` / `smoke_test_compat.py` output as the baseline to diff against.

### Phase 1 — Move `skills/excel-to-json/scripts/`
- `git mv scripts skills/excel-to-json/scripts`
- Update `resolve_plugin_root.py`'s `MARKER`
- Update all `$PLUGIN_ROOT/skills/excel-to-json/scripts/...` references (see scope list)
- Re-run checklist

### Phase 2 — Move `skill-rules/`
- `git mv skill-rules skills/excel-to-json/skill-rules`
- Update wherever `dq_check.py` / `parser_lib.py` load default rule paths, and any doc mentioning `skill-rules/*.json`
- Re-run checklist

### Phase 3 — Move `templates/`
- `git mv templates skills/excel-to-json/templates`
- Update `job-conventions.md`, `new-job` command, any "copy from `${CLAUDE_PLUGIN_ROOT}/templates/`" instruction
- Re-run checklist

### Phase 4 — Move `workflows/`
- `git mv workflows skills/excel-to-json/workflows`
- Update every `workflows/full-pipeline.md` link (`SKILL.md`, `commands/run.md`, agent defs, `CONTRIBUTING.md`)
- Re-run checklist

### Phase 5 — Split `design/reuse.md`
- Create `skills/excel-to-json/references/reuse.md`: Fingerprint, Reuse tiers, Family model, Flow, rewritten in the terse instructional register of the other `references/*.md` files, not the design-doc register
- Leave in `design/reuse.md`: Problem statement, dated spike results, Decisions (locked), Status & remaining work, Known refinements, Build order, `family.json` shape. This is a design-rationale record for maintainers, not something the model needs mid-task
- Update `SKILL.md`'s "When to read which reference" line from `../../design/reuse.md` to `references/reuse.md`
- Re-run checklist

### Phase 6 — Move `memory/`
- `git mv memory skills/excel-to-json/memory`
- Update `learnings.py`'s path resolution (simplifies: `memory/` becomes a sibling of `scripts/`, so two `dirname()` calls instead of four) and every `memory/learnings.md` / `memory/README.md` reference
- Re-run checklist
- Originally scoped as optional/deferrable; done after the Phase 8 acceptance test showed `learnings.py` fails hard on a skill-only install without it

### Phase 7 — Confirm mirroring needs no code change
- `install_adapters.py` already links the entire `skills/excel-to-json/` tree per agent (`CANONICAL_SKILL = Path("skills/excel-to-json")`); it never mirrored `skills/excel-to-json/scripts/` separately. Verify (don't assume) this holds by running `smoke_test_compat.py`'s full matrix and checking each agent's mirrored folder actually contains the new subfolders.

### Phase 8 — The acceptance test
This is the test that actually validates the motivating problem is fixed. Add a new smoke-test mode:
- In a scratch directory, copy **only** `skills/excel-to-json/` (no `bootstrap.py`, no other repo-root folder) into `.some-agent/skills/excel-to-json/`
- Run the pipeline end-to-end against a sample `.xlsx` using nothing but that folder
- This simulates exactly what `npx skills add` delivers today

**Result (2026-07-02, manual run):** `inspect_xlsx.py`, `dq_check.py`, and `validate_json.py` all ran correctly from the skill-only copy with zero other repo content present; `validate_json.py` against a real schema and instance returned `Valid: True (errors: 0)`. `dq_check.py` correctly resolved its sibling `skill-rules/` default config with no `$PLUGIN_ROOT` needed. One gap found at the time: `learnings.py --tags ...` failed (exit 2) in a skill-only install, since `memory/learnings.md` wasn't copied (Phase 6 was still deferred when this test ran). That is pre-existing fail-loud behavior in `learnings.py` itself, not a regression from this migration. Phase 6 was subsequently done specifically to close this gap; a skill-only install now has cross-job learnings from day one.

### Phase 9 — Docs and release
- Update README's "Layout (plugin repository)" tree and CONTRIBUTING's repository-layout section
- Update `INSTALL.md` / `skills/README.md` to remove or soften the "not sufficient alone" warning about `npx skills add`, since it's no longer true
- Bump plugin manifests, tag, release per the existing checklist in `CONTRIBUTING.md`

## Risks and things to not get wrong

- **The `rules/` config folder was renamed to `skill-rules/` before this migration ran** (both Cursor's `.cursor/rules/` and Kilo's `.kilo/rules/` are unrelated, tool-owned conventions that collided in name only). Phase 2 moves `skill-rules/`, not `rules/`.
- **Historical generated parsers** in `output/table-2026*/*.parser.py` hardcode the *old* absolute scripts path at generation time (written in once, not re-resolved). They keep working as-is and are not retroactively rewritten by this migration; that's expected, not a regression.
- **The copy-fallback install path** (`EXCEL_TO_JSON_FORCE_COPY=1`, or a failed junction) will genuinely duplicate the engine into each agent's mirror once `skills/excel-to-json/scripts/` moves in. This is a real, small, deliberately accepted cost that only affects a fallback path, not the primary symlink/junction-based install.
- **`resolve_plugin_root.py` still needs to resolve to the repo root, never to `skills/excel-to-json/`.** Redefining what "plugin root" means would break `${CLAUDE_PLUGIN_ROOT}` alignment on Claude Code, which the resolver can't override.

## What NOT to do

- Don't move `agents/` or `commands/`: Claude Code plugin-loader convention, not a generic-skill concern
- Don't move `families/` or `output/`: user-project-local runtime state, not plugin content
- Don't skip re-running the release checklist after each phase
- Don't retroactively rewrite already-generated `output/table-*/*.parser.py` files
- Don't dump the whole of `design/reuse.md` into `references/` or `skill-rules/` verbatim: split it, most of it is historical record, not task guidance
