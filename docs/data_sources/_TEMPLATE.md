# Data card: <source_id>

Every field is filled from evidence (query, file, saved page), never from memory (CLAUDE.md §5).

## Identity
- id:
- name / provider:
- landing page:
- exact endpoint / URL pattern:

## Licence
- licence name + URL:
- verbatim snapshot: `docs/references/licences/<file>` (read on YYYY-MM-DD)
- required attribution string:

## Challenge eligibility
- basis (organizer ruling date + location, or prize-rule text):

## Coverage
- requested (stations / grid / period incl. margins):
- measured per airport-month: `reports/checks/<file>`

## Retrieval
- script: `scripts/fetch/<source_id>.py`
- command + parameters:
- retrieved at (UTC):
- tool + library versions:

## Files
- listed in `data/external/MANIFEST.csv` (path, bytes, SHA256, retrieved_at)

## Schema
- raw columns, units, time zone, missing markers — each verified by `reports/checks/<file>`

## Lineage
- `raw_<id>` → `stg_<id>` → `clean_<id>` → `feat_<id>`; SQL files:

## Quality
- checks run, outputs, known issues:

## Value
- features derived; experiments that measured them (kept and rejected):

## Re-fetch policy
- checksum mismatch → stop and report, never overwrite silently.
