"""
Remove duplicate ObservedMutation rows left behind by repeat uploads of the same
sample (docs/pipeline-upload-roadmap.md, sections 8-9).

Rule: a row is deleted only if an earlier row (lower id) exists in the same sample
(sequencing_experiment_id) with identical values in every other column, i.e. it is
an exact copy produced by re-ingesting the same breseq output. Rows that share a
sample and a mutation but differ in any column (e.g. the ingest quirk that writes
a breseq-evidence row and a GATK-only row for one mutation) are left in place and
reported. Copies of a sample that were ingested as a *separate* sample record
(own sequencing_experiment_id) are never touched: that is a data-owner decision.

Deleted rows are first copied into a backup table (same schema, same ids) so the
operation can be undone with
    INSERT INTO seq_observedmutation SELECT * FROM <backup_table>;

Examples:
    manage.py dedupe_observed_mutations 2674 --dry-run
    manage.py dedupe_observed_mutations 2674
    manage.py dedupe_observed_mutations --all --dry-run
"""
from django.core.management import BaseCommand, CommandError
from django.db import connection, transaction

TABLE = 'seq_observedmutation'
DEFAULT_BACKUP_TABLE = 'seq_observedmutation_dedupe_backup'

RESEQ_IDS_FOR_EXPERIMENT_SQL = """
    SELECT r.id
    FROM seq_resequencingexperiment r
    JOIN ale_technicalreplicate tr ON tr.id = r.tech_rep_id
    JOIN ale_isolate i ON i.id = tr.isolate_id
    JOIN ale_flask f ON f.id = i.flask_id
    JOIN ale_aleid a ON a.id = f.ale_id_id
    WHERE a.ale_experiment_id = %s
    ORDER BY r.id
"""

RESEQ_IDS_WITH_DUPLICATES_SQL = """
    SELECT DISTINCT sequencing_experiment_id
    FROM (SELECT sequencing_experiment_id
          FROM seq_observedmutation
          GROUP BY sequencing_experiment_id, mutation_id
          HAVING COUNT(*) > 1) t
    ORDER BY sequencing_experiment_id
"""

def _columns():
    from seq.models import ObservedMutation
    return [f.column for f in ObservedMutation._meta.fields if f.column != 'id']


def _exact_copy_ids_sql():
    """Ids of rows that are exact copies (all non-id columns equal) of a lower-id row in the same sample."""
    columns = _columns()
    return """
        SELECT o.id
        FROM seq_observedmutation o
        JOIN (SELECT %(cols)s, MIN(id) AS keep_id
              FROM seq_observedmutation
              WHERE sequencing_experiment_id = %%s
              GROUP BY %(cols)s
              HAVING COUNT(*) > 1) k
          ON %(join)s AND o.id > k.keep_id
        ORDER BY o.id
    """ % {'cols': ', '.join(columns),
           'join': ' AND '.join('o.%s <=> k.%s' % (c, c) for c in columns)}  # NULL-safe


def _non_identical_groups_sql():
    """(mutation_id, row count) for sample+mutation groups that still hold more than one distinct row."""
    columns = ', '.join(_columns())
    return """
        SELECT mutation_id, SUM(n)
        FROM (SELECT mutation_id, COUNT(*) AS n
              FROM (SELECT DISTINCT %s FROM seq_observedmutation WHERE sequencing_experiment_id = %%s) d
              GROUP BY mutation_id HAVING COUNT(*) > 1) t
        GROUP BY mutation_id
    """ % columns


def _remaining_exact_copies_sql():
    columns = ', '.join(_columns())
    return """
        SELECT COUNT(*)
        FROM (SELECT 1 FROM seq_observedmutation WHERE sequencing_experiment_id = %%s
              GROUP BY %s HAVING COUNT(*) > 1) t
    """ % columns


class Command(BaseCommand):

    help = ("Delete duplicate ObservedMutation rows (same sample + same mutation), keeping the lowest id. "
            "Deleted rows are copied to a backup table first.")

    def add_arguments(self, parser):
        parser.add_argument('experiment_ids', nargs='*', type=int,
                            help='AleExperiment ids to process (omit with --all)')
        parser.add_argument('--all', action='store_true', help='Process every sample that has duplicates')
        parser.add_argument('--dry-run', action='store_true', help='Report what would be deleted; change nothing')
        parser.add_argument('--batch-size', type=int, default=20000, help='Rows per DELETE statement (default 20000)')
        parser.add_argument('--backup-table', default=DEFAULT_BACKUP_TABLE,
                            help='Table that receives deleted rows (default %s)' % DEFAULT_BACKUP_TABLE)

    def handle(self, *args, **options):
        experiment_ids = options['experiment_ids']
        if bool(experiment_ids) == options['all']:
            raise CommandError("give one or more experiment ids, or --all (not both)")
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        backup_table = options['backup_table']
        exact_copy_ids_sql = _exact_copy_ids_sql()
        non_identical_sql = _non_identical_groups_sql()
        remaining_sql = _remaining_exact_copies_sql()
        left_in_place = 0
        if not backup_table.replace('_', '').isalnum():
            raise CommandError("backup table name must be alphanumeric/underscore")

        with connection.cursor() as cursor:
            if options['all']:
                cursor.execute(RESEQ_IDS_WITH_DUPLICATES_SQL)
                scope = [('all', [row[0] for row in cursor.fetchall()])]
            else:
                scope = []
                for experiment_id in experiment_ids:
                    cursor.execute(RESEQ_IDS_FOR_EXPERIMENT_SQL, [experiment_id])
                    reseq_ids = [row[0] for row in cursor.fetchall()]
                    if not reseq_ids:
                        raise CommandError("experiment %s has no samples (wrong id?)" % experiment_id)
                    scope.append((experiment_id, reseq_ids))

            if not dry_run:
                cursor.execute("CREATE TABLE IF NOT EXISTS %s LIKE %s" % (backup_table, TABLE))
                self.stdout.write("Deleted rows are copied to %s before deletion." % backup_table)

            grand_total = 0
            for label, reseq_ids in scope:
                samples_affected = 0
                rows_for_scope = 0
                for reseq_id in reseq_ids:
                    cursor.execute(exact_copy_ids_sql, [reseq_id])
                    ids = [row[0] for row in cursor.fetchall()]
                    cursor.execute(non_identical_sql, [reseq_id])
                    non_identical = cursor.fetchall()
                    if not ids and not non_identical:
                        continue
                    note = ""
                    if non_identical:
                        left_in_place += len(non_identical)
                        note = "; %d mutation(s) also have non-identical extra rows, left in place (e.g. mutation %s, %d distinct rows)" % (
                            len(non_identical), non_identical[0][0], non_identical[0][1])
                    if not ids:
                        self.stdout.write("  sample %s: no exact copies%s" % (reseq_id, note))
                        continue
                    samples_affected += 1
                    rows_for_scope += len(ids)
                    if dry_run:
                        self.stdout.write("  sample %s: %d exact-copy rows%s" % (reseq_id, len(ids), note))
                        continue
                    for start in range(0, len(ids), batch_size):
                        chunk = ids[start:start + batch_size]
                        placeholders = ','.join(['%s'] * len(chunk))
                        with transaction.atomic():
                            cursor.execute("INSERT INTO %s SELECT * FROM %s WHERE id IN (%s)"
                                           % (backup_table, TABLE, placeholders), chunk)
                            cursor.execute("DELETE FROM %s WHERE id IN (%s)" % (TABLE, placeholders), chunk)
                    cursor.execute(remaining_sql, [reseq_id])
                    remaining = cursor.fetchone()[0]
                    self.stdout.write("  sample %s: deleted %d exact-copy rows, remaining exact copies: %d%s"
                                      % (reseq_id, len(ids), remaining, note))
                    if remaining:
                        raise CommandError("sample %s still has exact copies after deletion; stopping" % reseq_id)
                grand_total += rows_for_scope
                self.stdout.write("%s experiment %s: %d samples with exact copies, %d rows%s"
                                  % ("DRY RUN" if dry_run else "DONE", label, samples_affected, rows_for_scope,
                                     " would be deleted" if dry_run else " deleted"))
            self.stdout.write("Total rows %s: %d" % ("that would be deleted" if dry_run else "deleted", grand_total))
            if left_in_place:
                self.stdout.write("%d sample+mutation group(s) with non-identical extra rows were left in place "
                                  "(ingest split rows, not upload copies)." % left_in_place)
            if not dry_run and grand_total:
                self.stdout.write("Derived tables are now stale: run rebuild_dashboard_data() and per-experiment "
                                  "rebuilds (see docs/pipeline-upload-roadmap.md section 9, step 2).")
