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
mkdir /data/aledata/{run_name}

# 2. Extract all .tar.gz files from /output to /data/aledata
find /output/{run_name} -name '*.tar.gz' -execdir tar -xzvf '{}' -C /data/aledata/{run_name} \;

# 3. Import to database via Django management command
docker exec aledb-web python manage.py upload /data/aledata/{run_name}
```

**Input**: Run name (e.g., `Necator_ta06_final`)
**Output**: Extracted experiments in `/data/aledata/{run_name}/` and database records created

---

### `upload.sh`
**Purpose**: Same as `webapp-upload.sh` but with interactive mode (`-it` flag)
**Difference**: Uses `docker exec -it` instead of `docker exec` for interactive terminal

---

### `transfer.sh`
**Purpose**: Alternative upload script using azcopy for downloading from Azure Blob
**Status**: Contains azcopy download logic (may be outdated - uses hardcoded SAS token)

**What it does**:
```bash
# 1. Download from Azure Blob using azcopy
azcopy copy "https://aledata.blob.core.windows.net/output/$1?<SAS_TOKEN>" . --recursive

# 2. Extract tar.gz files
find $1 -name '*.tar.gz' -execdir tar -xzvf '{}' \;

# 3. Remove tar.gz files
rm $1/*.tar.gz

# 4. Filter data (optional - currently commented out)
python3 ~/preuploader/filter.py $1/*/*

# 5. Move to aledata and import
mv $1 /data/aledata
docker exec -it aledb-web python manage.py upload /data/aledata/$1
```

**Note**: This script may be deprecated in favor of blobfuse mounts. The SAS token is hardcoded and may expire.

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
    run.status = "uploading"
    run.save()

    # SSH from container to host and run script
    upload_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'root@aledb.org',
                  f'/upload/webapp-upload.sh {name}']
    subprocess.Popen(upload_cmd)  # Non-blocking async execution

    run.status = "done"
    run.save()
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
