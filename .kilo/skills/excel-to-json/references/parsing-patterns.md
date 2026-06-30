# Parsing patterns for complex tables

How to turn a messy, hierarchical Excel sheet into clean nested JSON with a small, deterministic parser. Read this before writing `<job>.parser.py`.

## 1. Read the inspect report first

`inspect_xlsx.py` already told you: header row, per-column fill rate, inferred types, distinct/sample values, merged-cell ranges, and blank-row gaps. Use it to answer four questions **before writing any code**:

1. **Which column marks a new top-level entry?** Usually a column with a low fill rate that is populated only on the first row of each entry (e.g. a running number, an ID, a code). Low fill rate + monotonic int is the classic tell.
2. **Which columns are "header" attributes** (one value per entry) vs **list/detail columns** (many rows per entry)? Fill rate reveals this: ~`1/avg_block_size` for headers, high for detail lists.
3. **Is there sub-grouping** (intermediate levels between entry and detail)? Look for mid-fill-rate categorical columns (e.g. a risk level, a category, a status).
4. **Which detail columns carry multi-level numbering** (`1.` / `a.` / `1)`)? Those become nested trees.

## 2. The row state-machine

Most complex regulatory/tabular sheets are **denormalized**: one logical entry spans many physical rows, and "header" cells are filled only on the entry's first row (often because cells were merged). Parse with a single forward pass that keeps "current" pointers:

```python
import sys
# Job folder lives in the user's project, not under the plugin — use the
# absolute path from resolve_plugin_root.py (written in at generation).
sys.path.insert(0, r"<PLUGIN_ROOT>/scripts")
from parser_lib import clean, dehyphenate, nest_by_pattern, dedupe, as_int_str, write_json
import openpyxl

wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb["<sheet>"]

entries = []
cur = None              # current top-level entry
rows_seen = 0           # populated source rows, for the count check

for row in ws.iter_rows(min_row=DATA_START_ROW, values_only=True):
    if all(c is None or str(c).strip() == "" for c in row):
        continue                      # skip blank separator rows
    rows_seen += 1
    A, B, C, *rest = row              # name columns explicitly by position

    if A is not None:                 # ── new entry boundary ──
        if cur is not None:
            entries.append(finalize(cur))
        cur = new_entry(A, B, C, ...)
    else:                             # ── continuation row ──
        accumulate(cur, row)          # append detail cells to current entry's lists

if cur is not None:
    entries.append(finalize(cur))
```

Key ideas:
- **Boundary detection** is one explicit condition (a key cell is non-empty). Everything else is a continuation.
- **Accumulate** detail cells into flat lists on the current entry; defer nesting to `finalize`.
- **Name columns by position** (`A, B, C = row[0], row[1], row[2]`) so the logic is readable and reviewable.

## 3. Merged cells

`openpyxl` returns the value only in a merged range's **top-left** cell; the other cells read as `None`. That is exactly why "header" columns look empty on continuation rows — and why the state-machine above works. If a merged range matters (e.g. a header spanning columns), the inspect report lists the ranges; handle them explicitly rather than guessing.

## 4. Multi-level numbering → `nest_by_pattern`

When a detail column mixes levels like `1.` → `a.` → `1)`, collect the flat list during accumulation, then nest in `finalize`:

```python
node["persyaratan"] = nest_by_pattern(
    flat_list,
    levels=[("num", r"^\d+\."), ("alpha", r"^[a-z]\."), ("paren", r"^\d+\)")],
    drop=["-"],            # remove bare placeholders
    orphan="attach",       # unlabeled text continues the previous item
)
```

- `orphan="attach"` → unlabeled lines extend the deepest open item (continuation prose).
- `orphan="group"` → an unlabeled line starts a new top-level group the next items nest under (use when the column has conditional category headers like "For those using X:").
- Pick patterns from what the inspect samples actually show; don't assume a numbering style.

## 5. Denormalized repeats and de-duplication

If the sheet repeats the same detail across several rows that differ only by a secondary attribute (e.g. one row per business scale, same requirements), those rows append duplicates into the same list. Two correct responses:

- **Separate** them into distinct sub-groups if the attribute is structurally meaningful (model it as a level), **or**
- **De-duplicate** the list with `dedupe(...)` (order-preserving) if the repeat is pure redundancy.

Decide from meaning, not convenience, and record the choice in the log.

## 6. The row-count guarantee

Never drop a row silently. After parsing, prove conservation:

```python
print(f"rows_seen={rows_seen} entries={len(entries)} "
      f"details={sum(count_details(e) for e in entries)}")
```

Reconcile `rows_seen` against entries + accumulated detail items. If the numbers don't add up, a boundary or continuation case is wrong — fix the parser, do not paper over it. Put the reconciliation in `log-<job>.md`.

## 7. Iterate against the validator

Run `parse → validate_json.py` in a loop. Each schema error points to a row/field the parser handled wrong (or a schema rule that's too strict). Fix one cause at a time; re-run; stop at **0 errors**. Keep the parser small — push reusable logic into `parser_lib.py`, keep only table-specific shape in `<job>.parser.py`.
