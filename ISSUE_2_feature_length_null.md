# Pre-2021 mutations have null `feature_length` despite correct `sequence_change` values

## Summary

Before commit `2b434ea` (March 24, 2021), `builder/upload.py` did not include `feature_length` in the `Mutation.objects.get_or_create()` call. All mutations uploaded before that date have `feature_length=None`, even though the size information was correctly parsed and stored in `sequence_change` as a display string (e.g., "Δ5,481 bp").

## Example

Mutation id=1120634:
- `position=3362162`, `mutation_type=DEL`, `reseq_reference=NC_000913`
- `feature_length=None` (should be `5481`)
- `sequence_change="Δ5,481 bp"` (display value is correct)

## Impact

Any code querying `Mutation.feature_length` for programmatic analysis or export gets `None` instead of the actual size. This affects DEL, SUB, AMP, CON, and INV mutation types.

## Suggested fix

**Backfill `feature_length`** — write a migration script to populate `feature_length` from `sequence_change` (parse "Δ5,481 bp" → 5481) for all mutations where `feature_length=None` and `mutation_type` is in `[DEL, SUB, INV, AMP, CON]`.

## Affected code

- `builder/upload.py:237-244` — `get_or_create` includes `feature_length` since commit `2b434ea`

## Timeline

| Date | Event |
|---|---|
| Pre-2021 | Experiments uploaded without `feature_length` |
| 2021-03-24 | `feature_length` added to `upload.py` (muyao, commit `2b434ea`) |
