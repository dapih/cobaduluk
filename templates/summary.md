<!--
TEMPLATE: job summary. Copy to output/<job-id>/summary-<job-id>.md and fill in.
The single document a reader opens first. MUST include the field<->column mapping
(workflow guideline #7) and plain-language descriptions of both the table and the
schema.
-->
# Summary: {{job_id}}

**Source:** {{source_file}} (sheet `{{sheet}}`)
**Schema:** {{schema_file}}
**Instance:** {{instance_file}}
**Validation:** {{validation_status}}
**Generated:** {{datetime}}

---

## What this table is
{{table_description}}

## Schema in brief
{{schema_description}}

## Structure (hierarchy)
```
{{structure_tree}}
```

## Field ↔ column mapping
| JSON field (path) | Excel column | Group / sub-group | Transform | Notes |
|---|---|---|---|---|
| {{json_path}} | {{col}} | {{group}} | {{transform}} | {{notes}} |

## Statistics
| Metric | Value |
|---|---|
| Source rows | {{rows}} |
| Top-level entries | {{entries}} |
| {{level_2_label}} | {{n2}} |
| {{level_3_label}} | {{n3}} |
| Schema validation errors | {{errors}} |

## Data-quality headlines
- {{headline}}  <!-- see data-quality-{{job_id}}.md for the full report -->

## Files in this job
- `{{job_id}}.xlsx` — source table
- `{{job_id}}.schema.json` — JSON Schema (Draft 2020-12)
- `{{job_id}}.json` — generated instance
- `{{job_id}}.parser.py` — the generated parser (reproduces the instance)
- `log-{{job_id}}.md` · `data-quality-{{job_id}}.md` · `summary-{{job_id}}.md`
