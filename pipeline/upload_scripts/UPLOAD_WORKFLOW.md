# AleDB Upload Workflow

This document describes the workflow for registering AMP pipeline results into the AleDB database.

## Overview

The upload process takes breseq/GATK output from the AMP pipeline and registers mutations, evidence, and metadata into the AleDB Django database for visualization in the web UI.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AMP Pipeline Output                                │
│                                                                              │
│  ┌── PARSED DURING UPLOAD ─────────────────────────────────────────────────┐ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │ │
│  │  │ annotated.gd│  │ index.html  │  │ summary.html│                      │ │
│  │  │ (mutations) │  │ (evidence)  │  │ (stats)     │                      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                      │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │ │
│  │  │ metadata/*.csv - project, owner, AFIR, strain, media conditions │    │ │
│  │  └─────────────────────────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌── REFERENCED ONLY (served at runtime) ──────────────────────────────────┐ │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │ │
│  │  │ gatk/evidence/*.html, *.png - filenames stored, served from disk│    │ │
│  │  └─────────────────────────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         webapp-upload.sh                                     │
│         sudo docker exec aledb-web python manage.py upload <path>           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Upload Processing                                    │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐   │
│  │ GD File Parsing   │  │ HTML Parsing      │  │ Metadata Integration  │   │
│  │ (gdparse.py)      │  │ (BeautifulSoup)   │  │ (metadata/parser.py)  │   │
│  └───────────────────┘  └───────────────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Database Registration                                │
│  ┌──────────────┐ ┌──────────────────┐ ┌────────────────────────────────┐  │
│  │ Mutation     │ │ ObservedMutation │ │ UnassignedMissingCovEvidence   │  │
│  └──────────────┘ └──────────────────┘ └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Post-Processing                                        │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐   │
│  │ Converge Analysis │  │ Fixation Analysis │  │ Dashboard Rebuild     │   │
│  └───────────────────┘  └───────────────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Upload Script Execution

### Entry Point: `webapp-upload.sh`

```bash
# Extract experiment data
sudo mkdir /data/aledata/$1
sudo find /output/$1 -name '*.tar.gz' -execdir tar -xzvf '{}' -C "/data/aledata/$1" \;

# Execute Django upload command
sudo docker exec aledb-web python manage.py upload /data/aledata/$1
```

### Expected Directory Structure

```
/data/aledata/<experiment>/
├── breseq/
│   └── <sample_name>/
│       └── output/
│           ├── annotated.gd      # Annotated GenomeDiff file
│           ├── index.html        # Mutation report with evidence links
│           └── summary.html      # Sequencing statistics
├── gatk/
│   └── <sample_name>/
│       └── evidence/
│           ├── <position>.html   # Per-position variant details (served at runtime, NOT parsed)
│           └── <position>.png    # Coverage plots for AMP/large DEL (served at runtime, NOT parsed)
├── metadata/
│   └── <afir>.csv                # Per-sample metadata CSV files
└── <afir>.gd                     # Ensemble GD files (optional)
```

---

## Metadata CSV File Format

**File:** `metadata/parser.py`

Each sample requires a CSV file in the `metadata/` directory with key-value pairs. The CSV is parsed at two stages:

### Stage 1: Pre-Upload - Experiment Parameter Extraction

**Function:** `extract_experiment_parameters()`

Extracts experiment-level parameters to create/find the experiment:

| CSV Key | Description |
|---------|-------------|
| `project` | Project name for grouping experiments |
| `owner` | Creator/owner username |
| `experiment/subproject` | Experiment name/label |

### Stage 2: Post-Upload - Sample Metadata Integration

**Function:** `parse_metadata_post_experiment_upload()`

Links detailed metadata to each sample after mutations are registered:

| CSV Key | Description | Updates Model |
|---------|-------------|---------------|
| `A` | ALE number | - |
| `F` | Flask number | - |
| `I` | Isolate number | - |
| `R` | Technical replicate number | - |
| `taxonomy id` | NCBI taxonomy ID | `AleId.strain` |
| `starting strain` | Strain description | `AleId.description` |
| `seqencing library prep kit manufacturer` | Library prep kit | `Isolate.library_prep` |
| `sequencing library prep kit cycles` | PCR cycles | `Isolate.library_prep` |
| `medium description` | Experiment details | `TechnicalReplicate.description` |
| `medium derived from` | Base media (e.g., M9) | `Media.description` |
| `environmental conditions` | JSON with `temp`, etc. | `Media.temperature` |
| `media components` | JSON with nutrient sources | `Media.*_source` fields |

### Media Components JSON Structure

The `media components` field contains a JSON object:

```json
{
  "carbon source": "glucose",
  "nitrogen source": "NH4Cl",
  "phosphorus source": "KH2PO4",
  "sulfur source": "MgSO4",
  "calcium source": "CaCl2",
  "electron acceptor": "O2",
  "supplement": "thiamine"
}
```

### Environmental Conditions JSON Structure

The `environmental conditions` field contains:

```json
{
  "temp": 37
}
```

### Example CSV File

```csv
project,MyProject
owner,John Smith
experiment/subproject,Glucose-Evolution
A,1
F,2
I,3
R,1
taxonomy id,511145
starting strain,E. coli K-12 MG1655
medium derived from,M9
medium description,M9 minimal with glucose
environmental conditions,"{""temp"": 37}"
media components,"{""carbon source"": ""glucose"", ""nitrogen source"": ""NH4Cl""}"
seqencing library prep kit manufacturer,Illumina
sequencing library prep kit cycles,8
```

### Validation

Metadata CSV files are validated against a JSON schema before processing:
```python
is_valid(metadata_path, "metadata/xpmdvalidator/Json_schema.json")
```

---

## Step 2: Django Management Command

**File:** `ale/management/commands/upload.py`

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        for path in options['path(s)']:
            upload_ale_collection(path)
```

This calls `upload_ale_collection()` which discovers experiment paths and processes each one.

---

## Step 3: Experiment Discovery

**File:** `builder/ale_experiment.py`

### Functions:
- `upload_ale_collection(root_path)` - Entry point for batch upload
- `find_experiment_paths(root_path)` - Discovers experiments by looking for `/breseq` directories with adjacent `/metadata`
- `upload_ale_experiment(experiment_path)` - Processes a single experiment

### Metadata Validation
Before processing, metadata is validated against a JSON schema:
```python
if not is_valid(metadata_path, "metadata/xpmdvalidator/Json_schema.json"):
    return False
```

---

## Step 4: Experiment Creation

**File:** `builder/ale_experiment.py`

### Function: `create_ensemble_ale_experiment()`

Creates or retrieves database records for:

| Model | Description |
|-------|-------------|
| `Project` | Groups related experiments |
| `AleExperiment` | Main experiment record |
| `Instrument` | Sequencing instrument used |
| `Media` | Growth media conditions |
| `FreezerBox` | Sample storage location |

### Sample Processing Loop

For each sample in `breseq/<sample_name>/`:

1. Parse sample name to extract AFIR components:
   - **A**le number
   - **F**lask number
   - **I**solate number
   - **R**eplicate number

2. Create hierarchy records:
   - `AleId` → `Flask` → `Isolate` → `TechnicalReplicate`

3. Call `_create_and_commit_ale_entry()` for mutation processing

---

## Step 5: GD File Parsing

**File:** `builder/gdparse/gdparse/gdparse.py`

### GDParser Class

Parses GenomeDiff format files and extracts:

#### Metadata Fields
| Key | Description |
|-----|-------------|
| `GENOME_DIFF` | File version |
| `AUTHOR` | Creator (breseq version) |
| `COMMAND` | Execution command (determines clonal/population) |
| `REFSEQ` | Reference sequence used |
| `CREATED` | Processing date |

#### Mutation Types
| Type | Description |
|------|-------------|
| `SNP` | Single nucleotide polymorphism |
| `SUB` | Multiple base substitution |
| `DEL` | Deletion |
| `INS` | Insertion |
| `MOB` | Mobile element insertion |
| `AMP` | Amplification (from CNVnator) |
| `CON` | Gene conversion |
| `INV` | Inversion |

#### Evidence Types
| Type | Description |
|------|-------------|
| `RA` | Read alignment |
| `MC` | Missing coverage |
| `JC` | New junction |
| `UN` | Unknown base |

---

## Step 6: Mutation Database Registration

**File:** `builder/upload.py`

### Function: `add_breseq_results()`

#### 6.1 Create ResequencingExperiment

```python
reseq = ResequencingExperiment.objects.get_or_create(
    location=breseq_folder,
    gatk_location=gatk_folder,
    sample_name=sample_name,
    tech_rep_id=technical_replicate_id
)
```

Parses `summary.html` for statistics:
- `reads` - Total read count
- `average_read_length` - Mean read length
- `percentage_mapped` - Mapping percentage
- `mean_coverage` - Average coverage depth

#### 6.2 Register Mutations

**Function:** `_database_mutations()`

For each mutation in the GD file:

1. **Create Mutation record:**
```python
Mutation.objects.get_or_create(
    position=mutation_dict['position'],
    gene=gene_list_str,
    reseq_reference=mutation_dict['seq_id'],
    product=gene_product,
    feature_length=size,          # For AMP/DEL/INV/etc.
    sequence_change=sequence_str,
    mutation_type=mutation_dict['type'],
    protein_change=protein_str
)
```

2. **Create ObservedMutation record:**
```python
ObservedMutation(
    sequencing_experiment=seq_experiment,
    mutation=mut,
    breseq_present=True,
    gatk_present=True,
    evidence=html_evidence,        # From index.html
    gatk_evidence=gatk_file_path,  # .html or .png
    frequency=breseq_freq,
    frequency_gatk=gatk_freq
)
```

#### 6.3 Evidence Linking

**Breseq Evidence:**
- Extracted from `index.html` as HTML snippets
- Stored directly in `ObservedMutation.evidence` field

**GATK Evidence:**
- **NOT parsed or processed during upload**
- Only the filename is stored (not file contents)
- Files are served directly from disk when viewed in the web UI

| Mutation Type | GATK Evidence File | Content |
|--------------|-------------------|---------|
| `AMP` | `<position>.png` | Coverage plot from CNVnator |
| Large `DEL` (>190bp) | `<position>.png` | Coverage plot |
| Other (SNP, INS, etc.) | `<position>.html` | GATK variant call details |

**Database Storage:**
```python
# Only stores the filename, not the file contents
gatk_evidence = str(position) + '.png'  # or '.html'

ObservedMutation(
    gatk_evidence=gatk_evidence,        # e.g., "12345.html"
    frequency_gatk=frequencies[1]       # from GD file
)

ResequencingExperiment(
    gatk_location=gatk_folder           # e.g., "/experiment/gatk/1-2-3-1/"
)
```

**File Serving at Runtime** (`evidence/views.py`):
```python
# Full path constructed when user views evidence:
# /data/aledata/ + gatk_location + evidence/ + gatk_evidence
evidence_html = open(
    DATA_MOUNT_LOCATION + resequencing_experiment.gatk_location +
    'evidence/' + observed_mutation.gatk_evidence
).read()
```

#### 6.4 Frequency Extraction

Frequencies are extracted from GD file attributes:
- `frequency_breseq` or `frequency_output` → breseq frequency
- `frequency_GATK_CNVnator` → GATK/CNVnator frequency

#### 6.5 Unassigned Missing Coverage

**Function:** `_database_unassigned_missing_coverage()`

Parses `index.html` for unassigned missing coverage evidence and creates `UnassignedMissingCoverageEvidence` records with:
- Position and size
- Evidence URLs (reads left/right, coverage)
- Gene and description

---

## Step 7: HTML Evidence Parsing

**File:** `builder/upload.py`

### BeautifulSoup Parsing

```python
def _get_beautifulsoup_html(output_folder, html_file_name):
    with open(output_file_path) as infile:
        bs_html_file = BeautifulSoup(infile, "html.parser")
    return bs_html_file
```

### Mutation Table Parsing

From `index.html`:
- Locates mutation table by `mutation_header_row` class
- Extracts rows based on sample type:
  - Clonal: `normal_table_row`
  - Population: `normal_table_row` + `polymorphism_table_row`
- Retrieves evidence column HTML for each mutation

---

## Step 8: Post-Upload Processing

**File:** `builder/ale_experiment.py`

After all samples are processed:

### 8.1 Converge Mutation Analysis

```python
rebuild_converge_mutations(experiment.ale_id)
```

- Identifies mutations that appear across multiple independent ALE lineages
- Suggests convergent evolution targets
- Creates `ConvergeMutation` records

### 8.2 Fixation Analysis

```python
rebuild_fixated_mutations(experiment.ale_id)
```

- Identifies mutations that reached fixation (100% frequency)
- Tracks fixation across flask series
- Creates `FixatedMutation` records

### 8.3 Static Data Generation

```python
generate_static_data(experiment.ale_id)
```

- Pre-computes statistics for dashboard display
- Creates `StaticData` records

### 8.4 Dashboard Rebuild

```python
rebuild_dashboard_data()
```

- Updates dashboard caches and summary data
- Creates timeline events for experiment creation

### 8.5 Metadata Integration

```python
metadata.parser.parse_metadata_post_experiment_upload(metadata_path, experiment.ale_id)
```

- Links additional metadata to experiment
- Updates sample annotations

---

## Database Schema Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Project      │────▶│  AleExperiment  │────▶│     AleId       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │     Flask       │
                                                └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │    Isolate      │
                                                └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │TechnicalReplicate│
                                                └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Mutation     │◀────│ObservedMutation │────▶│ResequencingExp  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │
        ▼
┌─────────────────┐     ┌─────────────────┐
│FixatedMutation  │     │ConvergeMutation │
└─────────────────┘     └─────────────────┘
```

---

## How Mutation Sources Are Merged

The system currently supports two mutation calling sources: **Breseq** and **GATK/CNVnator**. Understanding how these are merged is essential for adding additional sources.

### Mutation Merging Flow (AMP Pipeline)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AMP Pipeline: Mutation Merging                       │
│                                                                              │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────────────────┐│
│  │   BRESEQ    │         │    GATK     │         │       CNVnator          ││
│  │ output.gd   │         │  VCF → GD   │         │   TSV → amp.gd          ││
│  └──────┬──────┘         └──────┬──────┘         └───────────┬─────────────┘│
│         │                       │                            │              │
│         │                       └────────────┬───────────────┘              │
│         │                                    ▼                              │
│         │                         ┌─────────────────────┐                   │
│         │                         │  GATK_CNVnator.gd   │                   │
│         │                         │ (gdtools union)     │                   │
│         │                         └──────────┬──────────┘                   │
│         │                                    │                              │
│         └──────────────────┬─────────────────┘                              │
│                            ▼                                                │
│                 ┌─────────────────────┐                                     │
│                 │  gdtools COMPARE    │                                     │
│                 │  → <afir>.gd        │                                     │
│                 │  (merged mutations) │                                     │
│                 └─────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Configuration (AMP: `alemutpipe/util/compare.py`)

```python
FIELDS_TO_COMPARE = {
    'breseq': 'output/output.gd',
    'gatk': 'GATK_CNVnator.gd'
}
```

### Merge Command

```bash
gdtools COMPARE --add-html-fields -f GD -o <afir>.gd \
    -r reference.gbk \
    breseq/<sample>/output/output.gd \
    gatk/<sample>/GATK_CNVnator.gd
```

### Resulting Merged GD File

Each mutation gets frequency attributes from each source:
```
#=GENOME_DIFF 1.0
SNP  1  .  NC_000913  12345  A  frequency_breseq=0.95  frequency_GATK_CNVnator=0.92
AMP  2  .  NC_000913  50000  5000  2  frequency_GATK_CNVnator=2.0
DEL  3  .  NC_000913  67890  500  frequency_breseq=1.0
```

### Frequency Extraction (AleDB: `builder/upload.py`)

```python
def _get_mutation_freq(mutation_dict):
    frequency = DEFAULT_CLONAL_FREQ      # breseq frequency
    frequency_gatk = DEFAULT_GATK_FREQ   # GATK/CNVnator frequency

    for key in mutation_dict.keys():
        if key.startswith('frequency_'):
            # Breseq frequency
            if key.endswith('breseq') or key.endswith('output'):
                frequency = mutation_dict[key]
            # GATK/CNVnator frequency
            elif key.endswith('GATK_CNVnator'):
                frequency_gatk = mutation_dict[key]

    return [frequency, frequency_gatk]
```

### Current Database Model (AleDB: `seq/models.py`)

```python
class ObservedMutation(models.Model):
    # Source presence flags
    breseq_present = models.BooleanField(null=True)
    gatk_present = models.BooleanField(null=True)

    # Frequencies from each source
    frequency = models.DecimalField(...)       # breseq
    frequency_gatk = models.DecimalField(...)  # GATK/CNVnator

    # Evidence links
    evidence = models.CharField(...)           # breseq HTML snippet
    gatk_evidence = models.CharField(...)      # filename (.html or .png)
```

---

## Adding a Third Mutation Source

To add a new variant calling tool (e.g., "DeepVariant", "Freebayes", etc.), modifications are required in both the AMP pipeline and AleDB.

### Step 1: AMP Pipeline Modifications

#### 1.1 Create New Tool Module

Create a new file `alemutpipe/util/newtool.py`:

```python
import subprocess
import AMPconfig

def run_newtool(bam_input, reference, output_path):
    """
    Run the new variant caller and convert output to GD format.

    The key requirement is to produce a GD file with frequency attributes
    using the naming convention: frequency_<toolname>=<value>
    """

    # 1. Run the variant caller (produces VCF or other format)
    vcf_path = output_path + "/newtool.vcf"
    cmd = f"newtool call -i {bam_input} -r {reference} -o {vcf_path}"
    subprocess.call(cmd, shell=True)

    # 2. Add frequency information to VCF INFO field
    # Format: frequency_newtool=0.95
    updated_vcf = add_frequency_to_vcf(vcf_path)

    # 3. Convert VCF to GD format using gdtools
    gd_path = output_path + "/newtool.gd"
    confpath = AMPconfig.BRESEQ_PATH
    cmd = f"{confpath}gdtools VCF2GD -o {gd_path} {updated_vcf}"
    subprocess.call(cmd, shell=True)

    # 4. Normalize the GD file
    normalized_gd = output_path + "/newtool_normalized.gd"
    cmd = f"{confpath}gdtools normalize -r {reference} -o {normalized_gd} {gd_path}"
    subprocess.call(cmd, shell=True)

    return normalized_gd


def add_frequency_to_vcf(vcf_path):
    """
    Add frequency_newtool attribute to VCF INFO field.
    This is critical for the frequency to be recognized during upload.
    """
    output_path = vcf_path.replace('.vcf', '.updated.vcf')

    with open(vcf_path, 'r') as infile, open(output_path, 'w') as outfile:
        for line in infile:
            if line.startswith('#'):
                outfile.write(line)
            else:
                fields = line.strip().split('\t')
                # Extract allele frequency from sample field
                sample_data = fields[-1].split(':')
                ad = sample_data[1].split(',')  # Allele depths
                dp = int(sample_data[2])        # Total depth
                if dp > 0:
                    freq = round(int(ad[1]) / dp, 3)
                else:
                    freq = 0

                # Add frequency to INFO field
                info = fields[7]
                fields[7] = f"frequency_newtool={freq};{info}"
                outfile.write('\t'.join(fields) + '\n')

    return output_path
```

#### 1.2 Update compare.py

Add the new tool to `FIELDS_TO_COMPARE` in `alemutpipe/util/compare.py`:

```python
# Line 10
FIELDS_TO_COMPARE = {
    'breseq': 'output/output.gd',
    'gatk': 'GATK_CNVnator.gd',
    'newtool': 'newtool_normalized.gd'  # ADD THIS
}
```

#### 1.3 Generate Evidence Files

Create evidence files in `<tool>/<sample>/evidence/` directory:
- `<position>.html` - For SNPs, INS, small DEL
- `<position>.png` - For AMP, large DEL (coverage plots)

#### 1.4 Update Main Workflow

In `alemutpipe/main.py` or the appropriate workflow file, add the call to the new tool:

```python
from alemutpipe.util.newtool import run_newtool

# In the processing loop:
newtool_gd = run_newtool(bam_file, reference, output_path)
```

### Step 2: AleDB Modifications

#### 2.1 Update Django Models

Edit `seq/models.py`:

```python
class ResequencingExperiment(models.Model):
    # Existing fields...
    location = models.CharField(max_length=200, blank=True, null=True)
    gatk_location = models.CharField(max_length=200, blank=True, null=True)
    newtool_location = models.CharField(max_length=200, blank=True, null=True)  # ADD


class ObservedMutation(models.Model):
    # Existing fields...
    breseq_present = models.BooleanField(null=True)
    gatk_present = models.BooleanField(null=True)
    newtool_present = models.BooleanField(null=True)  # ADD

    frequency = models.DecimalField(null=True, max_digits=5, decimal_places=4)
    frequency_gatk = models.DecimalField(null=True, max_digits=5, decimal_places=4)
    frequency_newtool = models.DecimalField(null=True, max_digits=5, decimal_places=4)  # ADD

    evidence = models.CharField(max_length=400, blank=True, null=True)
    gatk_evidence = models.CharField(max_length=400, blank=True, null=True)
    newtool_evidence = models.CharField(max_length=400, blank=True, null=True)  # ADD
```

#### 2.2 Run Django Migration

```bash
cd /path/to/aledb
python manage.py makemigrations seq
python manage.py migrate
```

#### Understanding Django Migrations

Django migrations automatically update the database schema when you change models. The database (MySQL/Azure SQL) is managed entirely through Django—you do not need to manually write SQL.

| Command | What It Does |
|---------|--------------|
| `makemigrations` | Compares your `models.py` to previous migrations and generates a new migration file describing the changes (e.g., `seq/migrations/0015_add_newtool_fields.py`) |
| `migrate` | Reads unapplied migration files, converts them to SQL, and executes them against the database |

**Example:** Adding `frequency_newtool` field to `ObservedMutation` will generate SQL like:
```sql
ALTER TABLE seq_observedmutation ADD frequency_newtool DECIMAL(5,4) NULL;
```

#### Important: Backup and Staging Best Practices

**Always follow these steps before running migrations on production:**

1. **Backup the database first**
   ```bash
   # For MySQL
   mysqldump -u username -p aledb > aledb_backup_$(date +%Y%m%d).sql

   # For Azure SQL, use Azure Portal or az cli to create a backup
   ```

2. **Test on staging environment first**
   - Apply migrations to a staging server with a copy of production data
   - Verify the application works correctly with the new schema
   - Check that existing data is preserved and accessible

3. **Schedule maintenance window**
   - Migrations that add nullable columns (like these) are usually fast
   - However, large tables may take longer to alter

4. **Have a rollback plan**
   - Keep the previous migration state documented
   - Django supports `python manage.py migrate <app> <migration_number>` to rollback

#### 2.3 Update Frequency Extraction

Edit `builder/upload.py`:

```python
# Update constants at top of file
DEFAULT_NEWTOOL_FREQ = 0

# Update _get_mutation_freq function (around line 294)
def _get_mutation_freq(mutation_dict):
    frequency = DEFAULT_CLONAL_FREQ
    frequency_gatk = DEFAULT_GATK_FREQ
    frequency_newtool = DEFAULT_NEWTOOL_FREQ  # ADD

    for key in mutation_dict.keys():
        if key.startswith('frequency_'):
            if key.endswith('breseq') or key.endswith('output'):
                if isinstance(mutation_dict[key], (float, int)):
                    frequency = mutation_dict[key]
                else:
                    frequency = 0
            elif key.endswith('GATK_CNVnator'):
                if isinstance(mutation_dict[key], (float, int)):
                    frequency_gatk = mutation_dict[key]
                else:
                    frequency_gatk = 0
            elif key.endswith('newtool'):  # ADD THIS BLOCK
                if isinstance(mutation_dict[key], (float, int)):
                    frequency_newtool = mutation_dict[key]
                else:
                    frequency_newtool = 0

    return [frequency, frequency_gatk, frequency_newtool]  # UPDATE RETURN
```

#### 2.4 Update Mutation Registration

Edit `builder/upload.py` in `_database_mutations()` function (around line 266):

```python
# Determine evidence file for new tool
if mutation_dict[mut_num].get(GD_MUT_TYPE_ATTR_KEY) == "AMP":
    newtool_evidence = str(mutation_dict[mut_num].get(GD_MUT_POS_ATTR_KEY)) + '.png'
elif mutation_dict[mut_num].get(GD_MUT_TYPE_ATTR_KEY) == "DEL" and \
     int(mutation_dict[mut_num].get(GD_CNV_LENGTH_ATTR_KEY, 0)) > 190:
    newtool_evidence = str(mutation_dict[mut_num].get(GD_MUT_POS_ATTR_KEY)) + '.png'
else:
    newtool_evidence = str(mutation_dict[mut_num].get(GD_MUT_POS_ATTR_KEY)) + '.html'

# Update ObservedMutation creation (around line 274)
observed_mutation = ObservedMutation(
    sequencing_experiment=seq_experiment,
    mutation=mut,
    breseq_present=True,
    gatk_present=True,
    newtool_present=True,                    # ADD
    evidence=evidence,
    gatk_evidence=gatk_evidence,
    newtool_evidence=newtool_evidence,       # ADD
    frequency=frequencies[0],
    frequency_gatk=frequencies[1],
    frequency_newtool=frequencies[2]         # ADD
)
```

#### 2.5 Update ResequencingExperiment Creation

Edit `builder/upload.py` in `_get_reseq_experiment_with_stats()` (around line 159):

```python
newtool_folder = '%s/newtool/%s/' % (experiment_path, sample_name)

reseq, created = ResequencingExperiment.objects.get_or_create(
    location=breseq_folder.replace(ale_data_root_dir, ""),
    gatk_location=gatk_folder.replace(ale_data_root_dir, ""),
    newtool_location=newtool_folder.replace(ale_data_root_dir, ""),  # ADD
    experiment_location=experiment_path.replace(ale_data_root_dir, ""),
    sample_name=sample_name,
    tech_rep_id=technical_replicate_id,
    person=person
)
```

#### 2.6 Update Evidence View

Edit `evidence/views.py`:

```python
def evidence(request, *args, **kwargs):
    # Existing code...

    # Add new tool evidence (around line 89)
    newtool_evidence_location = 'evidence/' + observed_mutation.newtool_evidence

    try:
        evidence_html_newtool = open(
            DATA_MOUNT_LOCATION + resequencing_experiment.newtool_location +
            newtool_evidence_location, 'r'
        ).read()
    except:
        evidence_html_newtool = "N/A"

    # Update context (around line 114)
    context.update({
        # Existing fields...
        'evidence_html_newtool': evidence_html_newtool,  # ADD
    })
```

#### 2.7 Update Evidence Template

Edit `evidence/templates/evidence/evidence.html` to display the new evidence:

```html
<!-- Add new tab/section for the new tool -->
<div class="evidence-section">
    <h3>NewTool Evidence</h3>
    <div class="evidence-content">
        {{ evidence_html_newtool|safe }}
    </div>
</div>
```

### Step 3: Update Directory Structure

The expected directory structure after adding the new tool:

```
/data/aledata/<experiment>/
├── breseq/
│   └── <sample_name>/
│       └── output/
│           ├── annotated.gd
│           ├── index.html
│           └── summary.html
├── gatk/
│   └── <sample_name>/
│       └── evidence/
│           ├── <position>.html
│           └── <position>.png
├── newtool/                          # NEW DIRECTORY
│   └── <sample_name>/
│       ├── newtool_normalized.gd
│       └── evidence/
│           ├── <position>.html
│           └── <position>.png
├── metadata/
│   └── <afir>.csv
└── <afir>.gd                         # Contains frequency_newtool attributes
```

### Summary: Files to Modify

| Repository | File | Changes |
|------------|------|---------|
| **AMP** | `alemutpipe/util/newtool.py` | Create new module |
| **AMP** | `alemutpipe/util/compare.py` | Add to `FIELDS_TO_COMPARE` |
| **AMP** | `alemutpipe/main.py` | Call new tool in workflow |
| **AleDB** | `seq/models.py` | Add fields to `ResequencingExperiment` and `ObservedMutation` |
| **AleDB** | `builder/upload.py` | Update `_get_mutation_freq()`, `_database_mutations()`, `_get_reseq_experiment_with_stats()` |
| **AleDB** | `evidence/views.py` | Add evidence display logic |
| **AleDB** | `evidence/templates/evidence/evidence.html` | Add UI for new evidence |

### Critical Requirements

1. **Frequency Attribute Naming**: The GD file must use `frequency_<toolname>` format
2. **Evidence Files**: Must be in `<tool>/<sample>/evidence/` directory
3. **GD Format**: Output must be valid GenomeDiff format
4. **Database Migration**: Must run migrations after model changes

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `pipeline/upload_scripts/webapp-upload.sh` | Shell entry point |
| `ale/management/commands/upload.py` | Django management command |
| `builder/ale_experiment.py` | Experiment creation and orchestration |
| `builder/upload.py` | Mutation and evidence registration |
| `builder/gdparse/gdparse/gdparse.py` | GenomeDiff file parser |
| `metadata/parser.py` | CSV metadata file parsing (project, owner, media, strain info) |
| `metadata/xpmdvalidator/validate.py` | Metadata JSON schema validation |
| `fixation/util.py` | Fixation analysis |
| `converge/util.py` | Convergence analysis |
| `stats/util.py` | Statistics generation |

---

## Troubleshooting

### Common Issues

1. **Metadata validation fails**
   - Check JSON schema compliance in `metadata/xpmdvalidator/Json_schema.json`
   - Verify all required fields are present in CSV files
   - Ensure JSON fields (`environmental conditions`, `media components`) are properly escaped

2. **No metadata CSV files found**
   - Error: "No Metadata: Please ensure there are csv metadata files in the metadata folder"
   - Ensure `metadata/` directory contains `.csv` files for each sample

3. **Project/Owner/Experiment mismatch**
   - All CSV files in one experiment must have identical `project`, `owner`, and `experiment/subproject` values
   - Check for typos or inconsistencies across CSV files

4. **Sample name parsing fails**
   - Ensure sample names follow AFIR format: `<ale>-<flask>-<isolate>-<replicate>`
   - Ensure CSV files have matching `A`, `F`, `I`, `R` values

5. **Missing evidence files**
   - Verify breseq `output/` directory contains `index.html` and `annotated.gd`
   - Check GATK evidence files exist for each mutation position

6. **Duplicate mutations**
   - Mutations are deduplicated by position + gene + reference + type
   - ObservedMutations link unique mutations to specific experiments

7. **User not found**
   - The `owner` field must match a username or name in the Django User model
   - System will prompt for user selection if multiple matches found

### Manual Operations

```python
# Django shell commands for maintenance

# Delete an experiment
from builder.ale_experiment import delete_ale_experiments
delete_ale_experiments([experiment_id])

# Rebuild analysis for an experiment
from builder.ale_experiment import rebuild_converge_mutations, rebuild_fixated_mutations
rebuild_converge_mutations(experiment_id)
rebuild_fixated_mutations(experiment_id)

# Rebuild all statistics
from builder.ale_experiment import rebuild_all_static_data
rebuild_all_static_data()
```
