# Pipeline upload: history, changes, and roadmap

_Living document. Started 2026-09-15 to record why the 2026-09-11 upload overhaul
was made, what it changed, and what is still open. Update the **Roadmap** section as
items land; append to **Timeline** rather than rewriting it._

Related write-ups (all under `docs/`):

- `ISSUE_upload_metadata_skipped_on_oom.md` — metadata silently lost when the ingest is OOM-killed
- `ISSUE_slow_upload_rebuild_full_table_scan.md` — the ~15 min post-ingest rebuild query
- `ISSUE_run_name_collisions.md` — run names are global keys with no uniqueness enforcement
- `pipeline-retry-and-cleanup.md` — planned VM-size escalation retry, cancel button, background poller
- `pipeline/upload_scripts/README.md` — operator reference for the host-side upload scripts

---

## 1. Timeline

| Date | Event |
|---|---|
| 2026-07-01/02 | Upload of run 341 (experiment 2673) "hangs" 10+ min after mutations load, then finishes with **no per-isolate metadata**. Investigation finds the rebuild step ran a ~700 s full-table query, the process was OOM-killed, and metadata (applied last) was skipped silently. Two issue docs written (commit `f4e322ec`). |
| 2026-08-14 | Planning note for retry/cancel/cleanup in the web pipeline (commit `4f02c2b1`). |
| 2026-09-09 | Same failure mode again on a production upload (experiment 2674, submitted through the webapp). The run page showed **Done** although the ingest had died. Metadata for that experiment must be backfilled. |
| 2026-09-11 | Upload overhaul (this changeset). A dev test submission also surfaced the input-folder prefix bug and the run-name collision problem. End-to-end verified with a dev run (run 352, experiment 2678): status flow `uploading → Upload Completed`, per-run log written, metadata present, rebuild peak memory 0.4 GB. Host script deployed to `/upload/` (backup `/upload/webapp-upload.sh.bak-2026-09-11`), web container restarted. |
| 2026-09-15 | Changeset reviewed and committed. Pre-check for the 2674 backfill exposes DB-wide duplicate observed-mutation rows from repeat uploads (§8) and one oversized experiment (2660); repair plan written (§9). Dedupe run the same day on 2674 and 2660, dashboard rebuilt, 2674 metadata backfilled; specifics in the private audit record. Kernel log confirms the OOM mechanism: python killed at ~25 GB on a 31 GB host with no container limit, once per Upload click. |

## 2. The problem chain

Five independent defects lined up to make a failed upload look successful:

1. **The webapp lied about status.** `pipeline/views.py:upload` set the `Run` to
   `uploading`, spawned the host script with `Popen`, and then immediately set the
   status to `done`. Nothing ever reported the real outcome back.
2. **Metadata was applied last.** In `builder/ale_experiment.py`, per-isolate metadata
   (`parse_metadata_post_experiment_upload`) ran after four expensive global rebuilds.
   Any crash or kill during those rebuilds skipped it, and nothing recorded that.
   A DB-wide discriminator query found ~252 experiments with mutations but no metadata.
3. **The rebuild did not fit in RAM.** `dashboard.util.rebuild_mutation_counts` called
   `filter_observed_mutations` on the entire `ObservedMutation` table (5.8M+ rows) with
   `select_related`, materializing every row as an ORM object (~25 GB). The kernel
   OOM-killer ended the ingest with exit 137 and no traceback.
4. **The host script had no error handling.** `webapp-upload.sh` did not check any exit
   code, wrote no log, and its bare `mkdir` failed on reruns. An OOM-killed ingest left
   no trace anywhere an operator would look.
5. **Input-folder listing used a bare blob prefix.** `list_blobs(name_starts_with='foo')`
   also matched `foo_bar/`. A neighbouring folder's year-old CSV had been moved to the
   archive tier, the read raised `BlobArchived`, and the submission crashed after creating
   the `Run` row but before creating the Batch job (run stuck at `running`, run page 500).

## 3. What changed (2026-09-11 changeset)

### A. Truthful upload status

| File | Change | Why |
|---|---|---|
| `pipeline/models.py` | New `Run` status `uploaded` ("Upload Completed"). | `done` was overloaded (Batch analysis finished vs. ingested into ALEdb). `done` is now reserved for the future background poller; nothing writes it anymore. |
| `pipeline/views.py` | `upload` no longer sets `done`. It ignores the click if the run is already `uploading`. | The host script owns the final status. The guard prevents double-launching the ingest on repeat clicks. |
| `pipeline/management/commands/set_run_status.py` (new) | `manage.py set_run_status <run_name> <status>`; validates against `PIPELINE_RUN_STATUS`. | Gives the host script (and operators) a way to write the real outcome. Also the manual reset for a run stuck in `uploading`. |
| `pipeline/upload_scripts/webapp-upload.sh` | Calls `set_run_status <run> uploaded` on success, `error` on failure. | Closes the loop the view left open. |
| `templates/pipeline/run.html` | Shows the status; while `uploading` the button is disabled and the page auto-refreshes every 30 s; `error` and `uploaded` states get an explanatory message. | Users kept re-clicking Upload because the page gave no feedback. |
| `templates/pipeline/pipeline_manager.html` | Uses `get_status_display`. | Human-readable labels for the new status. |

### B. Metadata before rebuilds, failures propagate

| File | Change | Why |
|---|---|---|
| `builder/ale_experiment.py` (both `create_ale_experiment` and `create_ensemble_ale_experiment`) | `parse_metadata_post_experiment_upload` now runs **before** the rebuilds, wrapped in its own `try/except`. A metadata failure is logged, printed with the `load_md` replay hint, and reflected in the return value, but does not abort the rebuilds. Each rebuild step prints a progress line. | Fix 1 ("reorder") and fix 3 ("fail loud") from the OOM issue doc. The step markers make a killed ingest diagnosable from the log. |
| `builder/ale_experiment.py` | `upload_ale_experiment` returns the create result; `upload_ale_experiments` returns the failed paths; `upload_ale_collection` returns `(count, failed_paths)`. | The management command needs to know what failed. |
| `ale/management/commands/upload.py` | Raises `CommandError` (non-zero exit) when no experiments were found or any experiment failed; prints an `N of M ok` summary. | Until now `manage.py upload` exited 0 no matter what, so the host script could not tell success from failure. |

### C. Rebuild fits in memory

| File | Change | Why |
|---|---|---|
| `filter/util.py` | `filter_observed_mutations` split: new `build_filtered_observed_mutation_queryset` returns the lazily-filtered queryset plus the two gene collections; the original function now calls it and keeps its exact materializing behaviour for its 12 other callers. | Lets a caller apply the SQL half of the filter without loading rows. No behaviour change for existing callers (filter test suite passes). |
| `dashboard/util.py` | `rebuild_mutation_counts` uses new `_compute_mutation_count_stats`, which streams id-keyed chunks of 100k rows via `values_list` (six slim columns), re-implements the per-row gene exclusion with the same operator precedence, dedupes unique mutations by `mutation_id`, and classifies each mutation once. | Peak memory 25 GB → 0.4 GB (measured). Fix 2 ("memory hog") from the issue doc, memory half only. The ~15 min query time is unchanged (see Roadmap). |

### D. Host script hardening

`pipeline/upload_scripts/webapp-upload.sh` was rewritten: `#!/bin/bash`, `set -uo pipefail`,
`mkdir -p`, every invocation logged to `/upload/logs/<run>_<UTC timestamp>.log` with
timestamped step markers and elapsed seconds, and outcome reported via `set_run_status`.
Both management commands are invoked with `--skip-checks` to avoid the slow Django system
checks on every call. Dead commented-out scp/filter lines were removed.

### E. Input-folder prefix fix

`pipeline/azure_pipeline_util.py:get_input_directory_contents` appends a trailing slash to
the prefix so a folder only matches itself.

### F. Documentation

`ISSUE_upload_metadata_skipped_on_oom.md` updated with what is now implemented;
`ISSUE_run_name_collisions.md` is new; `pipeline/upload_scripts/README.md` describes the
new status reporting, the log location, and the manual reset command.

## 4. Status semantics after this change

| Status | Written by | Meaning |
|---|---|---|
| `new` | submit view | Row created. |
| `transferring` / `running` | submit view | Azure Batch job in flight. |
| `awaiting upload` | (unused) | Reserved. |
| `uploading` | upload view | Host script launched; page auto-refreshes; button disabled. |
| `uploaded` | `webapp-upload.sh` via `set_run_status` | Ingest exited 0: all experiments created and metadata applied. |
| `error` | `webapp-upload.sh` via `set_run_status` | Extraction failed, ingest exited non-zero (including OOM kill 137), or a metadata failure. Check `/upload/logs/`. |
| `done` | nothing (reserved) | Intended for the future poller: Batch analysis finished. Existing rows keep it. |

A run stuck in `uploading` (host script itself killed) is reset with:

```
docker exec aledb-web python manage.py set_run_status <run_name> error
```

## 5. Verification performed

- End-to-end dev upload on 2026-09-11 (run 352 → experiment 2678): correct status transitions, per-run log written, metadata applied, rebuild completed at 0.4 GB peak.
- 2026-09-15 review: `manage.py test filter builder` gives the same 9 pre-existing builder failures as unmodified master and all filter tests pass. `bash -n` and `py_compile` clean. Deployed `/upload/webapp-upload.sh` is byte-identical to the repo copy.
- Refactor equivalence of `_compute_mutation_count_stats` checked by reading against the original: same `not deleted and A or B` precedence, same subset rules, unique mutations deduped by `mutation_id` exactly as `get_mutations_from_observed_muations` did, same type/functional-change classification.

## 6. Known limitations carried forward (from the 2026-09-15 review)

- **Retry after `error` re-ingests and duplicates `ObservedMutation` rows** (`builder/upload.py`, the `bulk_create` path has no dedupe). A metadata-only failure now also lands in `error` even though mutations are fully in the DB, so the `run.html` "you can retry" copy is risky advice. Needs either a dedupe guard on ingest or a distinct status/message for metadata-only failures.
- **`find -execdir tar … \;` always exits 0** even when `tar` fails, so the script's "extraction FAILED" branch cannot trigger. A corrupt tarball currently surfaces later as an ingest failure (or a partial experiment). Iterate the archives in a shell loop instead.
- `run.html` says the status will change to "Done or Error"; the terminal success state is actually "Upload Completed".
- `dashboard/util.py` still imports `filter_observed_mutations` / `get_mutations_from_observed_muations` and keeps `_find_mutation_type` / `_find_functional_change_type`, none of which are used any more.
- `pipeline/util.py:update_run_status` has no `uploaded` arm (it is a no-op switch today, so harmless).
- `makemigrations --check` reports a pending change for `Run.status` choices. Migrations are local-only in this repo (`*/migrations` is gitignored) and the local `0001_initial` already lacked `transferring`/`error`; a choices change does not alter the MySQL schema. No action unless migrations are ever brought under version control.
- `set_run_status` uses `.update()` by name, so duplicate run names (see the collisions issue) update several rows.
- Upload view has no ownership check (any logged-in user can trigger any run's upload). Pre-existing.
- Dashboard functional-change update block matches `snp_type_synonymous` / `snp_type_nonsynonymous` but `FUNCTIONAL_CHANGE_TYPE_LIST` carries the plain names, so those two columns are never written. Pre-existing.

## 7. Roadmap

Ordered by priority. Tick items as they land and note the commit.

### Queued (approved in principle, confirm before running)

- [x] **Backfill metadata for experiment 2674** with `manage.py load_md` — done 2026-09-15, one call per source run folder, after the mode-1 dedupe; the sample that exists as two records was skipped by the parser and completed by hand (details in the private audit record). **Never re-upload a run to fix metadata**: re-ingest duplicates `ObservedMutation` rows.
- [ ] **Clean up the dev test artifacts**: experiment 2678 and its dev project (`delete_ale_experiments([2678])`, ~25 min because it triggers the orphan sweep and rebuild), the run 352 row, and the dev folders under `/pipeline_inputs/`, `/output/`, and `/data/aledata/`.

### Next

- [ ] **Database repair, phase 1: remove duplicate observed-mutation rows** (see §9). Do this before any further rebuilds; it removes ~1.05M rows (18% of the table) and fixes experiment 2674's inflated samples as a side effect.
- [ ] **Make ingest idempotent** (see §8 item 1 and `docs/elt-split-plan.md`, three steps: ELT split → builder test harness → idempotent upload with Re-upload button and unique constraint). Without this the repair will not stick.
- [ ] **Filter query-shape rewrite.** The `NOT (mut IN (…) OR (exp AND freq))` predicate forces a full scan; rebuilds still take ~15 min. Memory is fixed, speed is not. Plan in `ISSUE_slow_upload_rebuild_full_table_scan.md`.
- [ ] **Metadata backfill sweep** for the ~252 affected experiments. Discriminator query and `load_md` recipe in `ISSUE_upload_metadata_skipped_on_oom.md`.
- [ ] **Run-name submission guard**, `JobExists` handling in `create_job`, and a proper error state on the run page instead of a 500. Proposed fixes in `ISSUE_run_name_collisions.md`. Longer term: `unique=True` on `Run.name` after deduping existing rows.
- [ ] **Background poller** that flips `running → done` when Azure Batch finishes and cleans up drained pools (`pipeline-retry-and-cleanup.md`). `done` is reserved for it.

### Needs the data owner

- [ ] **Experiment 2660 reference check.** An order of magnitude more mutations per sample than any normal experiment, nearly all of them present in every sample: almost certainly analysed against a reference that is not the parent strain. Options: re-analyse against the ancestor and re-upload, or delete. Until resolved it is the largest single contributor to the observed-mutation table and dominates every rebuild.
- [ ] **Experiment 2674: one sample was re-run in a later pipeline run and ingested as a second sample record**, with different breseq results. Owner decides which copy to keep; metadata can be applied to both meanwhile.
- [ ] **Mode 2 duplicates in 19 older experiments** (291 extra sample records): review per experiment, some may be deliberate re-sequencing.

### Smaller fixes

- [ ] Ingest dedupe guard or a distinct metadata-only failure state, and matching `run.html` copy (see §6, first item).
- [ ] Make extraction failures detectable in `webapp-upload.sh` (shell loop over archives).
- [ ] Fix "Done or Error" wording in `run.html`.
- [ ] Remove dead imports/helpers from `dashboard/util.py`.
- [ ] Ownership check on the upload view.
- [ ] Fix the `snp_type_*` name mismatch in the dashboard update block.
- [ ] VM-size escalation retry and cancel button (`pipeline-retry-and-cleanup.md`).

## 8. Data integrity findings and codebase improvements (2026-09-15)

Investigating the 2674 backfill exposed that repeat uploads have been silently duplicating
data for years. Two modes, with different symptoms:

| Mode | What the repeat upload did | Visible where | Scale (whole DB) |
|---|---|---|---|
| 1. Duplicate rows under one sample record | Found the existing experiment/ALE/flask/isolate/replicate/sample records and appended a second full set of `ObservedMutation` rows to the same sample (`bulk_create`, no existence check) | Nowhere in the mutation table (grid is keyed by mutation × sample, copies overwrite the same cell). Only in row-based counts: home-page totals, Stats page "observed" counts, rebuild memory/time | 1,036,878 duplicate (sample, mutation) groups, 1,052,363 extra rows, 674 samples, 141 experiments; 99% are exact 2× copies, max 9× |
| 2. Duplicate sample record | A lookup field differed (e.g. date/person on the isolate), so a new isolate/replicate/sample record was created | Extra column in the mutation table, extra row in the Stats sample list | 291 extra sample records in 19 experiments, mostly old (ids ~1086–1199) |

Verified: mode-1 copies are byte-identical in every non-id column for the experiments checked
(2674, 2510, 2568, 904, 2539), apart from a handful of groups in 2660 explained by the ingest
split in item 7a. Experiment 2660 alone holds the large majority of the extra rows and is the
largest single contributor to the ~5.8M-row table. Independently of the duplicates, 2660 has an
order of magnitude more distinct mutations per sample than a typical experiment, nearly all of
them present in every sample, i.e. a reference-mismatch profile. The oldest affected experiment
dates from 2019, so this predates the webapp upload button: any repeat of `manage.py upload` on
the same folder duplicates. Per-experiment counts live in the private audit record (see §9).

Why mode 1 matters even though the table looks fine: the Stats page and the dashboard rebuild
load every `ObservedMutation` row as an ORM object. The junk rows are a large part of the 25 GB
peak that caused the OOM kills and of the ~15 min rebuild, and the home-page observed-mutation
total is inflated by ~18%.

### Codebase improvements, in priority order

1. **Idempotent ingest** (`builder/upload.py`, `builder/ale_experiment.py`).
   - DB unique constraint on `ObservedMutation(sequencing_experiment, mutation)` so a repeat
     insert fails loudly. Migrations are gitignored in this repo, so the constraint has to be
     applied by a tracked SQL/one-off script and recorded in `docs/operations/`.
   - Per-sample replace-or-skip: before `bulk_create`, either delete that sample's existing
     rows (explicit re-ingest) or skip the sample when rows exist (default), and print which.
   - Look up isolate/replicate records by their stable identity (ALE, flask, isolate,
     replicate numbers) rather than every field, so a re-run cannot mint a second sample record
     (mode 2).
2. **Take the global rebuild out of the ingest (ELT split).** `create_*_ale_experiment`
   currently ends with `rebuild_dashboard_data()`, which recomputes the *whole-database*
   sample and mutation count tables that only the home page reads. That is a global transform
   riding on a per-experiment load: it made every upload's memory and time proportional to the
   entire table (the OOM chain in §2) and it is where every metadata loss happened. Split it:
   - **Load** (per upload): parse samples, insert rows, apply metadata. Must be cheap,
     scoped to the experiment, and idempotent (item 1).
   - **Per-experiment transforms** (convergence, fixation, static data): scoped and fast for a
     normal experiment; keep them in the upload for now, but make them re-runnable on their own
     (`rebuild_stats`-style command taking experiment ids) so a failed step can be replayed
     without re-ingesting.
   - **Global aggregates** (dashboard counts): drop the call from the ingest and run the
     existing `manage.py rebuild_stats` on a schedule (host cron, nightly) and optionally at the
     end of `webapp-upload.sh` as a separate process after the ingest has exited. Home-page
     totals then lag an upload by at most a day, which is acceptable.
   Cheapest item on this list (one call removed, one cron line) and it removes the whole-table
   dependency from the upload path for good.
3. **Upload view guards** (`pipeline/views.py`): refuse a plain re-upload of a run already in
   `uploaded`; require an explicit re-ingest action; add the ownership check.
4. **Ingest data-quality gate**: after a sample is parsed, warn (and optionally refuse) when
   the mutation count is far above normal or when >90% of an experiment's mutations are shared
   by every sample. This is the cheap detector for a wrong reference genome (2660's profile).
5. **Stats page counts in SQL** (`stats/util.py`, `stats/views.py`): the by-type and
   by-protein-change counts materialize every row exactly as the dashboard rebuild used to.
   Reuse `build_filtered_observed_mutation_queryset` + the streaming tally from
   `dashboard/util.py`. Same pattern, modest change, makes large experiments load in seconds.
6. **Filter query-shape rewrite** (existing item; the NOT IN predicate forces a full scan).
7. **Mutation table page size cap** for experiments above a few thousand mutations (paginate
   or require a gene/position filter) so one oversized experiment cannot take the site down.
8. **Ingest atomicity**: wrap each sample's insert in a transaction so a killed ingest cannot
   leave a half-inserted sample.
8a. **Ingest split rows**: when breseq junction evidence and GATK both report the same
   mutation, the ingest writes two `ObservedMutation` rows for it (one with breseq evidence and
   frequency, one GATK-only) instead of one merged row. Seen for one mutation across many
   samples of one experiment. Merge into a single row at ingest; the unique constraint in item 1
   will enforce it.
9. **Tests**: repair the 9 stale builder tests (fixture setup, list-valued frequency, the
   zero-mutation ingest of the LTEE fixture) and add tests for idempotent ingest and the
   dedupe command.
9. The smaller items already listed in §6/§7.

## 9. Database repair plan

Ordered so each step is verifiable and reversible. All deletions need an explicit go from the
operator; run artifacts (row exports, audit counts with real specifics) go to the private side,
not this repo: dated markdown files under `/data/ops_audit/` on the VM host (data disk, not in
git). Operator procedure: `docs/operations/observed_mutation_dedupe.md`.

0. **Backup first.** `mysqldump` of `seq_observedmutation` (or a full dump) to the data disk;
   record row count, distinct (sample, mutation) count, and the per-experiment duplicate table
   as the "before" audit record.
1. **Mode-1 dedupe, in stages.** Management command
   `manage.py dedupe_observed_mutations <experiment id ...>|--all [--dry-run]` (added
   2026-09-15). A row is deleted only if a lower-id row in the same sample is identical in every
   other column, so only exact re-ingest copies go; deleted rows are copied to
   `seq_observedmutation_dedupe_backup` first (undo = one `INSERT ... SELECT`). Rows that share
   a sample and mutation but differ are reported and left in place. Order: 2674 (small proof)
   → 2660 → everything else (~38k rows across 139 experiments), with the long tail deliberately
   deferred to leave time to document and communicate. **2674 and 2660 done 2026-09-15**
   (counts and verification in the private audit record); the backup table is kept until the
   unique constraint is in place.
2. **Rebuild derived data.** `rebuild_dashboard_data()` once; convergence/fixation/static data
   are set-based and should be unchanged, but re-run them for the 141 affected experiments and
   diff row counts before/after as the check.
3. **Unique constraint** on `(sequencing_experiment_id, mutation_id)` as soon as step 1 is
   clean, so the repair cannot regress. Deploy the ingest change (§8 item 1) in the same window.
4. **Experiment 2674 metadata backfill.** One `manage.py load_md <folder>/metadata:2674` per
   source run folder. The sample that exists as two records will be skipped by the parser
   (`TechnicalReplicate.get` raises on two matches); apply its metadata to both copies
   with a short script until the owner picks one, then delete the other copy's isolate/replicate
   /sample/rows.
5. **Experiment 2660.** Owner decision (re-analyse vs delete). Deleting an experiment of this
   size triggers the orphan sweep and full rebuild; plan for a long-running background job.
6. **Mode-2 duplicates (19 experiments).** Per-experiment review with the owners; delete only
   confirmed accidental sample records (isolate → replicate → sample → rows), then rebuild those
   experiments.
7. **Metadata backfill sweep** for the ~252 experiments with empty strain/description and the
   parser's default medium (discriminator query in `ISSUE_upload_metadata_skipped_on_oom.md`).
   Needs the source metadata folders; where they no longer exist, record the experiment as
   unrecoverable.
8. **Dev artifacts cleanup** (experiment 2678, run 352, dev input/output/extract folders).
