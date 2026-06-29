# Bug: Duplicate `AleExperimentFilter` rows on experiment re-upload break the filter page #72

## Summary

When a user customizes their per-experiment filter and the experiment is later **re-uploaded**, the upload code creates a **second** `AleExperimentFilter` row for the same experiment. Subsequent visits to `/filter/?ale_experiment_id=<id>` then raise `MultipleObjectsReturned`, which renders the "Page not available" error template (HTTP 200, ~2.5 KB body).

Reported by a colleague on 2026-05-12 for `ale_experiment_id=2658`. The duplicate row was removed manually via Django admin, but the same failure mode is currently latent for 6 other experiments.

---

## Cause

`AleExperimentFilter.ale_experiment` has **no unique constraint** (`filter/models.py:23`), so multiple rows for the same experiment can coexist.

Two places in `builder/ale_experiment.py` use `get_or_create` incorrectly:

```python
# builder/ale_experiment.py:351-352  and  461-462
default_filter_params = filter.models.get_default_experiment_filter_params(experiment)
AleExperimentFilter.objects.get_or_create(**default_filter_params)
```

Because the default params dict is `**`-unpacked into kwargs, **every default value becomes part of the lookup**:

```sql
SELECT * FROM AleExperimentFilter
 WHERE ale_experiment_id = 2658
   AND ignored_genes = ''
   AND ignored_mutations = ''
   AND min_cutoff = 20
   AND max_cutoff = 100
   AND ...
```

On re-upload, if the user had already customized any field (e.g. `ignored_genes != ''`), this `SELECT` returns 0 rows and `get_or_create` happily inserts a fresh defaults-valued row — leaving the experiment with two filter rows.

The view at `filter/views/ale_exp_filter.py:30` then does `AleExperimentFilter.objects.get_or_create(ale_experiment=experiment, ...)`, which raises `MultipleObjectsReturned`. The exception is caught and rendered as "Page not available".

The correct `get_or_create` pattern is already used at `builder/upload.py:287-289`:

```python
exp_filter, created = AleExperimentFilter.objects.get_or_create(
    ale_experiment=experiment,
    defaults=filter.models.get_default_experiment_filter_params(experiment))
```

Only the identifying field (`ale_experiment`) is in the lookup; everything else goes through `defaults=`, which is used only on insert.

---

## Existing duplicates to clean up

6 experiments currently have 2 `AleExperimentFilter` rows. In every case the lower `id` row holds the user's customizations; the higher `id` row is the duplicate created by re-upload (and for `ale_id=1849` is byte-identical to the original). Delete the higher `id` row in each pair:

| ale_experiment_id | Experiment name | Project | Keep (id) | Delete (id) |
|---|---|---|---|---|
| 1532 | KO7-s | Bsubtilis M9 Glucose | 1343 | 1376 |
| 1533 | BS168 | Bsubtilis M9 Glucose | 1344 | 1377 |
| 1846 | KT2440_TALE | Putida_Acetate_2021 | 1677 | 2308 |
| 1849 | KT2440_ALE | Putida_Acetate_2021 | 1680 | 2309 |
| 2520 | P_putida_HGL1175_ISEScan | Butylamine ALE | 2375 | 2383 |
| 2521 | P_putida_KT2440_ISESCan | Butylamine ALE | 2376 | 2385 |

`ale_id=2658` was the original report; its duplicate has already been removed.

---

## Suggested code change

Fix both call sites in `builder/ale_experiment.py` to use the `defaults=` form, matching the pattern in `builder/upload.py:287`:

```python
# builder/ale_experiment.py:351-352  →
AleExperimentFilter.objects.get_or_create(
    ale_experiment=experiment,
    defaults=filter.models.get_default_experiment_filter_params(experiment))

# builder/ale_experiment.py:461-462  →  (same change)
```

This stops new duplicates from being created on re-upload. The fix is functionally backward-compatible — first-time uploads still create the default row; re-uploads now find the existing row (regardless of customizations) and leave it alone.

---

## Suggested schema change

Add a `unique=True` constraint on `AleExperimentFilter.ale_experiment` so the invariant is enforced at the database level. A future code mistake would then raise `IntegrityError` immediately rather than silently corrupting data.

```python
# filter/models.py
class AleExperimentFilter(models.Model):
    ale_experiment = models.ForeignKey(AleExperiment, on_delete=models.CASCADE, unique=True)
    ...
```

This requires a data migration that:
1. Deletes the 6 duplicate rows listed above (or merges them via a configurable rule — keep lowest `id`).
2. Adds the unique constraint.

The migration must run **after** the code fix is deployed, otherwise an in-flight re-upload could re-introduce a duplicate between the dedupe step and the constraint step.

---

## Behavior if all filter rows were deleted by mistake

For reference — deleting `AleExperimentFilter` rows is **not catastrophic**:

- `/filter/` page and the "Add to filter" button auto-recreate a defaults row via `get_or_create`.
- The central filtering logic at `filter/util.py:25-32` uses `.filter(...)`, which returns an empty queryset and applies no experiment-level filtering — mutation/converge/fixation pages just show un-filtered data.
- No 500 errors.

But **user customizations are lost** (cutoffs, `ignored_mutations`, `ignored_genes`), and `starting_strain_mutations` is lost too — the latter is only recoverable by re-uploading the wild-type sample.

---

## Timeline

| Date | Event |
|---|---|
| Unknown | `builder/ale_experiment.py` introduced with the wrong `get_or_create` pattern at two call sites |
| 2026-05-12 16:45 UTC | User hits `MultipleObjectsReturned` on `/filter/?ale_experiment_id=2658` |
| 2026-05-12 17:44 UTC | Duplicate row manually deleted; filter page renders normally |
| 2026-05-13 | Audit finds 6 other experiments with latent duplicate filter rows |

---

## Related

This bug concerns the **per-experiment (local) filter** (`AleExperimentFilter`).
For the separate **global** filter issue (an orphaned `GlobalFilter` hiding
mutations with no management UI), see
[ISSUE_1_orphaned_global_filter.md](ISSUE_1_orphaned_global_filter.md).
