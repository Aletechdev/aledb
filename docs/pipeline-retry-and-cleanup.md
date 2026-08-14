# Future work: VM-size escalation retry + cancel/cleanup for pipeline runs

Status: **not implemented** — planning note (2026-08-14).

Both features exist in spirit in the interactive CLI tool at
`/var/www/pipeline/batch-amp/src/batch_amp.py` (sibling repo, not this one).
This note records what porting them into the ALEdb web pipeline would take.

Relevant code: `pipeline/azure_pipeline_util.py` (submission),
`pipeline/azure_batch_status_util.py` (status/task queries),
`pipeline/views.py` + `templates/pipeline/run.html` (run page),
`pipeline/models.py` (`Run`, `Attempt`).

---

## 1. Cancel + cleanup — LOW complexity (~half a day)

Today there is no way to stop a run from the UI, and jobs/pools are never
deleted — pools autoscale to 0 nodes but the Batch objects accumulate forever.

### Cancel button on the run page

- New view `cancel(request, id)`; POST-only, restrict to run owner or staff.
- In the web pipeline, **job id == pool id == run.name** (see
  `run_pipeline()` — it passes `run_name` for both), so no lookup needed:
  ```python
  batch_client.job.terminate(run.name)   # stops queued/running tasks
  batch_client.pool.delete(run.name)     # releases nodes immediately
  run.status = 'error'                   # or add a 'cancelled' choice to PIPELINE_RUN_STATUS
  ```
- Wrap both calls in `try/except BatchErrorException` and ignore
  `JobNotFound` / `PoolNotFound` — the button must be safe to click twice.
- Template: confirm-dialog button on `run.html`, shown while status is
  `running`.

### End-of-run cleanup

Two options, in increasing correctness:

1. **Opportunistic (trivial):** the `run()` view already counts completed
   tasks. When `complete_count == len(task_list)`, delete the pool (keep the
   job for its task history / stdout links, or delete it too and rely on the
   blob-stored `_out.txt` copies).
2. **Background poller (better, do later):** a cron'd management command that
   sweeps `Run.objects.filter(status='running')`, updates statuses, deletes
   drained pools, and evicts bad nodes (`unusable`/`startTaskFailed`). This is
   also the prerequisite for making escalation automatic instead of a button.

Caution: do NOT copy the CLI's cleanup error handling — its exception path
deletes the pool unconditionally before asking and can `NameError` on an
unbound `pool_id`. Cleanup should be a deliberate action, not an
exception-handler side effect.

## 2. VM-size escalation retry — MEDIUM complexity (~1–2 days incl. Azure testing)

CLI behavior being ported: when tasks fail (typically OOM), rerun just those
tasks on the next-larger VM by swapping the job onto a new pool
(`batch_amp.py:461-469`: disable job → create bigger pool → update job's
pool_info → re-enable). The `Attempt` model already has a `vm` field per
attempt — the schema anticipates this.

### Sketch

New helper in `azure_pipeline_util.py`, e.g. `escalate_run(run, failed_task_ids)`:

1. Find current VM in `config.EDSV4_SERIES_PROGRESSION`, pick the next entry;
   if already at the last entry, surface "no larger size available".
2. `batch_client.job.disable(job_id, 'requeue')`, then wait ~10 s (the CLI
   does; the disable is async).
3. Create the new pool. **The pool id must differ from the job id** (the job
   already owns a pool named `run.name`), so suffix the VM size like the CLI
   does: `f"{run.name}_{vm_size_name}"[:64]` (Batch pool-id limit is 64
   chars). `create_pool()` is already idempotent on `PoolExists`.
4. `batch_client.job.update(job_id, JobUpdateParameter(pool_info=PoolInformation(pool_id=new_pool_id)))`
   then `batch_client.job.enable(job_id)`.
5. **Reactivate completed-failed tasks** — this is the step the CLI doesn't
   have and the main subtlety: `disable('requeue')` only requeues tasks that
   were *running*; tasks already in `completed` state with
   `execution_info.result == 'failure'` will NOT rerun on their own. For each:
   `batch_client.task.reactivate(job_id, task_id)`.
6. Delete the old pool.
7. Record a new `Attempt(run=run, vm=new_vm, input=<same>, output=<same>)`.

View + template: a "Retry failed on larger VM" button on `run.html`, shown
when any task has `execution_info.result == 'failure'`; the `run()` view
already iterates tasks so the failed list is nearly free.

### Gotchas

- **VM-name mapping:** the form posts full names ("Standard_E4ds_v4") but the
  progression config uses tuples like `('Edsv4', 4)`; map via
  `SERIES_INFO[series]['naming_schema']` (see the CLI's naming logic,
  including the `naming_progression == 'linear'` special case for Dv2).
- The disable→sleep→update→enable sequence takes ~15 s of wall time inside a
  request. Acceptable for a manual button; move it into the background poller
  if it ever becomes automatic.
- Output blobs from a failed first attempt may partially exist under
  `output/<run_name>/`; task rerun overwrites them (same blob path), which is
  the desired behavior.
- Real testing needs a real (small, cheap) Batch run — budget for one
  2-sample run on the smallest Edsv4 size. There is no meaningful way to test
  the pool-swap dance offline.

## Suggested order

Cancel button first (small, closes the "runaway cost with no off switch"
gap), then opportunistic cleanup, then escalation retry, then fold all three
into a background poller.

---

## Backlog: other CLI features worth borrowing later

From the same source (`/var/www/pipeline/batch-amp/src/batch_amp.py` +
`node_control.py`). Not scoped yet — captured here so they aren't forgotten.
Note that `pipeline/config.py` already carries the data most of these need
(`SERIES_INFO` cost tables, `ESTIMATE_FINAL_COST_ADJUSTMENT`, VM
progressions) — currently unused by the web path.

- **Cost preview + confirmation gate** (probably the highest-value one).
  CLI shows $/node-hour and total $/hour from `SERIES_INFO` and asks
  "Continue?" before creating the pool. Web path currently submits on POST
  with `vm_count = len(samples)` — no confirmation, no effective cap
  (`DEDICATED_POOL_NODE_COUNT_LIMIT` is 1000). Port as a confirm step
  between the form and `run_pipeline()`: "Found N samples → N nodes of
  <vm> ≈ $X/hour", node count clamped/editable. Also fixes the silent
  0-task job when a directory name is mistyped.
- **Completion monitoring that updates `Run.status`.** CLI watches to the
  end and distinguishes failed (`execution_info.result == 'failure'`) from
  incomplete tasks. Web sets `status='running'` at submission and never
  updates it. Port as the background poller described above.
- **Bad-node sweep.** CLI removes nodes in `BATCH_NODE_BAD_STATES`
  (`unusable`, `startTaskFailed`, `preempted`, ...) while polling
  (`node_control.py`). Autoscale only adjusts target counts and never
  evicts a broken node, so an `unusable` node can bill indefinitely.
  Belongs in the poller.
- **Wall-clock bound.** CLI bounds monitoring at 24 h client-side. Better
  server-side port: `max_wall_clock_time` via `JobConstraints` /
  `TaskConstraints` at submission, so Azure enforces it with no client
  attached (deallocation currently waits for task completion, so one hung
  task holds a node forever).
- **Version/provenance stamping.** CLI prints tool version + build date at
  startup. Web equivalent: record the amp image identifier / pipeline code
  version on each `Attempt` — for an academic resource, knowing which
  pipeline version produced which calls is genuinely valuable.

Known CLI bugs NOT to copy while borrowing (all in its error paths):
unconditional `pool.delete` before prompting with possibly-unbound
`pool_id`/`job_id` (`batch_amp.py` main except block); `print(...".format)`
missing its call args; `node_control.py` error path calls
`print_batch_exception`/`query_yes_no` without importing them.
