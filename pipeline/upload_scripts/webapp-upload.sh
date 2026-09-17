#!/bin/bash
# Extracts a finished pipeline run from /output into /data/aledata and ingests
# it into ALEdb, then reports the outcome back to the webapp's Run row.
# An OOM-killed or crashed ingest exits non-zero here, so the run is marked
# "error" instead of silently looking finished.
# Everything is captured to a per-run log file under /upload/logs/ for
# troubleshooting and step-duration tracking.
set -uo pipefail

RUN_NAME="$1"

LOG_DIR=/upload/logs
sudo mkdir -p "$LOG_DIR"

# Repeat-attempt detection. Stopgap until re-upload is idempotent
# (docs/elt-split-plan.md step 3): users may click Upload again, but an attempt
# that follows one which already reached the ingest step appends a second copy
# of the run's ObservedMutation rows, so it is recorded in REUPLOADS.log for an
# operator to dedupe. Must run before this attempt's own log file is created.
REUPLOAD_INDEX="$LOG_DIR/REUPLOADS.log"
D='[0-9]'
PRIOR_ATTEMPTS=0
PRIOR_INGESTS=0
for prior_log in "$LOG_DIR/$RUN_NAME"_${D}${D}${D}${D}${D}${D}${D}${D}_${D}${D}${D}${D}${D}${D}.log; do
    [ -f "$prior_log" ] || continue
    PRIOR_ATTEMPTS=$((PRIOR_ATTEMPTS + 1))
    if sudo grep -q "ingesting into database" "$prior_log"; then
        PRIOR_INGESTS=$((PRIOR_INGESTS + 1))
    fi
done

LOG_FILE="$LOG_DIR/${RUN_NAME}_$(date -u +%Y%m%d_%H%M%S).log"
exec > >(sudo tee -a "$LOG_FILE") 2>&1

report_status() {
    sudo docker exec aledb-web python manage.py set_run_status --skip-checks "$RUN_NAME" "$1"
}

step() {
    echo "=== [$(date -u +%FT%TZ)] (+${SECONDS}s) $* ==="
}

step "upload started for $RUN_NAME"

if [ "$PRIOR_INGESTS" -gt 0 ]; then
    step "REPEAT ATTEMPT #$((PRIOR_ATTEMPTS + 1)): $PRIOR_INGESTS earlier attempt(s) reached the ingest step. DEDUPE NEEDED after this upload; recorded in $REUPLOAD_INDEX"
    echo "$(date -u +%FT%TZ) run=$RUN_NAME attempt=$((PRIOR_ATTEMPTS + 1)) prior_ingests=$PRIOR_INGESTS log=$LOG_FILE action='manage.py dedupe_observed_mutations <experiment ids of this run> --dry-run, then without --dry-run, then rebuild_stats (pipeline/upload_scripts/README.md, Repeat uploads)'" \
        | sudo tee -a "$REUPLOAD_INDEX" > /dev/null
elif [ "$PRIOR_ATTEMPTS" -gt 0 ]; then
    step "REPEAT ATTEMPT #$((PRIOR_ATTEMPTS + 1)): no earlier attempt reached the ingest step, nothing to dedupe"
fi

sudo mkdir -p "/data/aledata/$RUN_NAME"

step "extracting from /output/$RUN_NAME"
if ! sudo find "/output/$RUN_NAME" -name '*.tar.gz' -execdir tar -xzvf '{}' -C "/data/aledata/$RUN_NAME" \; ; then
    step "extraction FAILED"
    report_status error
    exit 1
fi

step "ingesting into database: sudo docker exec aledb-web python manage.py upload /data/aledata/$RUN_NAME"
if sudo docker exec aledb-web python manage.py upload --skip-checks "/data/aledata/$RUN_NAME"; then
    step "ingest finished OK"
    report_status uploaded
else
    step "ingest FAILED (non-zero exit; OOM kill or failed experiments — see above)"
    report_status error
    exit 1
fi
