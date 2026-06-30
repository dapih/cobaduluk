# excel-to-json

For Excel/xlsx → JSON tasks, **load skill `excel-to-json`** and follow [`workflows/full-pipeline.md`](../../workflows/full-pipeline.md).

- Skill: [`skills/excel-to-json/SKILL.md`](../../skills/excel-to-json/SKILL.md) (also at `.kilo/skills/excel-to-json/SKILL.md`)
- Plugin root: `python tools/excel-to-json/scripts/resolve_plugin_root.py` (or `EXCEL_TO_JSON_ROOT`)
- **Never** read the full `.xlsx` or `.json` into context — only the inspect report
- All gates in the workflow are mandatory unless the user explicitly skips them
