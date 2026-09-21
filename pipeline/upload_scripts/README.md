# Upload Scripts

## Overview

These scripts run on the **VM host** (not inside Docker containers) to handle the upload phase of the AleDB pipeline. They bridge the gap between Azure Batch results and the Django database by:

1. Extracting pipeline results from blobfuse-mounted Azure Blob storage
2. Preparing data in the correct directory structure
3. Triggering Django management commands to import data into MySQL

## Scripts

### `webapp-upload.sh`
**Called by**: Django view at `/pipeline/upload/{run_name}` via SSH
**Purpose**: Main upload workflow - extracts results and imports to database
**Usage**: `/upload/webapp-upload.sh <run_name>`

**What it does**:
```bash
# 1. Create directory in blobfuse mount
mkdir -p /data/aledata/{run_name}

# 2. Extract all .tar.gz files from /output to /data/aledata
find /output/{run_name} -name '*.tar.gz' -execdir tar -xzvf '{}' -C /data/aledata/{run_name} \;

# 3. Import to database via Django management command
docker exec aledb-web python manage.py upload /data/aledata/{run_name}

# 4. Report the outcome back to the webapp's Run row ("uploaded" or "error")
docker exec aledb-web python manage.py set_run_status {run_name} uploaded
```

If extraction or the ingest fails (non-zero exit, including an OOM-killed
ingest), the script sets the run status to `error` instead, so the webapp
never shows a failed upload as completed. (`uploaded` = ingested into ALEdb;
`done` remains the Azure-Batch-analysis-finished state.)

Every invocation is logged to `/upload/logs/<run_name>_<UTC timestamp>.log`
on the VM host (step markers with timestamps + elapsed seconds, full ingest
output, failure reasons). Check there first when troubleshooting an upload. A run stuck in `uploading` (e.g. the
host script itself was killed) can be reset manually:
`docker exec aledb-web python manage.py set_run_status <run_name> error`

#### Repeat uploads (`REUPLOADS.log`)

Users are allowed to click Upload again on a run in `Error` or `Upload Completed`.
The ingest is not idempotent yet (`docs/elt-split-plan.md` step 3), so a second ingest
of the same run appends a second copy of its `ObservedMutation` rows. As an interim measure the
script detects this and records it; it does not prevent it.

- Before creating its own log the script looks for earlier logs of the same run name
  (`<run_name>_<8 digits>_<6 digits>.log`, exact match, so `foo` never picks up
  `foo_bar`'s logs) and checks whether any of them contains the
  `ingesting into database` step marker.
- An earlier attempt reached the ingest → the current log gets a
  `REPEAT ATTEMPT #n ... DEDUPE NEEDED` line and one line is appended to
  `/upload/logs/REUPLOADS.log` (UTC time, run name, attempt number, number of earlier
  ingests, path of this attempt's log).
- Earlier attempts all died before the ingest (extraction failure) → a
  `REPEAT ATTEMPT #n ... nothing to dedupe` line in the run log only.

**Operator routine** (this is the only safeguard while the idempotent-upload work, GitHub #83,
is postponed as of 2026-09-21): read `/upload/logs/REUPLOADS.log` weekly. For each new line, find
the run's experiment ids (the upload log does not print them):

```bash
docker exec aledb-web python manage.py shell -c "
from seq.models import ResequencingExperiment as R
print(sorted(set(R.objects.filter(experiment_location__startswith='<run_name>/')
    .values_list('tech_rep__isolate__flask__ale_id__ale_experiment__ale_id', flat=True))))"
```

then follow
`docs/operations/observed_mutation_dedupe.md`: `dedupe_observed_mutations <ids> --dry-run`,
the same without `--dry-run`, then `rebuild_stats`. Note the handled lines in the private
audit record; the index file itself is append-only.

**What this does not cover:**

1. **It detects, it does not prevent.** From the repeat upload until the operator's dedupe,
   the experiment carries duplicate rows: Stats-page "observed" counts and the home-page
   totals are inflated, and rebuilds are slower. The mutation table itself looks normal
   (copies land in the same cell).
2. **A sample re-analysed in a different pipeline run.** This is not a repeat attempt of
   one run, so nothing is flagged. The new run's breseq output carries a new creation
   timestamp, and the ingest looks isolates up by every field including that timestamp
   (`builder/ale_experiment.py`, `Isolate.objects.get_or_create(... reseq_date=...)`), so
   it creates a second isolate/replicate/sample record for the same ALE-flask-isolate-
   replicate numbers. Verified for the one recent case: the two records were identical in
   reference genome, breseq version, person and freezer box, and differed only in
   `reseq_date`. The dedupe command does not repair this (the rows are not exact copies
   under one sample); `load_md` then skips that sample because the replicate lookup
   matches two records. Needs an owner decision on which record to keep. Fix: stable
   identity lookup, `docs/elt-split-plan.md` step 3 item 3.
3. **Attempts older than the logs.** Per-run logs exist only since 2026-09-11. A run first
   uploaded before that has no earlier log, so its first repeat upload is not flagged.
4. **Uploads that bypass this script**: a manual `manage.py upload`, `upload.sh`,
   `transfer.sh`. Operators still must not re-ingest a folder by hand; use `load_md` for
   metadata and the per-experiment rebuild functions for derived data.
5. **Partial first attempts.** If the earlier ingest was killed part-way, the repeat
   upload duplicates the samples that had loaded and adds the ones that had not. The
   flag and the dedupe handle this correctly (only exact copies are removed), but until
   per-sample transactions exist (step 3 item 1) a sample that was cut off mid-insert
   ends up with a full set plus a partial copy, which the dedupe also removes.
6. **Renamed runs.** Detection is by run name. The same results uploaded under two run
   names land in two folders and are not flagged (see `docs/ISSUE_run_name_collisions.md`
   for the reverse problem, two runs sharing a name).

**Input**: Run name (e.g., `Necator_ta06_final`)
**Output**: Extracted experiments in `/data/aledata/{run_name}/` and database records created

---

### `upload.sh`
**Purpose**: Same as `webapp-upload.sh` but with interactive mode (`-it` flag)
**Difference**: Uses `docker exec -it` instead of `docker exec` for interactive terminal

---

### `transfer.sh`
**Purpose**: Manual fallback for ingesting a run when the blobfuse `/output` mount is unavailable or slow. Downloads the run from Azure Blob via `azcopy`, then performs the same extract → `/data/aledata` → `manage.py upload` sequence as `webapp-upload.sh`.

**Status**: **Not used by the webapp.** The Django upload view calls `webapp-upload.sh`, which reads directly from the blobfuse-mounted `/output`. `transfer.sh` is invoked manually only. As of 2026-06-03, the last observed invocation in `/root/.bash_history` is from September 2024 (`./transfer.sh Amino_A_Round_3_rerun_ettm`); no cron, systemd unit, or code path references it. The script is retained as a fallback.

**SAS token**: Previously hardcoded; now read from `AZURE_OUTPUT_CONTAINER_SAS`. Before running, source the env file on the host:
```bash
source /upload/.azure-env
./transfer.sh <run_name>
```
The script will exit immediately with a clear error if `AZURE_OUTPUT_CONTAINER_SAS` is unset.

**What it does**:
```bash
# 1. Download from Azure Blob using azcopy (SAS from env)
azcopy copy "https://aledata.blob.core.windows.net/output/$1?${AZURE_OUTPUT_CONTAINER_SAS}" . --recursive

# 2. Extract tar.gz files
find $1 -name '*.tar.gz' -execdir tar -xzvf '{}' \;

# 3. Remove tar.gz files
rm $1/*.tar.gz

# 4. Filter data
python3 ~/preuploader/filter.py $1/*/*

# 5. Move to aledata and import
mv $1 /data/aledata
docker exec -it aledb-web python manage.py upload /data/aledata/$1
```

---

## Deployment

### Requirements

1. **Blobfuse mounts must be active**:
   ```bash
   # Check mounts
   mount | grep blobfuse

   # Should see:
   # blobfuse on /output
   # blobfuse on /data/aledata
   ```

2. **Docker container must be running**:
   ```bash
   docker ps | grep aledb-web
   ```

3. **SSH access from container to host**:
   - Django container has SSH keys mounted at `/root/.ssh/`
   - Can execute: `ssh root@aledb.org <command>`

### Installation

**On VM host**, copy these scripts to `/upload/`:

```bash
# Create directory
sudo mkdir -p /upload

# Copy scripts from repo
sudo cp /var/www/aledb/pipeline/upload_scripts/*.sh /upload/

# Set permissions
sudo chmod +x /upload/*.sh
sudo chown root:root /upload/*.sh
```

### Verification

Test that the scripts work:

```bash
# From VM host
sudo /upload/webapp-upload.sh <test_run_name>

# Or from Django container (testing SSH)
ssh root@aledb.org /upload/webapp-upload.sh <test_run_name>
```

---

## How Django Calls These Scripts

**View**: `pipeline/views.py:upload()`

```python
@login_required(login_url='/accounts/login/')
def upload(request, name):
    run = Run.objects.get(name=name)
    if run.status == "uploading":
        return redirect(pipeline)  # already running; ignore repeat clicks
    run.status = "uploading"
    run.save()

    # SSH from container to host and run script; the script reports the final
    # "uploaded"/"error" status back via `manage.py set_run_status` when it exits.
    upload_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'root@aledb.org',
                  f'/upload/webapp-upload.sh {name}']
    subprocess.Popen(upload_cmd)  # Non-blocking async execution
    return redirect(pipeline)
```

**Why SSH from container to host?**
- Blobfuse mounts (`/output`, `/data/aledata`) exist on the **host**, not in container
- Scripts need `sudo` privileges for filesystem operations
- Container doesn't have direct access to blobfuse mount points

---

## Directory Structure

After successful execution, the data structure is:

```
/output/{run_name}/                           # Blobfuse mount (Azure Blob 'output')
├── sample1.tar.gz                            # Pipeline results
├── sample2.tar.gz
└── sample1_out.txt                           # Logs

/data/aledata/{run_name}/                     # Blobfuse mount (Azure Blob 'aledata')
├── sample1/                                  # Extracted experiment
│   ├── breseq/
│   │   ├── output.gd                         # Mutation calls
│   │   └── ...
│   └── metadata/
│       ├── experiment.json                   # Sample metadata
│       └── ...
├── sample2/
│   ├── breseq/
│   └── metadata/
└── ...
```

The Django container sees `/data/aledata/` via volume mount and can run:
```bash
python manage.py upload /data/aledata/{run_name}
```

---

## Troubleshooting

### Script not found
```bash
# Check if script exists on host
ls -la /upload/

# If missing, redeploy from repo
sudo cp /var/www/aledb/pipeline/upload_scripts/*.sh /upload/
sudo chmod +x /upload/*.sh
```

### Permission denied
```bash
# Scripts need execute permissions
sudo chmod +x /upload/*.sh

# May need root ownership
sudo chown root:root /upload/*.sh
```

### Blobfuse mount not found
```bash
# Check mounts
mount | grep blobfuse

# Remount if needed
sudo blobfuse /output --config-file=/cfg/azure_pipeline_out.cfg
sudo blobfuse /data/aledata --config-file=/cfg/azure_aledata.cfg -o allow_other
```

### SSH fails from container
```bash
# Check SSH keys are mounted
docker exec aledb-web ls -la /root/.ssh/

# Test SSH connection
docker exec aledb-web ssh root@aledb.org echo "Connection successful"
```

### Data not imported to database
```bash
# Check extracted structure
ls -la /data/aledata/{run_name}/

# Each sample should have breseq/ and metadata/ subdirs
# Manually run import to see errors
docker exec -it aledb-web python manage.py upload /data/aledata/{run_name}
```

---

## Version Control

**Important**: These scripts are stored in the git repository at `pipeline/upload_scripts/` but must be **deployed** to `/upload/` on the VM host to function.

**After making changes**:
1. Edit scripts in `pipeline/upload_scripts/`
2. Commit to git
3. Deploy to host: `sudo cp pipeline/upload_scripts/*.sh /upload/`
4. Set permissions: `sudo chmod +x /upload/*.sh`

---

## Related Documentation

- **Full Pipeline Docs**: `pipeline/PIPELINE_DOCUMENTATION.md`
- **System Overview**: `pipeline/PIPELINE_SYSTEM_OVERVIEW.md`
- **Django Upload View**: `pipeline/views.py:upload()`
- **Management Command**: `ale/management/commands/upload.py`
- **Import Logic**: `builder/ale_experiment.py`
