# Upload silently skips per-isolate metadata when the process is OOM-killed during post-upload rebuilds

_Draft for a GitHub issue. Investigated 2026-07-01/02 via the `ReducedGenomeEcoli_MS56_ALE_MS56_reJul1` upload (experiment id 2673)._

_Update 2026-09-11: proposed fix 1 (reorder) and fix 3 (fail loud) are implemented — `parse_metadata` now runs before the rebuilds in `builder/ale_experiment.py`, and a failed/killed ingest marks the pipeline Run as `error` via `manage.py set_run_status`. Fix 2 (memory/query scoping) and the backfill of the ~252 affected experiments remain open._

## Summary
When `manage.py upload` runs, per-isolate metadata (media, strain, library prep, description)
is applied **last**, by `parse_metadata_post_experiment_upload`, *after* several expensive
global rebuild steps. Those rebuilds can drive the container to ~27 GB RSS and get
**OOM-killed**. A SIGKILL leaves no traceback, so the upload "ends" with mutations committed
but **metadata never applied — and no error anywhere**. This has happened intermittently
throughout the DB's history: **~252 of 1,079 experiments (~23%) are missing per-isolate
metadata.**

## Impact
- ~23% of experiments show default media (`M9`) and empty strain/library/description even
  though their CSVs contain real values.
- Fails **silently**: no exception in `logs/debug.log`, no `Sample Failed`, upload reports done.
- Mutation data is unaffected — this is metadata-only.

## Root cause
Order of operations in `create_ensemble_ale_experiment` (`builder/ale_experiment.py`):
```
sample loop (mutations)               -> commits mutations         [~561-563, add_breseq_results]
461  AleExperimentFilter
463  rebuild_converge_mutations
464  rebuild_fixated_mutations
465  generate_static_data
466  rebuild_dashboard_data           <-- expensive, high memory
468  parse_metadata_post_experiment_upload   <-- applies media/strain/library/description
469  return True
```
Steps 463-466 run large, poorly-scoped queries that materialize huge `seq_observedmutation`
result sets into the ORM. On 2026-07-01 the upload process reached ~27 GB and was OOM-killed
at **13:41:15 UTC**, between step 465 and step 468 — so `parse_metadata` (468) never ran.

Because the metadata step is **last**, it is the first casualty of any OOM/kill during the
rebuilds.

## Evidence (experiment 2673)
- Mutations present: 32 isolates, 32 tech-reps, **1,105 observed mutations**.
- Rebuild steps that run *before* parse_metadata all completed:
  AleExperimentFilter=1, ConvergeMutation=72, FixatedMutation=47,
  StaticData needle=1105/histogram set.
- `parse_metadata` outputs: **0** `Error for …`, **0** `Invalid metadata` in the entire
  container log → it never iterated.
- No builder exception in `logs/debug.log` (a SIGKILL runs no `except`).
- Kernel log (`dmesg` / journalctl), UTC:
  ```
  Jul  1 13:41:15  docker-compose invoked oom-killer
  Jul  1 13:41:15  Out of memory: Killed process 209392 (python)
                   total-vm:27990128kB anon-rss:27261564kB  (~27 GB)
                   task_memcg=/docker/02a8e87d… (aledb-web container)
  ```
  (Same container OOM-killed multiple times that day: Jun 30 15:08, Jul 1 07:48, 09:17, 13:41.)
- The CSVs were present at the correct path the whole time (ctime 12:57-13:01 UTC, upload
  ran 13:01-13:42), and the path is correct (`find_experiment_paths` strips `/breseq`, so
  read#1 and read#2 use the same `.../metadata`). So neither a path bug nor a timing/race.
- **Dry run proves the code is correct:** running `parse_metadata` for 2673 now (inside a
  rolled-back transaction) flips media `{'M9':28}` -> `{'other':27, 'M9':1}`. The 1 hold-out
  is the starting-strain flask (A0-F0), which is expected.

## Scope (DB-wide)
Discriminator (two independent signals that agree on 252 experiments):
- flask still on the **default M9 media row** (parse_metadata never set media), AND
- `tech_rep.description IS NULL` (parse_metadata writes `''` when it runs, never NULL).

Result: **252 confidently affected / 801 healthy / 1,079 total**, spread across **every id band**
(id 50 -> 2673), with clusters (e.g. band 1000: 66; band 2600: 32, incl. 2660-2673 and the
2621-2640 batch). Not a code regression — it is memory/timing-dependent, and worse recently
because the DB is larger, so the rebuilds allocate more and OOM more often.

## Proposed fixes
1. **Reorder (cheap, high value):** move `parse_metadata` to run **before** the expensive
   rebuilds (461-466). It is cheap and would then survive an OOM in the rebuild. Metadata is
   independent of the rebuild outputs.
2. **Fix the memory hog:** `rebuild_dashboard_data` / the converge-filter query pulls millions
   of `seq_observedmutation` rows into Python (27 GB). Scope to the new experiment, push
   aggregation into SQL, and/or use `.iterator()` / chunking.
3. **Fail loud:** record upload step completion / failure so a killed or skipped post-step is
   visible instead of silently "done". At minimum, log when `parse_metadata` processes 0 CSVs
   for an experiment that has them.
4. **Raise the container memory limit** as a stopgap while (2) is done.

## Remediation / backfill
Metadata can be replayed without re-uploading via the standalone command (verified working
for 2673 in the dry run):
```
python manage.py load_md "<metadata_path>:<exp_id>"
# e.g.
python manage.py load_md "/data/aledata/ReducedGenomeEcoli_MS56_ALE_MS56_reJul1/Reduced_Genome_Ecoli_MS56/MS56_ALE_2022_MS56_reference/metadata:2673"
```
Backfill target = the ~252 affected experiments whose metadata CSVs still exist on disk.
Note: some source CSVs also leave `taxonomy id`/library-prep/`owner` blank (data-entry gaps),
so strain/library may remain empty even after a successful `load_md`.

## How to list affected experiments
Affected = ALL flasks on the default media row AND ALL tech-reps have `description IS NULL`.
(`flask.media_id == <default>` is reliable because `parse_metadata` creates a distinct Media
row even for M9, so a flask left on the default was never touched by `parse_metadata`.)

Django shell (`manage.py shell`):
```python
from ale.models import AleExperiment, Flask, TechnicalReplicate, Media
from django.db.models import Q
import metadata.parser as P

DEF = Media.objects.filter(
    description=P.DEFAULT_MEDIA_DESCRIPTION, temperature=P.DEFAULT_TEMPERATURE,
    volume=P.DEFAULT_VOLUME, stirring_speed=P.DEFAULT_STIRRING_SPEED,
).order_by('id').first().id   # default media row id (was 6)

affected = []
for e in AleExperiment.objects.all():
    fl = Flask.objects.filter(ale_id__ale_experiment=e)
    trs = TechnicalReplicate.objects.filter(isolate__flask__ale_id__ale_experiment=e)
    n, tr = fl.count(), trs.count()
    if n == 0 or tr == 0:
        continue
    on_default = fl.filter(media_id=DEF).count() == n              # media never overridden
    all_null_desc = trs.filter(description__isnull=True).count() == tr  # desc never written
    if on_default and all_null_desc:
        affected.append(e.ale_id)

print(len(affected), 'affected:', sorted(affected, reverse=True))
```

Equivalent raw SQL for a quick count:
```sql
SELECT COUNT(*) FROM (
  SELECT ae.ale_id
  FROM ale_aleexperiment ae
  JOIN ale_aleid aid   ON aid.ale_experiment_id = ae.ale_id
  JOIN ale_flask f     ON f.ale_id_id = aid.id
  JOIN ale_isolate iso ON iso.flask_id = f.id
  JOIN ale_technicalreplicate tr ON tr.isolate_id = iso.id
  GROUP BY ae.ale_id
  HAVING SUM(f.media_id <> 6) = 0          -- 6 = default media row id
     AND SUM(tr.description IS NOT NULL) = 0
) x;
```
