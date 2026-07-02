<!--
TEMPLATE: human-readable schema documentation.
Copy to docs/<job-id>/<job-id>.schema-summary.md (or include inside summary).
Document every $def/object, its fields, types, constraints, enums, and the
source->canonical normalization rules the parser applies.
-->
# Schema Summary: {{title}}

**Source file:** {{source_file}}
**Schema file:** {{schema_file}}
**Standard:** JSON Schema Draft 2020-12
**Root type:** {{root_type}}

---

## Structure
```
{{structure_tree}}
```

---

## {{object_name}} (Level {{n}})
| Field | Type | Constraints / allowed values | Notes |
|---|---|---|---|
| `{{field}}` | {{type}} | {{constraints}} | {{notes}} |

<!-- repeat one block per object / $def -->

---

## Enumerations
| Field | Allowed values |
|---|---|
| `{{field}}` | {{enum_values}} |

---

## Normalization (source → canonical)
| Field | Raw value in Excel | Canonical value | Rule applied |
|---|---|---|---|
| {{field}} | {{raw}} | {{canonical}} | {{rule}} |

---

## Design notes
- {{note}}  <!-- e.g. why a code is a string, why a field allows null, etc. -->
