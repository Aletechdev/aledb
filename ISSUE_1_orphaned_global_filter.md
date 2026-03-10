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
| LCTV02000* | 98 | *P. putida* |
| NC_000913 | 3 | *E. coli* MG1655 |
| AP009048 | 1 | *E. coli* W3110 |
| CP006881 | 1 | Other |
| Deleted | 1 | Unknown |

The *P. putida* mutations may have been intentionally filtered as reference artifacts. The *E. coli* mutations appear to be collateral damage.

## Suggested fixes

Rather than removing the existing global filter data (which was intentionally set up by the original team), add **toggle controls** to the mutations table:

1. **Add a "Show/Hide Global Filter" toggle**: Allow users to temporarily show mutations hidden by the global filter, so they can verify what's being filtered without permanently changing the filter
2. **Add a "Show/Hide Experiment Filter" toggle**: Same for per-experiment filters — let users see the full unfiltered view when needed
3. **Document the global filter contents**: Provide a way to view which mutations are in the global filter (e.g., restore the nav link or add a read-only admin page)
4. **Database access documentation**: Document how to query and manage filters via the Django shell for administrators

### Export with filter info (new feature)

Rather than only exporting the filtered (visible) mutations, add an **"Unfiltered Mutations"** export option on the experiments page (`/ale/experiments/`) that includes all mutations with extra columns showing their filter status.

5. **Add "Unfiltered Mutations" export button**: New button in the Export dropdown on the experiments page, alongside the existing Mutations/Converged/Fixed/Metadata options
6. **Add filter status columns to CSV**: The unfiltered export should include two additional columns beyond the standard CSV:
   - `global_filtered` — `TRUE` if the mutation is in the GlobalFilter ignored list, blank otherwise
   - `experiment_filtered` — `TRUE` if the mutation is in the AleExperimentFilter ignored list for that experiment, blank otherwise
7. **Skip filtering in export pipeline**: The new export path should bypass `filter_observed_mutations()` and instead query all observed mutations directly, then annotate each row with filter status

#### Files to modify
- `templates/ale/experiment_datatables.js` — Add new button that calls `export_data(table, 'unfiltered_mut')`
- `export/views.py` — Pass `mut_type_str` through to `get_csv_str()` (no changes needed, already passes the string)
- `export/util.py` — Handle `unfiltered_mut` type: skip `filter_observed_mutations()`, load global and experiment filter ignored mutation lists, add `global_filtered` and `experiment_filtered` columns to each CSV row

#### Current export flow (for reference)
1. JS collects selected experiment IDs → GET `/export?experiment_ids=...&mut_type=mut`
2. `export/views.py:export()` loops experiments, calls `get_csv_str(exp_id, mut_type_str)` per experiment
3. `export/util.py:get_csv_str()` calls `filter_observed_mutations()` which excludes global + experiment filtered mutations
4. CSV rows are built from the filtered mutation list — filtered mutations are invisible in the export

## Affected code

- `filter/util.py:30-32` — global filter exclusion logic still active
- `seq/views/mutation_table_builder.py:36` — global filter button commented out
- `templates/base.html:104` — global filter nav link commented out

## Timeline

| Date | Event |
|---|---|
| 2016-08-16 | Global filter feature added (dgosting) |
| 2017-11-10 | Global filter button restricted to admins (Kai Chen) |
| Before 2021-11-22 | 105 mutations added to global filter |
| 2021-11-22 | Global filter UI disabled (muyao, commit `5b466de`) |
| Present | Filter still active, hiding data with no management UI |
