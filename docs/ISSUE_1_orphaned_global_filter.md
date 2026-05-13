# Orphaned global filter hiding 11,697 observed mutations across 32 experiments

## Summary

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
| LCTV02000* | 98 | *Rhodotorula toruloides* NBRC 0880 (WGS project LCTV, assembly v02) |
| NC_000913 | 3 | *E. coli* MG1655 |
| AP009048 | 1 | *E. coli* W3110 |
| CP006881 | 1 | Other |
| Deleted | 1 | Unknown |

The *R. toruloides* mutations may have been intentionally filtered as reference artifacts (LCTV is the NCBI WGS accession for the *R. toruloides* NBRC 0880 assembly — the same strain as IFO 0880 used in experiment 2664). The *E. coli* mutations appear to be collateral damage.

---

## Implementation plan

### Phase 1: Mutation table filter toggles

Add "Show Global Filtered" and "Show Experiment Filtered" toggle checkboxes to the mutations table page so users can temporarily see what is hidden.

#### Steps
1. **`filter/util.py`** — Add `skip_global_filter` and `skip_experiment_filter` optional boolean params to `filter_observed_mutations()`. When `skip_global_filter=True`, skip global filter mutation ID exclusion (lines 30-32) and global gene filter (lines 80-84). When `skip_experiment_filter=True`, skip experiment filter loop (lines 34-55) and experiment gene filter (lines 85-88). All existing callers are unaffected (defaults to `False`).
2. **`seq/util.py`** — Forward the new flags through `get_all_observed_mutations_filtered()`
3. **`seq/views/mutations.py`** — Read `?show_global_filtered=1` and `?show_exp_filtered=1` from GET params in `mutation_table()` and `amplification_data()`, pass through `_get_table_body()` to `get_all_observed_mutations_filtered()`
4. **`templates/base_table_template.html`** — Add two checkbox inputs in the existing form (alongside `ale_no`, `sample_type`, `tag_select`), submitted with the existing Apply button

#### Testing
Navigate to `/mutations/?ale_experiment_id=748 and https://aledb.org/filter/?ale_experiment_id=735`, toggle each checkbox, click Apply. Verify hidden mutations appear. With no toggles, behavior should be identical to current.

---

### Phase 2: Review global filter nav link and page

**Decision needed:** The global filter page (`/filter/global_filter/`) and nav link (`templates/base.html:104`) were disabled in Nov 2021. The existing view and template still work and have permission checks (non-admins cannot modify). Before restoring:

- Review if the global filter page UI is still appropriate or needs updates
- Decide whether to restore as read-only for all users, or keep admin-only
- Decide whether to also restore the "Add to Global Filter" button on mutation tables (`seq/views/mutation_table_builder.py:36`)

#### Steps (pending review)
1. **`templates/base.html:104`** — Uncomment the Global Filter nav link (one-line change)
2. Review `filter/views/` and `templates/filter/` for the global filter page — confirm it renders correctly and permissions are appropriate
3. Decide on the "Add to Global Filter" mutation table button — restore or keep disabled

---

### Phase 3: Documentation

Create admin documentation for managing filters via the Django shell.

#### Steps
1. Create `docs/filter_admin.md` covering:
   - How to list global filter contents: `from filter.util import get_global_filter; gf = get_global_filter(); print(gf.ignored_mutations)`
   - How to list experiment filters: `from filter.models import AleExperimentFilter; AleExperimentFilter.objects.all()`
   - How to add/remove mutation IDs from the global filter
   - How to check which experiments have custom filters

---

### Phase 4: Unfiltered export with filter status columns (depends on Phase 1)

Add an "Unfiltered Mutations" export option on the experiments page that includes all mutations with extra columns showing their filter status.

#### Steps
1. **`templates/ale/experiment_datatables.js`** — Add new button in the Export dropdown:
   ```javascript
   { text: 'Unfiltered Mutations', action: function () { export_data(table, 'unfiltered_mut'); } }
   ```
2. **`export/util.py`** — Handle `unfiltered_mut` type in `get_csv_str()`:
   - Get all mutations unfiltered (using `skip_global_filter=True, skip_experiment_filter=True` from Phase 1)
   - Get filtered mutations normally to compute what was removed
   - Annotate each row with `global_filtered` and `experiment_filtered` columns (`TRUE` or blank)
   - Add the two extra columns to the CSV header
3. **`export/views.py`** — No changes needed (already passes `mut_type_str` through)

#### Current export flow (for reference)
1. JS collects selected experiment IDs → GET `/export?experiment_ids=...&mut_type=mut`
2. `export/views.py:export()` loops experiments, calls `get_csv_str(exp_id, mut_type_str)` per experiment
3. `export/util.py:get_csv_str()` calls `filter_observed_mutations()` which excludes global + experiment filtered mutations
4. CSV rows are built from the filtered mutation list — filtered mutations are invisible in the export

#### Testing
Select experiments on `/ale/experiments/`, click Export > Unfiltered Mutations. Verify:
- All mutations appear (including previously hidden ones)
- `global_filtered` column shows `TRUE` for mutations in the global filter
- `experiment_filtered` column shows `TRUE` for experiment-filtered mutations
- Compare row count with regular Mutations export to confirm the difference

---

## Affected code

- `filter/util.py:14-93` — `filter_observed_mutations()`, global filter at lines 30-32
- `seq/util.py:13-15` — `get_all_observed_mutations_filtered()` wrapper
- `seq/views/mutations.py:76-125` — `mutation_table()` and `_get_table_body()`
- `seq/views/mutation_table_builder.py:36` — global filter button commented out
- `templates/base.html:104` — global filter nav link commented out
- `templates/base_table_template.html` — mutation table page template
- `templates/ale/experiment_datatables.js` — export dropdown buttons
- `export/util.py:14-46` — `get_csv_str()` export logic

## Timeline

| Date | Event |
|---|---|
| 2016-08-16 | Global filter feature added (dgosting) |
| 2017-11-10 | Global filter button restricted to admins (Kai Chen) |
| Before 2021-11-22 | 105 mutations added to global filter |
| 2021-11-22 | Global filter UI disabled (muyao, commit `5b466de`) |
| Present | Filter still active, hiding data with no management UI |
