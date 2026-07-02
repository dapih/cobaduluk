<!--
TEMPLATE: post-conversion data-quality report.
Copy to output/<job-id>/data-quality-<job-id>.md and fill in.
Source the findings table from skills/excel-to-json/scripts/dq_check.py output, then interpret each
one (root cause + recommendation). Recommendations are PROPOSED, not applied -
apply only after user confirmation.
Severity: ERROR (blocks correctness) | WARN (review) | INFO (advisory).
-->
# Data-Quality Report: {{job_id}}

**Instance:** {{instance_file}}
**Schema:** {{schema_file}}
**Top-level entries:** {{entry_count}}
**Schema validation:** {{validation_status}}  <!-- PASSED (0 errors) | N errors -->
**Source rows accounted for:** {{rows_in}} in -> {{entries_out}} out  <!-- prove no row dropped -->
**Generated:** {{datetime}}

---

## Summary

| Severity | Category | Issues | Scope | Status / Recommendation |
|---|---|---|---|---|
| {{sev}} | {{category}} | {{count}} | {{scope}} | {{recommendation}} |

---

## Open issues

### {{SEV}} — {{category}} ({{count}})
**Where:** {{paths_or_entries}}
**Root cause:** {{cause}}
**Example:**
```
{{example}}
```
**Recommended fix:** {{fix}}

<!-- repeat per category -->

---

## Recommendations (proposed - apply only after confirmation)

1. **Placeholder -> empty:** replace `"-"` / `" "` values with empty string / empty array. Affected: {{where}}.
2. **Whitespace / hyphenation:** {{detail}}.
3. **Type / consistency:** {{detail}}.
4. **Schema improvement:** {{detail}}.

---

## Resolved since last run
- ~~{{category}}~~ {{before}} -> {{after}} ({{how}})

---

## Observations
1. {{observation}}
