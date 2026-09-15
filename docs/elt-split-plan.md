# Plan: robust upload in three steps (ELT split, test harness, idempotent re-upload)

Status: **planned, not implemented** (2026-09-15, revised the same day). Covers roadmap
items §8.1 and §8.2 in `docs/pipeline-upload-roadmap.md`.

## Design decision

The single recovery action for any upload problem is **re-upload**, and the upload itself
is made safe to repeat: it loads what is missing, skips what is loaded, re-applies metadata,
rebuilds the experiment's derived data, and reports. No separate "replay" or "check" tools
for operators; those exist only as functions the upload calls. Whole-database aggregates
leave the upload entirely and run on a schedule.

Kept deliberately small. Rejected as unnecessary: a per-sample load ledger table (per-sample
transactions make "sample record exists" a sufficient completeness test), a standalone
completeness command as a deliverable, a user-facing transform-replay command.

## Step 1 — ELT split (half a day, independent of the rest)

Move the whole-database count rebuild out of the ingest.

1. `builder/ale_experiment.py`: add
   ```python
   def rebuild_experiment_derived_data(ale_experiment_id):
       """Per-experiment transforms. Safe to re-run; touches only this experiment."""
       rebuild_converge_mutations(ale_experiment_id)
       rebuild_fixated_mutations(ale_experiment_id)
       generate_static_data(ale_experiment_id)
   ```
   and call it from `create_ale_experiment` / `create_ensemble_ale_experiment` in place of
   the inline block. Remove `rebuild_dashboard_data()` from all four call sites (the two
   ingest functions, `delete_ale_experiments`, `insert_starting_strain_flask`) and its
   import.
2. Remove `clear_dashboard_cache()` and its six call sites (`builder/ale_experiment.py`,
   `filter/views/ale_exp_filter.py`, `filter/views/global_filter.py`, helper in
   `common/util.py`): the cache setters were deleted in 2017 (commit 7df1428e); nothing
   reads those keys.
3. `ale/management/commands/rebuild_stats.py`: add `help` and a timing print.
4. `pipeline/upload_scripts/webapp-upload.sh`: after the ingest has exited and
   `report_status` has run, a separate step:
   ```bash
   step "refreshing home-page counts (separate process; failure does not affect the run)"
   sudo docker exec aledb-web python manage.py rebuild_stats --skip-checks \
       || step "count refresh FAILED; nightly cron will retry"
   ```
5. Root crontab on the VM host (first scheduler on this box; note it in
   `pipeline/upload_scripts/README.md`):
   ```
   15 3 * * * docker exec aledb-web python manage.py rebuild_stats --skip-checks >> /upload/logs/rebuild_stats.log 2>&1
   ```
   Home-page totals may lag a data change by up to a day; deletions and repairs no longer
   refresh them inline.

Verification: `py_compile`; `manage.py test builder dashboard filter` shows the same 9
pre-existing builder failures and nothing new (no test depends on the ingest doing the
global rebuild); `rebuild_stats` standalone gives unchanged totals, record its duration;
one dev upload through the webapp reaches `uploaded` with the count step logged after the
status report; run the cron line by hand once.

## Step 2 — Builder test harness (half a day, prerequisite for step 3)

The ingest module (`builder/ale_experiment.py`, `builder/upload.py`) is where the risk is:
two near-identical long functions, exceptions swallowed at several levels. Do not change
its transaction boundaries without tests that exercise it.

1. `builder/tests/test_upload.py`: the four `test_add_breseq_results_*` errors are a
   missing fixture (a `TechnicalReplicate` with id 1); create the ALE/flask/isolate/
   replicate chain in `setUp`. The two `test_get_mutation_freq_*` failures expect a scalar;
   `_get_mutation_freq` has returned `[frequency, frequency_gatk]` since 2021 — update the
   expected values.
2. `builder/tests/test_ale_experiment.py`: `test_create_ALE_experiment`,
   `test_upload_ALE_collection`, `test_reseq_URL` get 0 mutations from a 27-mutation
   fixture with no exception logged. Find why (evidence-free `.gd`, parser drift since
   2021) and either fix the ingest edge case or refresh the fixture. Add a `metadata/`
   folder to the fixtures so the metadata step no longer logs a FileNotFoundError.
3. Add the tests step 3 needs: upload the same fixture twice → identical row counts and
   one sample record per sample; a sample that fails mid-way leaves no partial rows.

Target: `manage.py test builder` green, so step 3 has a real harness.

## Step 3 — Idempotent upload + Re-upload button (1–2 days)

1. **One transaction per sample.** In the sample loop, wrap the creation of the
   isolate/replicate/sample records and the `bulk_create` of their rows in
   `transaction.atomic()`. A sample then either exists completely or not at all.
2. **Skip loaded samples.** Before loading a sample, look up its sample record by
   experiment + ALE, flask, isolate, replicate numbers. Found → skip and print "already
   loaded". Not found → load. Print "loaded N, skipped K, failed F of M samples" per
   experiment; any failure keeps the non-zero exit the upload command already has.
3. **Stable identity.** Restrict the isolate/replicate `get_or_create` lookups to the
   identity numbers (move date/person/description to `defaults=`), so a re-run cannot mint
   a second sample record (the 2674 duplicate-sample case).
4. **Unique constraint** on `seq_observedmutation (sequencing_experiment_id, mutation_id)`
   as the backstop, applied by a tracked SQL script in `docs/operations/` (migrations are
   gitignored here). Prerequisite: the split-row ingest quirk (roadmap §8.8a) fixed and the
   13 remaining split rows merged; and the mode-1 dedupe of the remaining experiments
   (roadmap §9 step 1) done, otherwise the constraint cannot be created.
5. **Metadata and derived data run every time** (already idempotent: media get-or-create
   + field overwrite; delete-then-rebuild per experiment).
6. **Re-upload button.** `pipeline/views.py` `upload`: keep the "already uploading" guard;
   turn the `uploaded` and `error` states into a confirmation ("re-upload: loads missing
   samples, re-applies metadata, rebuilds derived data") instead of a refusal; add the
   ownership check. `run.html`: the error-state copy changes from "you can retry" to what
   re-upload actually does.
7. **Explicit replace path** (operator only, not a button): a management command that
   deletes one sample record and its rows so the next upload reloads it — for a sample
   that loaded completely but from a bad archive. Deliberate, logged, never automatic.

Verification: the step-2 tests; on prod, re-upload of the dev run (queued for cleanup) is
a no-op that reports all samples skipped and leaves row counts unchanged; then delete one
of its samples with the replace command and re-upload → exactly that sample reloads.

## Deploy order and rollback

Each step is one commit, user pushes; host script by `sudo cp` with a dated backup; the
web container restart is user-run (Python changed); the cron line is installed by the
operator. Rollback per step: `git revert` + restart, restore the script backup, remove the
cron line; drop the unique constraint if step 3 has to be reverted. Count tables and
derived tables are rebuildable at any time, so no data is at risk in either direction.

## Investigation notes (2026-09-15)

- Home page reads the count tables directly; no cache in the read path. `cache_table`
  holds one fossil dashboard key from 2017 that nothing reads.
- `rebuild_dashboard_data()` call sites: the two ingest functions, `delete_ale_experiments`,
  `insert_starting_strain_flask`.
- The sample loop catches a failed sample, prints the traceback and continues; the
  experiment still returns success. Partial loads are silent today.
- No scheduler exists on the host (no cron entries, no celery/rq); Redis serves channels.
