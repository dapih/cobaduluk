# JSON Schema design (Draft 2020-12)

How to author `<job>.schema.json`. The schema is the contract the instance must satisfy and the spec the parser targets. Keep it strict enough to catch real errors, loose enough to admit legitimate source variation.

## Skeleton

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:id:<job-id>",
  "title": "<human title>",
  "type": "object",
  "required": ["<top-level fields>"],
  "additionalProperties": false,
  "properties": { "...": {} },
  "$defs": { "...": {} }
}
```

- Use `$defs` + `$ref` for every repeated object shape (one per hierarchy level). It keeps the schema DRY and the instance self-describing.
- Set `"additionalProperties": false` on every object once the shape is known — it turns "parser emitted an unexpected key" into a loud validation error instead of silent drift.
- Mark a field `required` only if it is truly always present in the source. Over-requiring forces the parser to invent data.

## Recursive structures

For arbitrarily deep numbered lists, define a self-referential item:

```json
"$defs": {
  "Item": {
    "type": "object",
    "required": ["teks"],
    "additionalProperties": false,
    "properties": {
      "teks": { "type": "string", "minLength": 1 },
      "sub":  { "type": "array", "items": { "$ref": "#/$defs/Item" } }
    }
  }
}
```

This matches `nest_by_pattern`'s `{teks, sub[]}` output. Make `sub` optional (omitted when there are no children) rather than requiring an empty array.

## Enums vs open strings

- Use `enum` when the column has a **small, closed, known** set of values (the inspect report's "distinct" count is tiny and stable). Enums catch typos and normalization gaps immediately.
- Keep an open `"type": "string"` (optionally `minLength: 1`) for free text.
- If an enum is *probably* closed but you're unsure, start open and tighten later — a too-strict enum produces validation errors that look like parser bugs. Record candidate enums in the schema-summary so they can be promoted after review.

## Nullable and empty

- Nullable: `"type": ["string", "null"]`. Add `null` to the `enum` list too if the field is an enum. Use null for "genuinely absent in source", not for "empty".
- Empty collections: prefer `[]` and `""` over null for "present but empty", and be consistent (pick one convention per field; the DQ `empty_vs_null` check flags mixing).

## Codes and identifiers

Numbers that are identifiers (codes, IDs, postal codes) belong as **strings**, to preserve leading zeros and prevent arithmetic:

```json
"code": { "type": "string", "pattern": "^[0-9]+$", "minLength": 1 }
```

Note in the schema-summary when a code's length is inconsistent in the source (e.g. mixed 4- and 5-digit) — that is a data observation, not necessarily an error to "fix".

## Constraints worth adding

- `minItems` on arrays that must be non-empty.
- `minLength: 1` on strings that must not be blank.
- `pattern` for structured codes/dates.
- `const` for a fixed banner/title value.

## Validate the schema itself

`validate_json.py` runs `Draft202012Validator.check_schema()` before validating the instance, so a malformed schema is reported as a schema error (exit 2), not a confusing instance error. Always run it once after authoring.

## Two-way fixes

When the instance fails validation, the cause is **either** the parser **or** the schema. Decide deliberately:
- Parser wrong → the source clearly means X but the parser emitted Y. Fix the parser.
- Schema wrong → the source legitimately contains a value the schema forbids. Loosen the schema (and note why).
Never "fix" validation by deleting source data.
