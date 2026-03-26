# AleDB Pipeline: Complete Technical Documentation

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Complete Workflow](#complete-workflow)
  - [Phase 1: Job Submission](#phase-1-job-submission)
  - [Phase 2: Input Discovery](#phase-2-input-discovery)
  - [Phase 3: Azure Batch Pool Creation](#phase-3-azure-batch-pool-creation)
  - [Phase 4: Job & Task Creation](#phase-4-job--task-creation)
  - [Phase 5: Azure Batch Execution](#phase-5-azure-batch-execution)
  - [Phase 6: Progress Monitoring](#phase-6-progress-monitoring)
  - [Phase 7: Data Upload to Database](#phase-7-data-upload-to-database)
- [Data Flow Diagram](#data-flow-diagram)
- [Key Technologies](#key-technologies)
- [Critical Configuration](#critical-configuration)
- [Important File Locations](#important-file-locations)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)
- [Performance & Costs](#performance--costs)

---

## Overview

The AleDB pipeline is a cloud-based bioinformatics workflow that automates mutation calling analysis for Adaptive Laboratory Evolution (ALE) experiments. It uses Azure Batch for distributed computing and Azure Blob Storage for data management, with results automatically imported into the AleDB Django database.

---

## System Architecture

### Core Components

**1. Django Web Application** (`aledb-web` container)
- User interface for job submission and monitoring
- REST API integration with Azure services
- Database management via Django ORM

**2. Azure Batch**
- Distributed computing platform
- Auto-scaling VM pools
- Docker-based task execution

**3. Azure Blob Storage** (3 containers)
- `data` - Input sequencing files and reference genomes
- `output` - Pipeline results (.tar.gz archives)
- `aledata` - Extracted experiment data ready for database import

**4. Blobfuse Mounts** (on VM host)
- `/output` → Azure Blob `output` container
- `/data/aledata` → Azure Blob `aledata` container
- ⚠️ Must be mounted BEFORE Docker containers start

**5. MySQL Database**
- Stores experiments, populations, mutations, projects, users

---

## Complete Workflow

### Phase 1: Job Submission

🌐 **User Interface**: `https://aledb.org/pipeline/`

📝 **User provides:**
- **Run name**: Unique identifier (e.g., `Necator_ta06_final`)
- **XPMD URL**: Metadata spreadsheet link
- **Data location**:
  - "Azure" (data already uploaded)
  - "Drive" (transfer from Google Drive first)
- **Input folder**: Directory name in Azure Blob `data` container
- **VM size**: Compute resources (16GB/32GB/64GB RAM)

⚙️ **Backend** ([pipeline/views.py:76-96](pipeline/views.py#L76-L96)):
```python
# Creates Run and Attempt database records
run, created = Run.objects.get_or_create(name=run_name, user=request.user, xpmd=xpmd)
run.status = "running"
run.save()

attempt = Attempt(run=run, vm=vm_size, input=input_dir, output=run_name)
attempt.save()

# Triggers Azure Batch pipeline
run_pipeline(input_dir, run_name, vm_size=vm_size)
```

---

### Phase 2: Input Discovery

📂 **Function**: `get_pipeline_inputs_from_directory()` ([pipeline/azure_pipeline_util.py:57-79](pipeline/azure_pipeline_util.py#L57-L79))

**Process:**

1️⃣ **Connects to Azure Blob Storage**:
```python
blob_service_client = BlobServiceClient(
    account_url="https://aledata.blob.core.windows.net/",
    credential=STORAGE_ACCOUNT_KEY
)
```

2️⃣ **Scans input folder** for `.csv` metadata files:
- Each CSV = one sample/experiment
- Example path: `data/project_name/sample1.csv`

3️⃣ **Parses CSV to identify required files**:
- `filename` - Read file 1 (e.g., `sample1_R1.fastq.gz`)
- `filename2` - Read file 2 (e.g., `sample1_R2.fastq.gz`)
- `additional read files` - Optional extra reads
- `reference file name(s)` - Reference genome(s) (e.g., `ecoli_K12.gbk`)

4️⃣ **Creates Azure Batch ResourceFile objects** for each file

📤 **Output**: Dictionary mapping CSV files to their required input files

---

### Phase 3: Azure Batch Pool Creation

🖥️ **Function**: `create_pool()` ([pipeline/azure_pipeline_util.py:82-135](pipeline/azure_pipeline_util.py#L82-L135))

**Configuration:**
- **Pool ID**: Same as run name
- **VM Image**: Custom Ubuntu 24.04 image with Docker pre-installed
  - Image path: `/subscriptions/.../ensembleamp/images/eAMP_Ubuntu24.04_open/versions/2.6.2`
- **VM Size**: User-selected (STANDARD_E2ds_V5 / E4ds_V5 / E8ds_V5)
- **Auto-scaling**: Scales up to one VM per sample, scales down on completion

**Startup Script** (runs on each VM):
```bash
# Move Docker storage from OS disk to ephemeral disk (prevents disk full)
sudo systemctl stop docker
sudo mkdir -p /mnt/docker
sudo rsync -aP /var/lib/docker/ /mnt/docker
sudo sed -i "s|^ExecStart=.*|ExecStart=/usr/bin/dockerd --data-root=/mnt/docker|" \
  /lib/systemd/system/docker.service
sudo systemctl daemon-reload
sudo systemctl start docker

# Load AMP Docker image from Azure Blob Storage
time /root/startup.sh  # Downloads and loads amp.tar
```

---

### Phase 4: Job & Task Creation

#### Job Creation

📋 [pipeline/azure_pipeline_util.py:137-145](pipeline/azure_pipeline_util.py#L137-L145)

```python
job = JobAddParameter(
    id=run_name,  # e.g., "Necator_ta06_final"
    pool_info=PoolInformation(pool_id=pool_id)
)
batch_client.job.add(job)
```

#### Task Creation (one per sample)

📋 [pipeline/azure_pipeline_util.py:209-246](pipeline/azure_pipeline_util.py#L209-L246)

For each CSV file:

1️⃣ **Generate task ID**: Sanitize sample name (e.g., `sample1.csv` → `sample1`)

2️⃣ **Build Docker command**:
```bash
docker run \
  -v $AZ_BATCH_TASK_WORKING_DIR/{input_dir}:/var/data \
  --name amp{sample_name} \
  aletechdev/amp \
  bash -i -c "source /root/.bashrc && time /amp.sh"
```
- Mounts task directory into container
- Runs `/amp.sh` (mutation calling pipeline)
- Outputs to `alemutpipe-outputs/{sample_name}.tar.gz`

3️⃣ **Configure outputs** (auto-uploaded to Azure Blob):
- **Results**: `{run_name}/{sample_name}.tar.gz` → `output` container
- **Logs**: `{run_name}/{sample_name}_out.txt` → `output` container

4️⃣ **Attach input files**: CSVs, FASTQs, reference genomes

5️⃣ **Add tasks to job**:
```python
batch_client.task.add_collection(run_name, tasks)
```

---

### Phase 5: Azure Batch Execution

⚡ **What happens on each VM:**

1. **Task starts** (status: `active` → `running`)
2. **Downloads input files** from Azure Blob `data` container
3. **Runs Docker container** with AMP pipeline:
   - Metadata validation (JSON schema)
   - Read quality control
   - Alignment to reference genome
   - Mutation calling (breseq)
   - Package results into `.tar.gz`
4. **Task completes** (status: `completed` or `failed`)
5. **Uploads outputs** to Azure Blob `output` container
6. **VM deallocates** (cost optimization)

🔄 **Parallel Processing**: Multiple samples run simultaneously on different VMs

---

### Phase 6: Progress Monitoring

🌐 **URL**: `https://aledb.org/pipeline/run/{run_id}`

📊 **View**: `run()` ([pipeline/views.py:119-157](pipeline/views.py#L119-L157))

**Features:**
- Real-time task status via Azure Batch API
- Shows for each sample:
  - Task ID (sample name)
  - Start time / End time
  - Status (active, running, completed, failed)
  - Duration
  - Link to stdout logs
- Completion counter: "X / Y completed"

**Implementation**:
```python
tasks = batch_client.task.list(job_id=run_name)
for task in tasks:
    # Display execution info, calculate duration, etc.
```

---

### Phase 7: Data Upload to Database

This is the critical step that imports results into the AleDB Django database.

#### 7.1: User Triggers Upload

🌐 **URL**: `https://aledb.org/pipeline/upload/{run_name}`

🔘 **How to access**: Click "Upload {run_name}" button on run details page

**View** ([pipeline/views.py:54-66](pipeline/views.py#L54-L66)):
```python
run = Run.objects.get(name=name)
run.status = "uploading"
run.save()

# SSH from Docker container to VM host
upload_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'root@aledb.org',
              f'/upload/webapp-upload.sh {name}']
subprocess.Popen(upload_cmd)  # Non-blocking background process

run.status = "done"
run.save()
return redirect(pipeline)
```

💡 **Why SSH from container to host?**
- Blobfuse mounts (`/output`, `/data/aledata`) are on the **host**
- Upload script needs `sudo` privileges
- Docker container SSHes to host to run privileged script

---

#### 7.2: Upload Script Execution

📜 **Script**: `/upload/webapp-upload.sh` (runs on VM host)

**Parameter**: `$1` = run name (e.g., `Necator_ta06_final`)

**Line-by-line:**

```bash
echo "Downloading: $1"
```

```bash
sudo mkdir /data/aledata/$1
```
- Creates directory in blobfuse mount
- Path: `/data/aledata/Necator_ta06_final/`
- This directory is **synced to Azure Blob `aledata` container**

```bash
sudo find /output/$1 -name '*.tar.gz' -execdir tar -xzvf '{}' -C "/data/aledata/$1" \;
```

⭐ **This is the key extraction step!**

- Searches `/output/Necator_ta06_final/` for all `.tar.gz` files
- Found files (examples):
  - `/output/Necator_ta06_final/sample1.tar.gz`
  - `/output/Necator_ta06_final/sample2.tar.gz`
- Extracts each to `/data/aledata/Necator_ta06_final/`

**Result structure:**
```
/data/aledata/Necator_ta06_final/
├── sample1/
│   ├── breseq/
│   │   ├── output.gd          # Mutation calls (GenomeDiff format)
│   │   ├── index.html
│   │   ├── summary.json
│   │   └── evidence/
│   └── metadata/
│       ├── experiment.json     # Sample metadata
│       └── ...
├── sample2/
│   ├── breseq/
│   └── metadata/
└── ...
```

```bash
sudo docker exec aledb-web python manage.py upload /data/aledata/$1
```

✅ **This registers data in the database!**

Runs Django management command inside `aledb-web` container.

---

#### 7.3: Database Import Process

⌨️ **Command**: `python manage.py upload /data/aledata/Necator_ta06_final`

📁 **Implementation**: [ale/management/commands/upload.py](ale/management/commands/upload.py)

**Workflow**:

1️⃣ **Call `upload_ale_collection()`** ([builder/ale_experiment.py:183](builder/ale_experiment.py#L183))

2️⃣ **Discover experiment directories** ([builder/ale_experiment.py:192-203](builder/ale_experiment.py#L192-L203)):
```python
def find_experiment_paths(root_path):
    # Walk directory tree
    # Find dirs with both /breseq/ and /metadata/ subdirs
    # Return list of valid experiment paths
```

3️⃣ **For each experiment**:

**a. Validate metadata** ([builder/ale_experiment.py:206-213](builder/ale_experiment.py#L206-L213)):
- Check `/metadata/experiment.json` against JSON schema
- Extract parameters: user, experiment name, project

**b. Parse breseq output** ([builder/ale_experiment.py:174-180](builder/ale_experiment.py#L174-L180)):
- Read `breseq/output.gd` (GenomeDiff format)
- Parse mutations (SNPs, insertions, deletions, etc.)

**c. Create database records**:
- **Project**: Create or get existing
- **Experiment**: Create ALE experiment record
- **Population**: Time points in evolution
- **Mutation**: Individual genetic changes
- **Lineage**: Phylogenetic relationships
- **Evidence**: Supporting data for mutations

4️⃣ **Link to users and permissions**:
- Associate with project owner
- Set public/private visibility
- Grant access permissions

🎉 **Result**: Data is now searchable and browsable on `https://aledb.org`

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER SUBMITS JOB                            │
│              https://aledb.org/pipeline/                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DJANGO WEB SERVER                             │
│              (aledb-web Docker container)                       │
│   • Creates Run & Attempt records                               │
│   • Calls run_pipeline()                                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE BATCH API                              │
│   • Creates Pool (VMs with Docker + amp.tar)                    │
│   • Creates Job (container for tasks)                           │
│   • Creates Tasks (one per sample)                              │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              AZURE BATCH VMs (running in parallel)              │
│   ┌──────────────────────────────────────────────┐              │
│   │ 1. Download inputs from Azure Blob (data)    │              │
│   │ 2. Run: docker run aletechdev/amp /amp.sh    │              │
│   │ 3. Generate output.tar.gz                    │              │
│   │ 4. Upload to Azure Blob (output)             │              │
│   └──────────────────────────────────────────────┘              │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│            AZURE BLOB STORAGE (output container)                │
│   Necator_ta06_final/                                           │
│   ├── sample1.tar.gz                                            │
│   ├── sample2.tar.gz                                            │
│   └── sample1_out.txt (logs)                                    │
└────────────────────────────┬────────────────────────────────────┘
                             ↓ (blobfuse mount)
┌─────────────────────────────────────────────────────────────────┐
│                  VM HOST: /output/                              │
│   (Blobfuse mount of Azure Blob 'output' container)            │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│          USER CLICKS "Upload Necator_ta06_final"                │
│         https://aledb.org/pipeline/upload/{run_name}            │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│   DJANGO SSHes TO HOST: /upload/webapp-upload.sh                │
│   • mkdir /data/aledata/Necator_ta06_final                      │
│   • find /output/... -name '*.tar.gz' -execdir tar -xzvf        │
│   • docker exec aledb-web python manage.py upload ...          │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              VM HOST: /data/aledata/                            │
│   Necator_ta06_final/                                           │
│   ├── sample1/                                                  │
│   │   ├── breseq/output.gd                                      │
│   │   └── metadata/experiment.json                             │
│   └── sample2/...                                               │
│   (Blobfuse mount of Azure Blob 'aledata' container)           │
└────────────────────────────┬────────────────────────────────────┘
                             ↓ (Docker volume mount)
┌─────────────────────────────────────────────────────────────────┐
│      DOCKER CONTAINER: /data/aledata/                           │
│      (Same files visible inside aledb-web container)            │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│           DJANGO MANAGEMENT COMMAND                             │
│   python manage.py upload /data/aledata/Necator_ta06_final      │
│   • Finds experiment dirs (breseq/ + metadata/)                 │
│   • Validates metadata schemas                                  │
│   • Parses breseq output.gd files                               │
│   • Creates database records                                    │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MYSQL DATABASE                               │
│   • Experiments                                                 │
│   • Populations                                                 │
│   • Mutations (SNPs, indels, etc.)                              │
│   • Projects & Users                                            │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  ALEDB WEB INTERFACE                            │
│        https://aledb.org (searchable experiments)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | Django 4.x | User interface, API, ORM |
| Container Platform | Docker | Isolated application environment |
| Cloud Compute | Azure Batch | Distributed parallel processing |
| Cloud Storage | Azure Blob Storage | Scalable object storage |
| Storage Mount | Blobfuse | Mount Azure Blobs as filesystem |
| Database | MySQL | Relational data storage |
| Pipeline Tool | Breseq | Mutation identification |
| Container Image | aletechdev/amp | Bioinformatics tools (breseq, etc.) |
| Authentication | Azure Service Principal | API access credentials |

---

## Critical Configuration

### Blobfuse Mounts

⚠️ **Must be mounted BEFORE starting Docker containers!**

```bash
# Mount output container (pipeline results)
sudo blobfuse /output \
  --tmp-path=/mnt/resource/outdirtmp \
  --config-file=/cfg/azure_pipeline_out.cfg \
  -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120

# Mount aledata container (extracted experiment data)
sudo blobfuse /data/aledata \
  --tmp-path=/mnt/resource/blobfusetmp \
  -o allow_other \
  --config-file=/cfg/azure_aledata.cfg \
  -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120
```

**Config file format** (`/cfg/azure_pipeline_out.cfg`):
```ini
accountName aledata
accountKey <Azure Storage Account Key>
containerName output
```

### Docker Volume Mount

**docker-compose-prod-asgi-host-nginx.yml**:
```yaml
services:
  web:
    volumes:
      - /data/aledata:/data/aledata  # Share blobfuse mount with container
```

### SSH Access

Django container needs SSH key to access host:
```yaml
volumes:
  - /home/muyao/.ssh:/root/.ssh  # Mount SSH keys into container
```

### Upload Scripts Deployment

```bash
# Deploy upload scripts from repo to host
sudo cp /var/www/aledb/pipeline/upload_scripts/*.sh /upload/
sudo chmod +x /upload/*.sh
sudo chown root:root /upload/*.sh
```

📚 See [pipeline/upload_scripts/README.md](upload_scripts/README.md) for details.

---

## Important File Locations

| Path | Location | Purpose |
|------|----------|---------|
| `/output/` | VM host (blobfuse) | Pipeline results from Azure Batch |
| `/data/aledata/` | VM host (blobfuse) | Extracted experiments ready for DB import |
| `/upload/*.sh` | VM host | Upload orchestration scripts |
| `/var/www/aledb/` | Docker container | Django application code |
| `/app/` | Docker container | Application root (mapped to /var/www/aledb) |

---

## Common Operations

### Monitor Pipeline Run
```bash
# View run details with task status
https://aledb.org/pipeline/run/{run_id}

# View task logs
https://aledb.org/pipeline/run/log/{job_name}/{task_id}
```

### Manual Upload (if web UI fails)
```bash
# SSH to VM host
ssh user@aledb.org

# Run upload script manually
sudo /upload/webapp-upload.sh {run_name}
```

### Manual Database Import
```bash
# From VM host
docker exec -it aledb-web python3 manage.py upload /data/aledata/{path}

# From inside container
python manage.py upload /data/aledata/{path}
```

### Check Blobfuse Mounts
```bash
# On VM host
mount | grep blobfuse
ls -la /output
ls -la /data/aledata
```

---

## Troubleshooting

### Upload button doesn't work

**Check:**
1. Blobfuse mounts are active: `mount | grep blobfuse`
2. SSH key exists: `ls /root/.ssh/aledb` (in container)
3. Upload script exists: `ls -la /upload/webapp-upload.sh` (on host)
4. Results exist in output: `ls /output/{run_name}/`

**Debug:**
```bash
# Check Django logs
docker logs aledb-web | grep "uploading.*via webapp"

# Manually run upload script
sudo /upload/webapp-upload.sh {run_name}
```

### "Create Run" fails silently (no new run appears)

**Most likely cause: Azure Batch pool quota reached (default limit: 100 pools).**

Old pools are never automatically deleted, so over time the quota fills up. The error is silently caught by the view — the page re-renders without any error message.

**Diagnose:**
```bash
# Check pool count and active VMs
sudo docker exec aledb-web python3 -c "
from pipeline.config import *
from azure.batch import BatchServiceClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials
credentials = ServicePrincipalCredentials(client_id=CLIENT_ID, secret=SECRET, tenant=TENANT_ID, resource=RESOURCE)
batch_client = BatchServiceClient(credentials, batch_url=BATCH_ACCOUNT_URL)
pools = list(batch_client.pool.list())
print(f'Active pools: {len(pools)} (quota is typically 100)')
active = [p for p in pools if p.current_dedicated_nodes > 0]
print(f'Pools with VMs: {len(active)}')
for p in active:
    print(f'  {p.id}: {p.current_dedicated_nodes} VMs')
"
```

**Fix — clean up idle pools and orphaned jobs:**
```bash
# Dry-run first (shows what would be deleted)
sudo docker exec aledb-web python3 pipeline/scripts/cleanup_batch_pools.py --dry-run
sudo docker exec aledb-web python3 pipeline/scripts/cleanup_batch_jobs.py --dry-run

# Then run for real (interactive confirmation)
sudo docker exec -it aledb-web python3 pipeline/scripts/cleanup_batch_pools.py
sudo docker exec -it aledb-web python3 pipeline/scripts/cleanup_batch_jobs.py
```

**Stop a specific run:**
```bash
sudo docker exec -it aledb-web python3 pipeline/scripts/stop_batch_run.py <run_name>
```

### Tasks fail on Azure Batch — Docker container name conflict

If a task fails and Azure Batch retries it on the same node, the retry fails with:
```
docker: Error response from daemon: Conflict. The container name "/amp{sample}" is already in use
```

The first failure is typically caused by resource limits (OOM, disk full) — check `stderr.txt` for the original error. The Docker name conflict prevents all subsequent retries from recovering.

**Fix:** The `--rm` flag was added to `docker run` in [azure_pipeline_util.py:214](pipeline/azure_pipeline_util.py#L214) to auto-remove containers after exit. See `ISSUE_docker_container_name_conflict_on_batch_retry.md` for details.

**Task retry count** is configured per-task in Azure Batch (default: 0). The pipeline currently does not set `max_task_retry_count` on tasks, so Azure Batch uses the default.

### Tasks fail on Azure Batch — other causes

**Check:**
1. Input files exist in Azure Blob `data` container
2. CSV metadata is valid
3. Reference genomes are present
4. VM has enough disk space (Docker storage moved to /mnt)

**View logs:**
```
https://aledb.org/pipeline/run/log/{job_name}/{task_id}
```

**Check Azure Batch error files:**
- `stdout.txt` — pipeline output
- `stderr.txt` — error messages (OOM, disk full, etc.)
- `fileuploaderr.txt` — output upload failures (often a symptom, not root cause)

### Data doesn't appear in database

**Check:**
1. Extracted files have correct structure (breseq/ and metadata/ dirs)
2. Metadata JSON is valid
3. Run upload command manually and check errors:
   ```bash
   docker exec -it aledb-web python manage.py upload /data/aledata/{run_name}
   ```

---

## Performance & Costs

- **VM Sizes**: Choose based on genome size
  - Prokaryotes: STANDARD_E2ds_V5 (16GB)
  - Eukaryotes: STANDARD_E4ds_V5 (32GB) or E8ds_V5 (64GB)

- **Auto-scaling**: VMs automatically scale down after tasks complete

- **Storage**: Blobfuse provides unlimited storage via Azure Blob

- **Parallel Processing**: Multiple samples run simultaneously for faster completion

---

This documentation covers the complete end-to-end workflow of the AleDB pipeline system. For questions or issues, refer to the codebase at `/var/www/aledb/` or consult the development team.
