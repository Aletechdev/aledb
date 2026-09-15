# Plan: take the global dashboard rebuild out of the ingest (ELT split)

Status: **planned, not implemented** (2026-09-15). Roadmap item §8.2 in
`docs/pipeline-upload-roadmap.md`. Investigation notes at the end.

## Goal

An upload (load) must be cheap, scoped to its experiment, and independent of the size
of the rest of the database. Per-experiment derived data (transform, scoped) stays with
the upload but becomes replayable on its own. Whole-database aggregates (transform,
global) run as their own scheduled process.

## Scope

In: `builder/ale_experiment.py`, one new management command, `rebuild_stats` polish,
`pipeline/upload_scripts/webapp-upload.sh`, one host cron line, dead cache helper
removal, docs. Out: idempotent ingest / unique constraint (roadmap §8.1), the streaming
rewrite of anything beyond what is already done, the Stats page.

## Steps

### 1. Code — `builder/ale_experiment.py`

1. Add
   ```python
   def rebuild_experiment_derived_data(ale_experiment_id):
       """Per-experiment transforms. Safe to re-run; touches only this experiment."""
       rebuild_converge_mutations(ale_experiment_id)
       rebuild_fixated_mutations(ale_experiment_id)
       generate_static_data(ale_experiment_id)
   ```
   next to the existing `rebuild_all_*` helpers.
2. In `create_ale_experiment` and `create_ensemble_ale_experiment`, replace the three
   per-experiment rebuild calls + `rebuild_dashboard_data()` with one call to the helper.
   Keep the progress prints inside the helper.
3. Remove `rebuild_dashboard_data()` from the two other call sites:
   `delete_ale_experiments` (end of the delete; this is part of why a delete takes ~25
   min) and `insert_starting_strain_flask`. Drop the import.
4. Remove `clear_dashboard_cache()` calls (4 in this file, 2 in
   `filter/views/ale_exp_filter.py` and `filter/views/global_filter.py`) and the helper in
   `common/util.py`: its setters were deleted in 2017 (commit 7df1428e), nothing reads
   those keys, the TODOs already say to remove it.

### 2. New command — `ale/management/commands/rebuild_experiment.py`

`manage.py rebuild_experiment <experiment id ...>`: validates ids, calls
`rebuild_experiment_derived_data` per id, prints per-step progress. This is the replay
path when a transform fails or after a data repair (dedupe, isolate deletion, filter
change), instead of re-uploading.

### 3. `rebuild_stats` — `ale/management/commands/rebuild_stats.py`

Add a `help` string and a timing print. No behavioural change; it already calls
`rebuild_dashboard_data()`, which (after commit ebf703ce) streams and peaks ~0.4 GB.

### 4. Host script — `pipeline/upload_scripts/webapp-upload.sh`

After the ingest has exited and `report_status` has run, add a separate step:
```bash
step "refreshing home-page counts (separate process; failure does not affect the run)"
sudo docker exec aledb-web python manage.py rebuild_stats --skip-checks \
    || step "count refresh FAILED; nightly cron will retry"
```
The run status never depends on it. Deploy with the usual `sudo cp` to `/upload/`
(backup `/upload/webapp-upload.sh.bak-<date>`).

### 5. Nightly safety net — root crontab on the VM host

```
15 3 * * * docker exec aledb-web python manage.py rebuild_stats --skip-checks >> /upload/logs/rebuild_stats.log 2>&1
```
First scheduler on this host; note it in `pipeline/upload_scripts/README.md`. Home-page
totals may lag a data change by up to a day; deletions and repairs no longer refresh
them inline.

### 6. Docs

Tick roadmap §8.2; update `pipeline/upload_scripts/README.md` (new step, cron, replay
command); add a line to `docs/ISSUE_upload_metadata_skipped_on_oom.md` (fix 2 now
structurally closed: the ingest no longer touches the whole table).

## Verification

1. `python -m py_compile` on touched files; `manage.py test builder dashboard filter`
   must show the same 9 pre-existing builder failures and nothing new (no test depends
   on the ingest doing the global rebuild — checked).
2. `manage.py rebuild_experiment 2674` on prod: convergence / fixation / static-data row
   counts identical before and after (they are set-based; expected 6 / 1 / 1 rows).
3. `manage.py rebuild_stats` standalone: totals unchanged from the last run; record the
   duration.
4. End-to-end: one dev upload through the webapp (reuse the dev run that is queued for
   cleanup, or a fresh small one): run reaches `uploaded`, per-experiment tables built,
   ingest peak memory well under 1 GB, count refresh step logged after `report_status`.
5. Cron: run the line by hand once as root, check the log file, then let it fire.

## Deploy order

1. Merge code + docs (one commit), user pushes.
2. `sudo cp` the host script; user restarts the web container (Python changed).
3. Install the cron line (needs root; operator does it or approves it).
4. Run verification steps 2–5.

## Rollback

`git revert` the commit and restart the container; restore
`/upload/webapp-upload.sh.bak-<date>`; remove the cron line. The count tables are
rebuildable at any time, so no data is at risk in either direction.

## Investigation notes (2026-09-15)

- Home page reads `ObservedMutationCounts`, `UniqueMutationCounts`, `SampleCounts`
  directly; no cache in the read path. `CACHES` is the DB backend; `cache_table` holds one
  fossil dashboard key from 2017 that nothing reads.
- `rebuild_dashboard_data()` call sites: the two ingest functions, `delete_ale_experiments`,
  `insert_starting_strain_flask`.
- Tests touching the count tables call the rebuild functions directly; ingest tests assert
  per-experiment static data only.
- No scheduler exists on the host (no cron entries, no celery/rq). Redis is used for
  channels, not tasks.
