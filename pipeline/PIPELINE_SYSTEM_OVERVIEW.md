# AleDB Pipeline System Overview

> **Quick Reference** for developers and AI agents working with the AleDB pipeline system

---

## Purpose

Automated cloud-based bioinformatics pipeline for mutation calling analysis in Adaptive Laboratory Evolution (ALE) experiments. Processes genomic sequencing data using Azure Batch distributed computing.

---

## Architecture Summary

### Components

| Component | Technology | Details |
|-----------|-----------|---------|
| **Web Interface** | Django + Docker | `aledb-web` container at `/var/www/aledb/` |
| **Compute** | Azure Batch | Auto-scaling VMs running Docker containers |
| **Storage** | Azure Blob + Blobfuse | 3 containers mounted as filesystems |
| **Database** | MySQL | Experiments, mutations, populations, projects |

### Azure Blob Containers

| Container | Purpose | Content |
|-----------|---------|---------|
| `data` | Input files | FASTQs, reference genomes, CSV metadata |
| `output` | Pipeline results | `.tar.gz` archives from breseq analysis |
| `aledata` | Extracted experiments | Ready for database import |

### Critical Mounts (on VM host)

```
/output          → Azure Blob 'output' container (blobfuse)
/data/aledata    → Azure Blob 'aledata' container (blobfuse)
                   Both shared with Docker via volume mounts
```

---

## Workflow Phases

### 1. Job Submission

| Aspect | Details |
|--------|---------|
| **Endpoint** | `POST /pipeline/` |
| **Handler** | `pipeline/views.py:pipeline()` |
| **Inputs** | run_name, xpmd_url, data_location, input_folder, vm_size |
| **Creates** | Run and Attempt database records |
| **Triggers** | `run_pipeline()` function |

---

### 2. Input Discovery

**Function**: `get_pipeline_inputs_from_directory()` in `pipeline/azure_pipeline_util.py`

**Process**:
1. Scans Azure Blob `data/{input_folder}` for `.csv` files
2. Each CSV = one sample with metadata (read files, reference genome)
3. Returns ResourceFile objects for Azure Batch

---

### 3. Azure Batch Setup

#### Pool Creation
**Function**: `create_pool()` in `pipeline/azure_pipeline_util.py`

```yaml
VM Image: Custom Ubuntu 24.04 with Docker
Auto-scales: 1 VM per sample
Startup: Moves Docker to ephemeral disk, loads aletechdev/amp image
```

#### Job Creation
**Function**: `create_job()`

```yaml
Job ID: run_name (e.g., "Necator_ta06_final")
Purpose: Container for tasks
```

#### Task Creation
**One task per sample**:

```bash
Command: docker run -v $WORKING_DIR:/var/data aletechdev/amp bash -i -c "/amp.sh"
Input: CSV + FASTQs + reference genomes from 'data' container
Output: {run_name}/{sample_name}.tar.gz uploaded to 'output' container
```

---

### 4. Execution

**Per VM**:
1. Downloads inputs from Azure Blob `data`
2. Runs Docker container with breseq mutation calling pipeline
3. Generates `.tar.gz` archive:
   - `breseq/output.gd` - Mutation calls (GenomeDiff format)
   - `metadata/experiment.json` - Sample metadata
4. Uploads to Azure Blob `output/{run_name}/{sample_name}.tar.gz`
5. VM deallocates

---

### 5. Monitoring

| Aspect | Details |
|--------|---------|
| **Endpoint** | `GET /pipeline/run/{run_id}` |
| **Handler** | `pipeline/views.py:run()` |
| **Displays** | Real-time task status from Azure Batch API |
| **Shows** | Task ID, start/end time, status, duration, logs |

---

### 6. Upload to Database

| Aspect | Details |
|--------|---------|
| **Endpoint** | `GET /pipeline/upload/{run_name}` |
| **Handler** | `pipeline/views.py:upload()` |

**Process**:

**Step 1**: Django SSHes from container to VM host
```bash
ssh root@aledb.org /upload/webapp-upload.sh {run_name}
```

**Step 2**: Host script runs
```bash
# Create directory in blobfuse mount
mkdir /data/aledata/{run_name}

# Extract all tar.gz files
find /output/{run_name} -name '*.tar.gz' -execdir tar -xzvf '{}' -C /data/aledata/{run_name} \;

# Import to database
docker exec aledb-web python manage.py upload /data/aledata/{run_name}
```

**Step 3**: Management command (`ale/management/commands/upload.py`)
- Scans for dirs with `breseq/` and `metadata/` subdirs
- Validates metadata JSON against schema
- Parses breseq `output.gd` files
- Creates database records: Experiment, Population, Mutation, etc.

**Result**: Data searchable on aledb.org

---

## Data Flow

```
User Form → Django → Azure Batch API → VMs (parallel) →
Azure Blob (output) → Blobfuse (/output) → Extract →
Blobfuse (/data/aledata) → Docker volume → Django manage.py → MySQL
```

---

## Key Files

### Django Views
- `pipeline/views.py` - Web endpoints (pipeline, run, upload)
- `pipeline/urls.py` - URL routing

### Azure Integration
- `pipeline/azure_pipeline_util.py` - Batch job orchestration
- `pipeline/azure_batch_status_util.py` - Task monitoring
- `pipeline/azure_upload_util.py` - Blob storage operations
- `pipeline/config.py` - Azure credentials and container names

### Data Import
- `ale/management/commands/upload.py` - CLI entry point
- `builder/ale_experiment.py` - Database import logic

### Host Scripts (deployed to `/upload/` on VM)
- `pipeline/upload_scripts/webapp-upload.sh` - Main upload workflow (extraction + import)
- `pipeline/upload_scripts/upload.sh` - Interactive version of webapp-upload.sh
- `pipeline/upload_scripts/transfer.sh` - Alternative upload using azcopy
- `pipeline/upload_scripts/README.md` - Deployment and usage instructions
- **Deployed location**: `/upload/` on VM host (not in container)

---

## Database Models

| Model | Purpose |
|-------|---------|
| `Run` | Pipeline execution record |
| `Attempt` | Individual run attempt with parameters |
| `Experiment` | ALE experiment (imported after upload) |
| `Population` | Evolution time point |
| `Mutation` | Genetic changes (SNPs, indels, etc.) |

---

## Important Paths

| Path | Location | Purpose |
|------|----------|---------|
| `/output/` | VM host (blobfuse) | Pipeline results (.tar.gz) |
| `/data/aledata/` | VM host + container (blobfuse + volume) | Extracted experiments |
| `/upload/*.sh` | VM host | Upload orchestration scripts |
| `/var/www/aledb/` | Docker container | Django application |

---

## Configuration Requirements

### Blobfuse Mounts

⚠️ **Must exist before Docker starts**

```bash
# Mount output container (pipeline results)
blobfuse /output --config-file=/cfg/azure_pipeline_out.cfg \
  -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120

# Mount aledata container (extracted experiment data)
blobfuse /data/aledata --config-file=/cfg/azure_aledata.cfg \
  -o allow_other -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120
```

### Docker Compose Volumes

```yaml
volumes:
  - /data/aledata:/data/aledata  # Share blobfuse mount
  - /home/muyao/.ssh:/root/.ssh  # SSH keys for host access
```

### Upload Scripts Deployment

```bash
# Deploy upload scripts from repo to host
sudo cp /var/www/aledb/pipeline/upload_scripts/*.sh /upload/
sudo chmod +x /upload/*.sh
sudo chown root:root /upload/*.sh
```

📚 **Note**: Scripts in `pipeline/upload_scripts/` are version controlled but must be deployed to `/upload/` on the VM host to function. See `pipeline/upload_scripts/README.md` for details.

---

## Common Operations

| Operation | Command/URL |
|-----------|-------------|
| **Submit job** | POST to `/pipeline/` with form data |
| **Monitor progress** | GET `/pipeline/run/{run_id}` |
| **Import to database** | GET `/pipeline/upload/{run_name}` or `docker exec aledb-web python manage.py upload /data/aledata/{path}` |
| **View logs** | GET `/pipeline/run/log/{job_name}/{task_id}` |
| **Check blobfuse** | `mount \| grep blobfuse` |
| **Manual upload** | `sudo /upload/webapp-upload.sh {run_name}` |

---

## Troubleshooting

### Upload fails
- Check blobfuse mounts: `mount | grep blobfuse`
- Check SSH keys: `ls /root/.ssh/aledb` (in container)
- Check upload script: `ls -la /upload/webapp-upload.sh` (on host)

### Tasks fail
- Check Azure Blob inputs exist
- Validate CSV metadata
- Check VM disk space

### No data in database
- Check extracted structure (breseq/ + metadata/)
- Run upload manually: `docker exec -it aledb-web python manage.py upload /data/aledata/{run_name}`

---

## Performance Notes

| Aspect | Details |
|--------|---------|
| **Auto-scaling** | 1 VM per sample for parallelism |
| **VM sizes** | E2ds_V5 (16GB) for prokaryotes, E4ds_V5 (32GB) or E8ds_V5 (64GB) for eukaryotes |
| **Background upload** | `subprocess.Popen()` runs async, status marked "done" immediately |
| **Blobfuse** | Provides Azure Blob as POSIX filesystem for fast file operations |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 4.x + Django ORM |
| **Containerization** | Docker |
| **Cloud Compute** | Azure Batch |
| **Cloud Storage** | Azure Blob Storage |
| **Storage Mount** | Blobfuse |
| **Database** | MySQL |
| **Bioinformatics** | Breseq (in aletechdev/amp Docker image) |
| **Auth** | Azure Service Principal |

---

**For detailed documentation**, see [PIPELINE_DOCUMENTATION.md](PIPELINE_DOCUMENTATION.md)
