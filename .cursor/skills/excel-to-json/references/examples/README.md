# Worked-output exemplars

Tiny, **synthetic** files that illustrate the *form* the pipeline targets — not any real dataset. Use them as a shape reference; your real `<job>.schema.json` and instance will mirror this structure with your table's actual fields and values.

| File | Shows |
|---|---|
| `example.schema.json` | A Draft 2020-12 schema: `$defs` + `$ref`, a 2-level hierarchy (`Item` → `Variant`), an `enum`, a string `id` with `pattern`, and a recursive `{teks, sub[]}` note tree. `additionalProperties: false` throughout. |
| `example.json` | A minimal instance that validates cleanly against the schema (note the empty `notes: []` for "present but empty"). |

Verify:
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_json.py" \
  "${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/references/examples/example.schema.json" \
  "${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/references/examples/example.json"
```
Your own schema and reports should *resemble these in structure and rigor* while reflecting your table.
