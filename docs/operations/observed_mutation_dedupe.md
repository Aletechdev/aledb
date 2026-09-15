# Removing duplicate observed-mutation rows

Operator procedure for `manage.py dedupe_observed_mutations`. Background and the
overall repair plan: `docs/pipeline-upload-roadmap.md` §8–9.

## What it fixes

Re-running the ingest on a run folder (a second click on Upload, or a repeat of
`manage.py upload`) finds the existing sample records and appends a second full set
of `ObservedMutation` rows to them. The mutation table pages hide this (their grid is
keyed by mutation × sample), but every row-based count is inflated and every rebuild
carries the extra rows.

## Rule

A row is deleted only if a row with a lower id exists in the **same sample**
(`sequencing_experiment_id`) that is identical in **every other column** (NULL-safe).
Only exact re-ingest copies qualify. Rows that share a sample and a mutation but differ
in any column are reported and left in place (they come from an ingest quirk that writes
a breseq-evidence row and a GATK-only row for one mutation, not from a re-upload).
Copies of a sample that were ingested as a *separate* sample record are never touched;
that is a data-owner decision.

## Procedure

```bash
# 1. dry run: per-sample counts, nothing changes
docker exec aledb-web python manage.py dedupe_observed_mutations <experiment id> --dry-run --skip-checks

# 2. record the "before" state in the private audit file (see below)

# 3. live run (minutes for a large experiment; runs in id-ordered batches)
docker exec aledb-web python manage.py dedupe_observed_mutations <experiment id> --skip-checks

# whole database instead of named experiments:
docker exec aledb-web python manage.py dedupe_observed_mutations --all --dry-run --skip-checks
```

Every deleted row is first copied, with its original id, into the table
`seq_observedmutation_dedupe_backup` (same schema; created on first use; not a Django
model, so it is invisible to the admin and to migrations). The command aborts if a sample
still has exact copies after its pass.

## After a live run

1. `rebuild_dashboard_data()` (home-page totals are row counts). Convergence, fixation
   and static data are set-based and unaffected, but compare their row counts before and
   after as the check.
2. Write the audit record.

## Undo

```sql
INSERT INTO seq_observedmutation
SELECT * FROM seq_observedmutation_dedupe_backup
WHERE sequencing_experiment_id IN (<sample ids of the experiment>);
```
then rebuild dashboard data again. Keep the backup table until the unique constraint on
`(sequencing_experiment_id, mutation_id)` is in place and the data owners have been
informed; then dump it to the data disk and drop it.

## Verification queries

```sql
-- exact copies left in an experiment's samples (must be 0 after a run)
SELECT COUNT(*) FROM (
  SELECT 1 FROM seq_observedmutation WHERE sequencing_experiment_id IN (<ids>)
  GROUP BY <all non-id columns> HAVING COUNT(*) > 1) t;

-- backup ids that still exist in the live table (must be 0)
SELECT COUNT(*) FROM seq_observedmutation_dedupe_backup b
JOIN seq_observedmutation o ON o.id = b.id;
```

## Audit record (private)

Per-experiment counts are unpublished research data and stay out of this repo. For each
run write a dated markdown file on the VM host under `/data/ops_audit/` with: date,
operator, command and commit, experiments and sample ids touched, rows before/after,
dashboard totals before/after, backup-table row count, and the verification results.
