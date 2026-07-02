# Cross-tool compatibility — progress tracker

Live status for the [cross-tool skills migration plan](plans/cross-tool-skills-migration.md).

**Not** [`memory/learnings.md`](../skills/excel-to-json/memory/learnings.md) — that file is for Excel-conversion pipeline insights only. This doc tracks marketplace install, path resolution, and per-agent smoke tests.

---

## Milestones

| ID | Milestone | Gate | Status | Completed |
|---|---|---|---|---|
| **M0** | Plan saved to repo + compat doc scaffold | Files exist | **done** | 2026-06-30 |
| **M1** | Marketplace manifest + INSTALL.md | `validate_marketplace.py` pass | **done** | 2026-06-30 |
| **M2** | Plugin root resolver | Nested install smoke test | **done** | 2026-06-30 |
| **M3** | Cross-tool discovery symlinks | No duplicated SKILL content in rules | **done** | 2026-06-30 |
| **M4** | Workflow adapters (Kilo + Antigravity) | Commands reference resolver | **done** | 2026-06-30 |
| **M5** | Public release (LICENSE, tag v0.1.0) | `verify_install.py` pass | **done** | 2026-06-30 |
| **M6** | Smoke matrix complete (8 tools) | All rows pass or documented workaround | **done** | 2026-06-30 |
| **M7** | skills.sh indexed | `npx skills add` telemetry run | **done** | 2026-06-30 |

Do not mark a milestone **done** until its gate passes.

---

## Checkpoints

| ID | Check | Status | Notes |
|---|---|---|---|
| **CP1** | `python skills/excel-to-json/scripts/validate_marketplace.py` → exit 0 | **pass** | 2026-06-30 |
| **CP2** | `python skills/excel-to-json/scripts/verify_install.py` → exit 0 | **pass** | 2026-06-30 |
| **CP3** | Nested install test — clone into test project, run inspect from parent dir | **pass** | resolver via script path from parent CWD (2026-06-30) |
| **CP4** | Update session log with test results | **pass** | M6 session log + `smoke_test_compat.py` (2026-06-30) |
| **CP5** | Git tag + README marketplace section reviewed | partial | README + INSTALL updated; `git tag v0.1.0` when ready (gh release blocked on auth) |

---

## Smoke test matrix

Run after M1–M3. Record tool version and install path in the session log.

| Tool | Marketplace install command | Trigger | Pass criteria | Status |
|---|---|---|---|---|
| Claude Code | `/plugin marketplace add dapih/cobaduluk` + `/plugin install excel-to-json@cobaduluk` | `/excel-to-json:inspect` | Plugin root resolves | **structural pass** — manifest + 8 commands; runtime needs Claude Code session |
| Cursor | `install.sh` / `install.ps1` (or bootstrap) **or** `npx skills add … --agent cursor` + `--replace-copies` | natural language | Skill at **project root** `.cursor/skills/`, no duplicate in `excel-to-json/` | **pass (local)** — bootstrap + nested smoke; marketplace manifest in `.cursor-plugin/` |
| Codex | `npx skills add … --agent codex -y` + full clone | `$excel-to-json` | `.agents/skills/` found | **structural pass** — mirror + AGENTS.md; Codex CLI not on PATH |
| OpenCode | `npx skills add … --agent opencode -y` + full clone | skill tool | Listed in skill tool | **structural pass** — `.opencode/skills/` mirror |
| Antigravity | `npx skills add … --agent antigravity -y` + full clone | workflow/skill | Skill loads | **structural pass** — `.agents/skills/` + `excel-to-json-run` workflow |
| OpenClaw | `npx skills add … --agent openclaw -y` + full clone | skill load | `skills/` found | **structural pass** — canonical + `.agents/` mirror |
| Kilo Code | bootstrap `--agents kilo` (or interactive install) **or** `npx skills add … --agent kilo` + bootstrap | `/excel-to-json-run` | `.kilo/` at **project root** | **structural pass** — 6 commands + `kilo.jsonc`; extension not auto-detected from PATH |
| Hermes | `hermes skills tap add dapih/cobaduluk` + install | `/excel-to-json` | Skill in `~/.hermes/skills/` | **structural pass** — INSTALL.md tap docs; Hermes CLI not on PATH |

**Automated gate:** `python skills/excel-to-json/scripts/smoke_test_compat.py` (structural checks for all 8 + nested resolver).

**Workarounds documented:**
- **Recommended install:** `install.sh` / `install.ps1` from project root (interactive bootstrap). Clones to `excel-to-json/`, writes adapters at project root, strips duplicate mirrors inside clone.
- Do **not** rely on `npx skills add` alone — copies skill only, no Python scripts. Use bootstrap or `--replace-copies` after skills CLI.
- Do **not** run `npx skills add .` from plugin repo root — it copies into `.agents/skills/` and breaks junction mirrors. Use a nested test project, or restore with `python skills/excel-to-json/scripts/link_skill_discovery.py --replace-copies`.
- Legacy path `tools/excel-to-json/` — move to `excel-to-json/` at project root and re-run bootstrap.

---

## Session log (append-only)

Newest entries at the top. Capture: tool version, install path, result, root cause, change made, follow-up.

### 2026-07-02 — Cursor-native subagents

- **Attempted:** verify (against Cursor's actual docs, not assumption) whether Cursor, Codex, and Antigravity have a native mechanism to invoke the plugin's `agents/*.md` files as real subagents, and close the gap for whichever platform it's cheap to close.
- **Findings:** Codex only reads subagents as TOML at `.codex/agents/` (Markdown is invisible to it regardless of location). Antigravity has no static-file subagent mechanism at all — subagents are created dynamically at runtime via a tool call. Cursor does have a real, documented equivalent (Markdown + frontmatter, scanned from `.cursor/agents/` by default), but with a narrower schema (`name`/`description`/`model`/`readonly`/`is_background` — no `tools:`/`color:`) and no equivalent to `${CLAUDE_PLUGIN_ROOT}`.
- **Result:** success — Cursor only
- **Change made:**
  - [`skills/excel-to-json/scripts/install_adapters.py`](../skills/excel-to-json/scripts/install_adapters.py) — `transform_agent_for_cursor()` converts each Claude Code subagent file into Cursor's schema (drops `tools:`/`color:`, adds `model: inherit`, replaces `${CLAUDE_PLUGIN_ROOT}` with the existing `$PLUGIN_ROOT`-via-`resolve_plugin_root.py` pattern already used by the Kilo/Antigravity adapters); `install_cursor_agents_with_rel()` writes the four transformed files to `.cursor/agents/` during bootstrap
  - [`skills/excel-to-json/scripts/smoke_test_compat.py`](../skills/excel-to-json/scripts/smoke_test_compat.py) — `PROJECT_BOOTSTRAP_CHECKS["cursor"]` now asserts all four `.cursor/agents/*.md` files exist post-bootstrap
- **Verified:** transform output inspected file-by-file (frontmatter correctly trimmed, `$PLUGIN_ROOT` substitution correct, generic `<path-to-plugin>`/`<resolver output>` placeholders left untouched); real nested-install run in a scratch project produced correct `.cursor/agents/*.md`; full checklist (`validate_marketplace.py`, `verify_install.py`, `smoke_test_compat.py`) passes
- **Follow-up:** not manually tested inside an actual running Cursor session — the docs-verified schema is trusted, but whether Cursor's subagent loader tolerates this specific output has not been confirmed live. Codex (TOML) and Antigravity (no static mechanism) are correctly out of scope, not deferred gaps.

### 2026-06-29 — Bootstrap installers + Cursor marketplace manifest

- **Attempted:** OS-aware per-agent install at project root; interactive `install.ps1` / `install.sh`; `.cursor-plugin/` manifest; nested bootstrap smoke test.
- **Environment:** Windows 10; Python 3.x; junction/symlink/copy fallback in `install_adapters.py`.
- **Result:** success (merged to `main`)
- **Change made:**
  - [`skills/excel-to-json/scripts/install_adapters.py`](../skills/excel-to-json/scripts/install_adapters.py), [`skills/excel-to-json/scripts/install_prompt.py`](../skills/excel-to-json/scripts/install_prompt.py) — interactive agent selection; adapters at user project root
  - [`skills/excel-to-json/scripts/bootstrap.py`](../skills/excel-to-json/scripts/bootstrap.py) — `--interactive` / `--non-interactive`; strip nested discovery mirrors; shallow walk for `pluginRoot` on Windows
  - [`install.ps1`](../install.ps1), [`install.sh`](../install.sh) — default clone path `excel-to-json/`; interactive by default
  - [`.cursor-plugin/`](../.cursor-plugin/) — Cursor marketplace manifest (parallel to `.claude-plugin/`)
  - [`skills/excel-to-json/scripts/smoke_test_compat.py`](../skills/excel-to-json/scripts/smoke_test_compat.py) — nested bootstrap gate (copytree, project-root adapters, no `excel-to-json/.cursor/skills`)
  - [`README.md`](../README.md), [`INSTALL.md`](../INSTALL.md), [`skills/README.md`](../skills/README.md) — install docs aligned
- **Verified:** nested bootstrap smoke; resolver from project CWD; duplicate-skill strip when plugin physically under project
- **Follow-up:** `git tag v0.1.0` + GitHub release when `gh auth login` available; user-global scope still not implemented (prompt documents project-only)

### 2026-06-30 — M7 complete

- **Attempted:** Seed skills.sh index via telemetry install from temp project dir.
- **Environment:** Windows 10; skills CLI (npm `skills@1.5.14` via npx); Cursor CLI detected.
- **Command:** `npx skills add dapih/cobaduluk --skill excel-to-json --all -y` (cwd: `%TEMP%\etj-m7-*`, not plugin root)
- **Result:** success
- **Verified:**
  - Install exit 0; skill copied to `.agents/skills/excel-to-json/SKILL.md` in temp dir
  - Listing live: [skills.sh/dapih/cobaduluk/excel-to-json](https://skills.sh/dapih/cobaduluk/excel-to-json) — First Seen: Today; Gen Agent Trust Hub + Snyk: Pass
  - Install command on page: `npx skills add https://github.com/dapih/cobaduluk --skill excel-to-json`
- **Follow-up:** Optional `git tag v0.1.0` (CP5); manual runtime smoke for Claude Code / Hermes when those CLIs are available

### 2026-06-30 — M6 complete

- **Attempted:** 8-tool smoke matrix; automated structural gate; local `npx skills` discovery/install.
- **Environment:** Windows 10; Python 3.14.2; Node/npx 11.6.2; skills CLI 1.5.14; Cursor CLI on PATH; Hermes/Codex not on PATH.
- **Result:** success (structural + local Cursor/npx; runtime manual for 6 tools)
- **Change made:**
  - [`skills/excel-to-json/scripts/smoke_test_compat.py`](../skills/excel-to-json/scripts/smoke_test_compat.py) — M6 automated gate (8 tools + nested resolver)
  - [`skills/excel-to-json/scripts/link_skill_discovery.py`](../skills/excel-to-json/scripts/link_skill_discovery.py) — `--replace-copies` after accidental `npx skills add` in repo root
- **Verified:**
  - `python skills/excel-to-json/scripts/smoke_test_compat.py` → exit 0
  - `npx skills add . --list` and `npx skills add dapih/cobaduluk --list` → discover `excel-to-json`
  - `npx skills add . --skill excel-to-json --agent cursor -y` in temp nested clone → copies to `.agents/skills/excel-to-json/SKILL.md`
  - Cursor workspace: rule + skill mirror + resolver OK
- **Workaround:** Running `npx skills add` from plugin root replaces `.agents/skills/` junction with a copy — restore via `link_skill_discovery.py --replace-copies`. End-user nested installs should copy (expected); junctions are repo-dev only.
- **Not tested (manual):** Claude Code `/plugin install`, OpenCode skill picker, Antigravity workflow trigger, Kilo `/excel-to-json-run`, Hermes tap (no CLI).
- **Follow-up:** M7 after public GitHub push + commit untracked scripts; optional manual runtime pass per tool; `git tag v0.1.0`

### 2026-06-30 — M5 complete

- **Attempted:** Public release files; split AGENTS/CONTRIBUTING; verify_install gate.
- **Result:** success
- **Change made:**
  - [`LICENSE`](../LICENSE) (MIT), [`requirements.txt`](../requirements.txt)
  - [`skills/excel-to-json/scripts/verify_install.py`](../skills/excel-to-json/scripts/verify_install.py) — CP2 pass
  - Slim [`AGENTS.md`](../AGENTS.md); dev rules in [`CONTRIBUTING.md`](../CONTRIBUTING.md)
  - [`README.md`](../README.md) — marketplace-first install, updated layout
- **Not done:** `git tag v0.1.0` (run manually when publishing to GitHub)
- **Follow-up:** M6 smoke matrix; M7 skills.sh telemetry after public push

### 2026-06-30 — M4 complete

- **Attempted:** Kilo slash commands + Antigravity workflow; all use `resolve_plugin_root.py`.
- **Result:** success
- **Change made:**
  - [`.kilo/commands/excel-to-json-{run,inspect,schema,convert,validate,review}.md`](../.kilo/commands/)
  - [`.agents/workflows/excel-to-json-run.md`](../.agents/workflows/excel-to-json-run.md)
  - [`INSTALL.md`](../INSTALL.md) — Kilo/Antigravity command table
  - [`validate_marketplace.py`](../skills/excel-to-json/scripts/validate_marketplace.py) — checks commands/workflows reference resolver
- **Follow-up:** M5 — LICENSE, requirements.txt, verify_install.py, README, git tag

### 2026-06-30 — M3 complete

- **Attempted:** Cross-tool skill discovery mirrors; slim Cursor/Kilo rules; Kilo config stub.
- **Result:** success
- **Change made:**
  - Junctions: `.agents/skills/`, `.cursor/skills/`, `.kilo/skills/`, `.opencode/skills/` → `skills/excel-to-json/`
  - [`skills/excel-to-json/scripts/link_skill_discovery.py`](../skills/excel-to-json/scripts/link_skill_discovery.py) — recreate mirrors after clone
  - Slim [`.cursor/rules/excel-to-json.mdc`](../.cursor/rules/excel-to-json.mdc) — skill pointer only (no duplicated pipeline table)
  - [`.kilo/kilo.jsonc`](../.kilo/kilo.jsonc), [`.kilo/rules/excel-to-json.md`](../.kilo/rules/excel-to-json.md)
  - [`.kilocode/rules/excel-to-json.md`](../.kilocode/rules/excel-to-json.md) — deprecation stub
  - [`validate_marketplace.py`](../skills/excel-to-json/scripts/validate_marketplace.py) — checks discovery mirrors
- **Verified:** all four mirrors resolve to canonical `SKILL.md`; CP1 still passes
- **Follow-up:** M4 — `.kilo/commands/`, `.agents/workflows/`

### 2026-06-30 — M2 complete

- **Attempted:** Plugin root resolver for nested install; update SKILL, agents, workflows, Cursor/Kilo rules, INSTALL, AGENTS, README.
- **Result:** success
- **Change made:**
  - [`skills/excel-to-json/scripts/resolve_plugin_root.py`](../skills/excel-to-json/scripts/resolve_plugin_root.py) — `CLAUDE_PLUGIN_ROOT` → `EXCEL_TO_JSON_ROOT` → walk CWD → walk from script
  - Updated [`skills/excel-to-json/SKILL.md`](../skills/excel-to-json/SKILL.md), [`agents/parser-builder.md`](../agents/parser-builder.md), [`workflows/full-pipeline.md`](../skills/excel-to-json/workflows/full-pipeline.md), [`.cursor/rules/excel-to-json.mdc`](../.cursor/rules/excel-to-json.mdc), [`.kilocode/rules/excel-to-json.md`](../.kilocode/rules/excel-to-json.md)
- **Verified:** resolver exits 0 from plugin root, from parent CWD via script path, and via `EXCEL_TO_JSON_ROOT`
- **Follow-up:** M3 — discovery symlinks (`.agents/skills/`, `.cursor/skills/`, `.kilo/skills/`)

### 2026-06-30 — Marketplace renamed to cobaduluk

- **Attempted:** Rename Claude Code marketplace id from `dapih-plugins` to `cobaduluk`.
- **Result:** success
- **Change made:** `.claude-plugin/marketplace.json`, `INSTALL.md`, plan + compat docs; install command is now `/plugin install excel-to-json@cobaduluk`
- **Follow-up:** M2 — plugin root resolver

### 2026-06-30 — M1 complete

- **Attempted:** Claude Code marketplace manifest, INSTALL.md, skills README, well-known index, validate_marketplace.py.
- **Result:** success
- **Change made:**
  - [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) — catalog `cobaduluk`, plugin `excel-to-json@0.1.0`
  - [`INSTALL.md`](../INSTALL.md) — per-tool GitHub-URL install commands
  - [`skills/README.md`](../skills/README.md) — skills.sh discovery pointer
  - [`.well-known/skills/index.json`](../.well-known/skills/index.json) — optional well-known discovery
  - [`skills/excel-to-json/scripts/validate_marketplace.py`](../skills/excel-to-json/scripts/validate_marketplace.py) — CP1 gate (exit 0)
  - [`README.md`](../README.md) — link to INSTALL.md
- **Follow-up:** M2 — `skills/excel-to-json/scripts/resolve_plugin_root.py` for nested install

### 2026-06-30 — M0 complete

- **Attempted:** Save plan to repo; scaffold progress tracker.
- **Result:** success
- **Change made:**
  - Added [`design/plans/cross-tool-skills-migration.md`](plans/cross-tool-skills-migration.md) (canonical plan copy)
  - Added this file (`design/cross-tool-compat.md`)
  - Replaced duplicate `design/cross-tool_skills_migration.plan.md` with pointer to canonical plan
- **Follow-up:** M1 — `.claude-plugin/marketplace.json`, `INSTALL.md`, `skills/excel-to-json/scripts/validate_marketplace.py`
