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
LOG_FILE="$LOG_DIR/${RUN_NAME}_$(date -u +%Y%m%d_%H%M%S).log"
exec > >(sudo tee -a "$LOG_FILE") 2>&1

report_status() {
    sudo docker exec aledb-web python manage.py set_run_status --skip-checks "$RUN_NAME" "$1"
}

step() {
    echo "=== [$(date -u +%FT%TZ)] (+${SECONDS}s) $* ==="
}

step "upload started for $RUN_NAME"
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
