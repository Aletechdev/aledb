# Bug: Orphaned global filter hiding mutations, null `feature_length`, and duplicate records

## Summary

An orphaned global filter is actively hiding 11,697 observed mutations across 32 experiments with no UI to manage it. Separately, mutations uploaded before March 2021 have `feature_length=None`, and the resulting mismatch in `get_or_create` has created duplicate mutation records.

---

## Priority 1 — Orphaned global filter (Problem 1)

**Quick fix — no data migration needed.**

A global filter (`GlobalFilter` id=1) contains 105 ignored mutation IDs, including 3 `NC_000913` mutations (ids: 1120627, 1120634, 1120640) from the pre-2021 upload. This filter hides **11,697 observed mutations across 32 experiments**.

The global filter UI was disabled on November 22, 2021 (commit `5b466de` by muyao), but the backend filter logic still runs on every page load. There is no UI to view or manage the ignored mutations list. **The filter has been frozen since late 2021** — 53% of all experiments (558 of 1,054) were uploaded after the UI was disabled, with no global filter review applied to any of them.

- **Nav link:** commented out in `templates/base.html:104`
- **Mutation table button:** commented out in `seq/views/mutation_table_builder.py:36`
- **Backend endpoint:** still functional at `/mutations/add_to_global_filter`
- **Filter logic:** still active in `filter/util.py:30-32`
- **All 105 mutation IDs** fall in the range 1,120,627 – 1,664,812 (31–47% through the current DB; latest mutation ID is 3,531,070)
- **No new entries** have been added since the UI was disabled

### Global filter breakdown

| Reference | Count | Organism |
|---|---|---|
| LCTV02000* | 98 | *P. putida* |
| NC_000913 | 3 | *E. coli* MG1655 |
| AP009048 | 1 | *E. coli* W3110 |
| CP006881 | 1 | Other |
| Deleted | 1 | Unknown |

The *P. putida* mutations may have been intentionally filtered as reference artifacts. The *E. coli* mutations appear to be collateral damage.

### Suggested fixes for Problem 1

Rather than removing the existing global filter data (which was intentionally set up by the original team), add **toggle controls** to the mutations table:

1. **Add a "Show/Hide Global Filter" toggle**: Allow users to temporarily show mutations hidden by the global filter, so they can verify what's being filtered without permanently changing the filter
2. **Add a "Show/Hide Experiment Filter" toggle**: Same for per-experiment filters — let users see the full unfiltered view when needed
3. **Document the global filter contents**: Provide a way to view which mutations are in the global filter (e.g., restore the nav link or add a read-only admin page)

#### Affected code
- `filter/util.py:30-32` — global filter exclusion logic still active
- `seq/views/mutation_table_builder.py:36` — global filter button commented out
- `templates/base.html:104` — global filter nav link commented out

### Export with filter info (new feature)

Rather than only exporting the filtered (visible) mutations, add an **"Unfiltered Mutations"** export option on the experiments page (`/ale/experiments/`) that includes all mutations with extra columns showing their filter status.

4. **Add "Unfiltered Mutations" export button**: New button in the Export dropdown on the experiments page, alongside the existing Mutations/Converged/Fixed/Metadata options
5. **Add filter status columns to CSV**: The unfiltered export should include two additional columns beyond the standard CSV:
   - `global_filtered` — `TRUE` if the mutation is in the GlobalFilter ignored list, blank otherwise
   - `experiment_filtered` — `TRUE` if the mutation is in the AleExperimentFilter ignored list for that experiment, blank otherwise
6. **Skip filtering in export pipeline**: The new export path should bypass `filter_observed_mutations()` and instead query all observed mutations directly, then annotate each row with filter status

#### Files to modify
- `templates/ale/experiment_datatables.js` — Add new button that calls `export_data(table, 'unfiltered_mut')`
- `export/views.py` — Pass `mut_type_str` through to `get_csv_str()` (no changes needed, already passes the string)
- `export/util.py` — Handle `unfiltered_mut` type: skip `filter_observed_mutations()`, load global and experiment filter ignored mutation lists, add `global_filtered` and `experiment_filtered` columns to each CSV row

#### Current export flow (for reference)
1. JS collects selected experiment IDs → GET `/export?experiment_ids=...&mut_type=mut`
2. `export/views.py:export()` loops experiments, calls `get_csv_str(exp_id, mut_type_str)` per experiment
3. `export/util.py:get_csv_str()` calls `filter_observed_mutations()` which excludes global + experiment filtered mutations
4. CSV rows are built from the filtered mutation list — filtered mutations are invisible in the export

### Documentation
7. **Database access documentation**: Document how to query and manage filters via the Django shell for administrators

---

## Priority 2 — Data issues (Problems 2 & 3)

**Requires manual data curation — separate issues to be created.**

### Problem 2: `feature_length=None` on pre-2021 mutations

Before commit `2b434ea`, `builder/upload.py` did not include `feature_length` in the `Mutation.objects.get_or_create()` call. All mutations uploaded before that date have `feature_length=None`, even though the size information was correctly parsed and stored in `sequence_change` as a display string (e.g., "Δ5,481 bp").

**Example:** Mutation id=1120634
- `position=3362162`, `mutation_type=DEL`, `reseq_reference=NC_000913`
- `feature_length=None` (should be `5481`)
- `sequence_change="Δ5,481 bp"` (display value is correct)

**Impact:** Any code querying `Mutation.feature_length` for programmatic analysis or export gets `None` instead of the actual size.

**Fix:** Backfill `feature_length` — write a migration script to populate `feature_length` from `sequence_change` (parse "Δ5,481 bp" → 5481) for all mutations where `feature_length=None` and `mutation_type` is in `[DEL, SUB, INV, AMP, CON]`

### Problem 3: Duplicate mutation records

Because `get_or_create` uses all fields for matching, the same biological mutation exists as two separate database records:

| Field | Old record (id=1120634) | New record (id=1933880) |
|---|---|---|
| position | 3362162 | 3362162 |
| mutation_type | DEL | DEL |
| feature_length | **None** | **5481** |
| gene | [yhcA],yhcD,yhcE,insH-10,yhcE,[yhcF] | same |
| sequence_change | Δ5,481 bp | same |
| reseq_reference | NC_000913 | same |

Observed mutations from older uploads link to the old record; newer uploads link to the new record. This splits what should be a single mutation across two IDs, affecting convergence analysis, fixation detection, and any cross-experiment comparisons.

**Fix:** After backfilling `feature_length` (Problem 2), identify and merge duplicate mutation records, reassigning observed mutations to the canonical record.

#### Affected code
- `builder/upload.py:237-244` — `get_or_create` with `feature_length` causes duplicates when matching against pre-2021 records

---

## Timeline

| Date | Event |
|---|---|
| 2016-08-16 | Global filter feature added (dgosting) |
| Pre-2021 | Experiment 748 and others uploaded without `feature_length` |
| 2017-11-10 | Global filter button restricted to admins (Kai Chen) |
| Before 2021-11-22 | 105 mutations added to global filter |
| 2021-03-24 | `feature_length` added to `upload.py` (muyao, commit `2b434ea`) |
| 2021-11-22 | Global filter UI disabled (muyao, commit `5b466de`) |
| Present | Filter still active, hiding data with no management UI |
