# Duplicate mutation records caused by `feature_length` mismatch in `get_or_create`

## Summary

Because `Mutation.objects.get_or_create()` uses all fields for matching — including `feature_length` — the same biological mutation can exist as two separate database records: one with `feature_length=None` (pre-2021 upload) and one with the correct value (post-2021 upload).

## Example

| Field | Old record (id=1120634) | New record (id=1933880) |
|---|---|---|
| position | 3362162 | 3362162 |
| mutation_type | DEL | DEL |
| feature_length | **None** | **5481** |
| gene | [yhcA],yhcD,yhcE,insH-10,yhcE,[yhcF] | same |
| sequence_change | Δ5,481 bp | same |
| reseq_reference | NC_000913 | same |

## Impact

Observed mutations from older uploads link to the old record; newer uploads link to the new record. This splits what should be a single mutation across two IDs, affecting:
- Convergence analysis
- Fixation detection
- Cross-experiment comparisons

## Suggested fix

**Depends on Issue 2** (`feature_length` backfill). After backfilling, identify and merge duplicate mutation records, reassigning observed mutations to the canonical record.

## Affected code

- `builder/upload.py:237-244` — `get_or_create` with `feature_length` causes duplicates when matching against pre-2021 records
