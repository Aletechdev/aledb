# Bug (fixed): mutation details page returned 500 for any filtered mutation

**Status: fixed** in `evidence/views.py` (deployed 2026-08-24). This doc records
the root cause and the verification trail.

## Symptom

`/mutations/details?observed_mut_id=<id>` returned HTTP 500 whenever the
observed mutation's underlying `Mutation` was hidden by the **global filter**
or by the experiment's **local filter** (frequency cutoffs, ignored genes,
ignored mutations, or starting-strain mutations). Mutations visible in the
default table view rendered fine, so the breakage only surfaced when users
enabled "show global/experiment filtered" in the mutations table and clicked
through — e.g. `observed_mut_id=560533` (exp 262; a mutation listed in the
experiment filter's `starting_strain_mutations`).

## Root cause

`evidence.views.get_next_mutation()` built the experiment's mutation list with
`get_all_observed_mutations_filtered(experiment_id)` using the **default**
filter flags, then located the current mutation with `list.index()`:

```
ind = list_muts.index(current_mutation)   # ValueError if current is filtered out
```

A filtered-out mutation is, by definition, not in that list, so `.index()`
raised `ValueError`, which nothing caught, and the whole page 500ed. Every
globally- or experiment-filtered mutation in every experiment was affected.

## Fix

Wrap the `.index()` lookup in `try/except ValueError`. On the exception
(current mutation is hidden), fall back to scanning the already-built,
position-sorted visible list for the first mutation with a greater genome
position — so "next" navigation from a hidden mutation's page rejoins the
visible set. Zero additional queries; behavior for visible mutations is
unchanged.

## Verification

- `get_neighbor_ids()` exercised in `manage.py shell` for a visible mutation
  (unchanged result), for 560533 (previously `ValueError`, now returns
  neighbors), and for 560717 (same).
- Post-restart, `GET /mutations/details?observed_mut_id=560533` and `560717`
  return 200.
- Evidence files were confirmed present on disk for **all** observed
  mutations of the affected experiment, filtered and visible alike, so
  unhidden detail pages render real breseq evidence, not "N/A".

## Related

- [ISSUE_1_orphaned_global_filter.md](../ISSUE_1_orphaned_global_filter.md) —
  what the global filter hides (issue #47).
- [BUG_duplicate_ale_experiment_filter.md](../BUG_duplicate_ale_experiment_filter.md) —
  per-experiment filter duplication (issue #72).
- Pre-existing oddity, not addressed here: `get_neighbor_ids()` computes
  "prev" as the previous `ObservedMutation` **by id across the entire table**
  (not scoped to the experiment), and would `AttributeError` on the lowest id
  in the table. Harmless in practice; noted for any future rework of the
  neighbor navigation.
