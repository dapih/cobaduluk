# Normalization rules: safe vs risky

What to clean during parsing, and what to leave alone. Defaults live in `${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/skill-rules/normalization.default.json`; copy it into the job folder and tune per table. The guiding rule: **normalize formatting artifacts, preserve meaning.** When in doubt, don't transform — flag it in the DQ report instead.

## Always safe (on by default)

| Issue | Fix | Helper |
|---|---|---|
| Non-breaking spaces, zero-width chars | replace/remove | `clean()` |
| Leading/trailing whitespace | strip | `clean()` |
| Double/!internal runs of whitespace | collapse to single space | `clean()` |
| Trailing `.0` on integer codes | render as int string | `as_int_str()` |

`clean()` does the first three in one call. Apply it to every text cell at read time.

## Usually safe (review the inspect samples first)

| Issue | Fix | Helper | Caution |
|---|---|---|---|
| Line-break hyphenation `peri- zinan` → `perizinan` | merge hyphen + space | `dehyphenate()` | Only merges hyphen **followed by whitespace**; safe for wrapped words. |
| Bare placeholder `-`, `N/A`, `—` | → empty string / drop from array | `is_placeholder()`, `nest_by_pattern(drop=[...])` | Confirm the token really means "nothing" in this table. |

## Risky (off by default — enable only with evidence + a note)

| Issue | Why risky |
|---|---|
| Merge intra-word hyphen `wo-rd` → `word` (`merge_no_space=True`) | Catches line-break splits like `pe-nangkap`→`penangkap`, but can damage legitimate hyphenated terms (`e-commerce`). Enable per-table when the inspect samples show pervasive intra-word line-break hyphens. **Keep `protect_reduplication=True`** (the default) so reduplications like `undang-undang` / `sehari-hari` are preserved. |
| Strip trailing conjunctions (`... dan` / `... and`) | These are usually sentence fragments split across rows; trimming them can change legal/semantic meaning. Prefer to **keep** them and note the fragmentation, unless the user wants list items rejoined. |
| Auto-dedup of list items | Fine when repeats are pure redundancy; wrong when a repeat is structurally meaningful (model it as a level instead). Decide from meaning. |

## Placeholder → empty (a standing recommendation)

A cell containing only `-` or a blank-looking token almost always means "no value here". Standard handling:
- scalar field → empty string `""` (or null if the field is genuinely nullable)
- array field → empty array `[]` (drop the placeholder item)

Surface this as a recommendation in the DQ report and apply it after confirmation, per the workflow.

## How to decide

1. Look at the **inspect samples** for the column. Do the artifacts appear? Are there counter-examples (legitimate hyphens, meaningful dashes)?
2. Prefer the **narrowest** transform that fixes the artifact without touching good data.
3. Encode the decision in the job's normalization rules file and **log it**, so the next similar table can reuse the choice (see `${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/memory/learnings.md`).
4. If a transform is even slightly judgment-laden, leave the data raw and **report** it rather than silently changing it.
