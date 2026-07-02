# Slow upload: post-upload derived-table rebuild scans the whole mutation table

_Observed 2026-07-01 while uploading `ReducedGenomeEcoli_MS56_ALE_MS56_reJul1` (run 341)._

## Symptom
The `manage.py upload` process appears to "hang" for a long time (10+ min) **after**
mutations are already loaded. The sample loop finishes fast (all 32 isolate `.gd`
files processed, 0 failures); the wait is entirely in the post-loop rebuild phase.

Process evidence: PID used **6 s CPU over 11 min (0.9%)**, parked in `do_sys_poll`.
So it is **not** CPU- or subprocess-bound — it is blocked waiting on a single MySQL query.

## Where the time goes
`builder/ale_experiment.py:461-468`, in `create_ensemble_ale_experiment`, runs after the
sample loop:
```
rebuild_converge_mutations → rebuild_fixated_mutations → generate_static_data → rebuild_dashboard_data → parse_metadata
```
One of these (converge/filter rebuild) issues a query that ran **~700 s**:
```sql
SELECT ...50+ cols...
FROM seq_observedmutation
  INNER JOIN seq_mutation
  LEFT JOIN seq_resequencingexperiment
  LEFT JOIN ale_technicalreplicate
  LEFT JOIN ale_isolate
  LEFT JOIN ale_flask
  LEFT JOIN ale_aleid
  LEFT JOIN ale_aleexperiment
WHERE NOT ( seq_observedmutation.mutation_id IN (~100 ids)
            OR (ale_aleid.ale_experiment_id = 50 AND ... frequency < 0.2 ...) )
```

## Why it is slow
1. **Global scan, not experiment-scoped.** `WHERE NOT (A OR B)` = `NOT A AND NOT B`.
   `NOT (ale_experiment_id = 50 AND ...)` matches every row where the experiment isn't 50,
   i.e. effectively the entire `seq_observedmutation` table (all experiments, millions of
   rows). Cost grows with total DB size, not with the 32 samples just added.
2. **Index-defeating shape.** A negated compound predicate across 6 joined tables can't use
   an index range scan → MySQL does a full scan + nested-loop joins.
3. **Large result materialized into Python** via the Django ORM (select_related across the
   whole FK chain), pulling a huge row set.

Net: every upload pays this global recompute; it gets slower as ALEdb grows. Same family as
the global-filter/search performance work (see recent search-performance profiling notes).

## Not a bug in this upload
Data is safe and already committed; the rebuild is grinding, not hung. It will finish.

## Possible improvements (unverified — needs EXPLAIN + measurement)
- **Scope the rebuild to the new experiment** instead of scanning globally. Trace
  `converge.util.get_converge_mutation_list()` (called from
  `_create_converge_mutations`, `builder/ale_experiment.py:504`) and the default-filter
  query builder in `filter/models.get_default_experiment_filter_params`; the
  `NOT (... OR ale_experiment_id = 50 ...)` clause is where the whole-table scan enters.
- **Rewrite the negation** (`NOT (X IN list OR cond)`) into positive, index-friendly
  conditions, or split into two queries, so MySQL can use indexes.
- **Add indexes** covering the join/filter columns actually used
  (`seq_observedmutation.mutation_id`, `.frequency`, `ale_aleid.ale_experiment_id`).
- **Defer/queue** the dashboard/static-data rebuilds out of the synchronous upload path
  (background task) so the uploader returns promptly and derived tables refresh async.

## How to inspect live next time
- Long query: `SHOW FULL PROCESSLIST` (DB is **MySQL**, not Postgres).
- Process state: `ps -o etime,time,%cpu,stat,wchan -p <pid>` inside `aledb-web`
  (low CPU + `do_sys_poll` = blocked on DB, not computing).
