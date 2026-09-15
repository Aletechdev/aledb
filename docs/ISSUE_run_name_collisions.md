# Run names are global keys with no uniqueness enforcement — reuse breaks silently

_Written 2026-09-11, after a failed test submission surfaced the adjacent prefix-matching bug
(fixed same day, see below)._

## Summary

A pipeline run's name is used as the primary key everywhere — Django `Run` row, Azure Batch
job id, Azure Batch pool id, output blob folder (`output/<run_name>/`), and the ingest
directory (`/data/aledata/<run_name>/`) — but nothing enforces uniqueness. Submitting a
second run with an already-used name never works and never cleanly overwrites; each layer
fails differently, mostly silently.

## What happens per layer

1. **Django row** — `pipeline/views.py` uses
   `Run.objects.get_or_create(name=run_name, user=request.user, xpmd=xpmd)` and `Run.name`
   has no unique constraint:
   - same user + same name + same xpmd string → row is reused (benign);
   - different user, **or same user with a different xpmd string** (it is free-typed) →
     a **second `Run` row with the same name** is created. The upload view and
     `set_run_status`'s lookup by name then hit `MultipleObjectsReturned` /
     multi-row updates: the Upload button 500s **for both runs**.
2. **Azure pool** — `create_pool` tolerates `PoolExists` and silently **reuses the old
   pool**, including its original VM size; the VM size chosen on resubmission is ignored.
3. **Azure job** — `create_job` has no error handling. Jobs are never deleted, so
   resubmitting any previously-run name raises `JobExists` and kills the submission
   halfway: `Run.status` is already set to `running`, no tasks are added, and the only
   trace is a `pipeline manager broke` traceback in `logs/debug.log`. The user sees
   nothing.
4. **Output blobs** — task outputs land at `output/<run_name>/<sample>.tar.gz`; this is
   the one layer that truly **overwrites** (last writer wins). Desired for a deliberate
   rerun of failed tasks, destructive for accidental reuse.
5. **Run detail page** — while a `Run` row exists but its Azure job does not (cases 1/3
   above, or a submission crash), `/pipeline/run/<id>` raises `JobNotFound` inside the
   view, which is swallowed and the view returns `None` → HTTP 500 ("page not available").

## Observed trigger (2026-09-11)

A test submission created the Run row, then crashed during sample discovery before any job
existed: input-folder listing used `list_blobs(name_starts_with=<folder>)` — a bare prefix —
so the folder name also matched an older sibling folder sharing the prefix, whose year-old
CSV had been moved to the Azure **archive tier**, and the read failed with `BlobArchived`.
Symptoms: run stuck at `running`, run page 500, no user-visible error.

**Fixed same day:** the listing now appends a trailing slash
(`pipeline/azure_pipeline_util.py:get_input_directory_contents`), so a folder only matches
itself. The remaining items below are still open.

## Proposed fixes (open)

- **View guard (no migration):** on submit, reject a name for which any `Run` already
  exists (unless it is the same user's row with no Azure job yet — the failed-submission
  retry case) with a visible form error.
- **Handle `JobExists` in `create_job`** with a clear "run name already used, pick a new
  name" error surfaced to the form.
- **Run page:** render an error state instead of returning `None` when the Batch job
  doesn't exist (fixes the 500).
- **Longer term:** `unique=True` on `Run.name` (needs a migration plus dedup of existing
  duplicate names first).

## How to inspect

- Submission crashes: `logs/debug.log`, search `pipeline manager broke`.
- Ingest/upload phase: per-run log files on the VM host under `/upload/logs/` (one file
  per upload invocation, named `<run_name>_<timestamp>.log`), plus `docker logs aledb-web`.
- Batch job/pool state: `pipeline/scripts/` helpers or the Azure portal; job id == pool id
  == run name.
