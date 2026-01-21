# VCF Integration Architecture

This document describes the recommended architecture for integrating VCF-based variant callers while maintaining compatibility with breseq's GenomeDiff (GD) format.

## Current Architecture: GD-Centric

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Current: GD as Primary Format                        │
│                                                                              │
│  Breseq ──────────────────────────────────────────┐                         │
│    └─ output.gd (native GD format)                │                         │
│                                                   │                         │
│  GATK ──> .vcf ──> gdtools VCF2GD ──> .gd ───────┼──> gdtools COMPARE      │
│                                                   │         │               │
│  CNVnator ──> .tsv ──> Python ──> .gd ───────────┘         │               │
│                                                             ▼               │
│                                                      <afir>.gd              │
│                                                             │               │
│                                                             ▼               │
│                                                    AleDB (GDParser)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Proposed Architecture: Hybrid (Recommended)

Keep GD as internal format, add VCF as interchange format for new tools:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Proposed: Hybrid GD + VCF Integration                     │
│                                                                              │
│  ┌── Breseq-native pathway ──────────────────────────────────────────────┐  │
│  │  Breseq ──> output.gd ──────────────────────────────────────────────┐ │  │
│  │               │                                                      │ │  │
│  │               └──> gdtools GD2VCF ──> .vcf ──> (VCF Export)         │ │  │
│  └──────────────────────────────────────────────────────────────────────┘ │  │
│                                                                            │  │
│  ┌── VCF-native pathway (new tools) ────────────────────────────────────┐ │  │
│  │  GATK ────────────────────> .vcf ──┐                                 │ │  │
│  │  DeepVariant ─────────────> .vcf ──┼──> gdtools VCF2GD ──> .gd ─────┼─┤  │
│  │  Freebayes ───────────────> .vcf ──┤                                 │ │  │
│  │  NewTool ─────────────────> .vcf ──┘                                 │ │  │
│  └──────────────────────────────────────────────────────────────────────┘ │  │
│                                                                            │  │
│  ┌── CNV pathway ───────────────────────────────────────────────────────┐ │  │
│  │  CNVnator ──> .tsv ──> Python ──> .gd ──────────────────────────────┼─┤  │
│  └──────────────────────────────────────────────────────────────────────┘ │  │
│                                                                            │  │
│                                    ┌───────────────────────────────────────┘  │
│                                    ▼                                          │
│                           gdtools COMPARE                                     │
│                                    │                                          │
│                     ┌──────────────┼──────────────┐                          │
│                     ▼              ▼              ▼                          │
│               <afir>.gd      <afir>.html    <afir>.vcf                       │
│                     │                            │                           │
│                     ▼                            ▼                           │
│              AleDB (GDParser)              External Tools                    │
│                                          (bcftools, IGV, etc.)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Why Keep GD as Primary Format?

### 1. Breseq-Specific Features

GD format supports mutation types not well-represented in VCF:

the `gdtools GD2VCF` output a VCF with limited stats, e.g. all AF=1 (SEM10_P._putida_in_p  60830  .    GATGTAA G    .    PASS  AF=1.0000;AD=69;DP=70).

Mutation type documented on https://gensoft.pasteur.fr/docs/breseq/0.39.0/output.html

| Type | Description | GD Support | VCF Support |
|------|-------------|------------|-------------|
| SNP | Single nucleotide polymorphism | ✅ Native | ✅ |
| SUB | Multiple base substitution | ✅ Native | ✅ no SUB in clonal sample data for validation |
| DEL | Deletion | ✅ Native | ✅ |
| INS | Insertion | ✅ Native | ✅ |
| **MOB** | Mobile element insertion | ✅ Native | ✅ |
| **AMP** | Amplification (CNV) | ✅ Native | ⚠️ test featue of breseq, not validate |


**VCF captures:** Full inserted sequence, position, frequency, depth

**VCF loses:** IS element name, strand orientation, target site duplication size

#### Frequency Rounding

The `frequency` field in both VCF (AF) and GD mutation entries is **rounded/thresholded**, not the raw observed frequency. The actual frequency is stored in `polymorphism_frequency` within the RA (read alignment) entries in the GD file.

| Position | `frequency` (VCF/GD) | `polymorphism_frequency` (GD RA) |
|----------|----------------------|----------------------------------|
| 380188 | 1 | 0.9667 |
| 430835 | 1 | 0.9545 |
| 475292 | 1 | 0.9310 |
| 1004251 | 1 | 0.9524 |
| 3762741 | 1 | 0.9688 |
| 4616396 | 1 | 0.9608 |

Variants with `polymorphism_frequency` above ~90% are rounded to `frequency=1` for the consensus call.



**Use VCF if you need:**
- Standard variant format for downstream tools
- Basic variant calls (position, ref, alt, frequency)

**Use GD if you need:**
- Mobile element annotations (IS name, strand, duplication)
- Structural variant evidence (junction reads)
- Quality metrics (strand bias, polymorphism scores)
- Coverage gap information
- **Precise allele frequencies** (from `polymorphism_frequency` in RA entries)

### 2. Evidence Record System

GD files contain evidence records that link to HTML visualizations:

```
# Mutation record
SNP  1  54  NC_000913  67699  T  frequency=0.95

# Evidence records (link to HTML files)
RA   54  .  NC_000913  67699  0  A  T  bias_e_value=4611780  fisher_strand_p_value=1...
MC   106 .  NC_000913  257908 258683  768  0  left_inside_cov=0...
JC   111 .  NC_000913  1  1  NC_000913  4641652  -1  0  alignment_overlap=0...
```

These evidence records:
- Link mutations to supporting read alignments
- Enable HTML evidence visualization in breseq output
- Are preserved in AleDB for mutation review

**VCF has no equivalent concept.**

### 3. HTML Evidence Visualization

Breseq generates HTML evidence files:
- `RA_*.html` - Read alignment plots
- `MC_*.html` - Missing coverage plots
- `JC_*.html` - Junction evidence plots

These are critical for manual mutation review in AleDB.

## Integration Strategy for New Tools

### Step 1: Tool Outputs VCF

New variant caller outputs standard VCF:

```vcf
##fileformat=VCFv4.2
##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">
##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
#CHROM  POS     ID  REF ALT QUAL    FILTER  INFO            FORMAT  SAMPLE
NC_000913   12345   .   A   T   500 PASS    AF=0.95;DP=100  GT:AD   0/1:5,95
```

### Step 2: Add Frequency Attribute

Before conversion, add tool-specific frequency to VCF INFO:

```python
# In newtool.py
def add_frequency_to_vcf(vcf_path, tool_name):
    """Add frequency_{toolname} to VCF INFO field."""
    # frequency_newtool=0.95
```

### Step 3: Convert to GD

Use gdtools VCF2GD:

```bash
gdtools VCF2GD -o newtool.gd newtool.vcf
```

### Step 4: Merge with Other Sources

Add to FIELDS_TO_COMPARE in `compare.py`:

```python
FIELDS_TO_COMPARE = {
    'breseq': 'output/output.gd',
    'gatk': 'GATK_CNVnator.gd',
    'newtool': 'newtool.gd'  # New tool
}
```

### Step 5: Generate Evidence Files

Create evidence HTML/PNG files in `newtool/<sample>/evidence/`:

```
newtool/
└── <sample>/
    └── evidence/
        ├── 12345.html   # SNP evidence
        ├── 50000.png    # AMP coverage plot
        └── ...
```

## VCF Export (Optional)

For users who need VCF output:

```bash
# Export merged results to VCF
gdtools GD2VCF -r reference.gb -o output.vcf merged.gd
```

**Note:** Some GD-specific information may be lost in VCF export (see testing section).

## Benefits of Hybrid Approach

| Benefit | Description |
|---------|-------------|
| **Low risk** | Minimal changes to existing code |
| **Incremental** | Add new tools without rearchitecting |
| **Evidence preserved** | Breseq HTML evidence still works |
| **VCF compatible** | New tools just need VCF output |
| **Export available** | VCF export for external tools |
| **Backward compatible** | Old experiments unaffected |

## Comparison: Full VCF Migration vs Hybrid

| Aspect | Full VCF Migration | Hybrid (Recommended) |
|--------|-------------------|---------------------|
| Effort | 🔴 High (2-3 months) | 🟢 Low (days per tool) |
| Risk | 🔴 High | 🟢 Low |
| Evidence system | 🔴 Needs rebuild | 🟢 Preserved |
| MOB/CON support | 🔴 Custom work | 🟢 Native |
| New tool integration | 🟢 Easy | 🟢 Easy |
| Interoperability | 🟢 Best | 🟡 Good (via export) |

## Files to Modify for New Tool

| Repository | File | Changes |
|------------|------|---------|
| **AMP** | `alemutpipe/util/newtool.py` | Create: run tool, convert VCF→GD |
| **AMP** | `alemutpipe/util/compare.py` | Add to `FIELDS_TO_COMPARE` |
| **AleDB** | `seq/models.py` | Add frequency/evidence fields |
| **AleDB** | `builder/upload.py` | Extract new frequency |
| **AleDB** | `evidence/views.py` | Display new evidence |

## Related Documentation

- [UPLOAD_WORKFLOW.md](./UPLOAD_WORKFLOW.md) - Upload process details
- [BACKWARD_COMPATIBILITY.md](./BACKWARD_COMPATIBILITY.md) - Handling old experiments
- [GD2VCF_TESTING.md](./GD2VCF_TESTING.md) - gdtools conversion testing

---

## Appendix: GD Format Reference

### Mutation Types

| Type | Format | Example |
|------|--------|---------|
| SNP | `SNP id parent seq pos new [attrs]` | `SNP 1 54 NC_000913 67699 T frequency=0.95` |
| SUB | `SUB id parent seq pos size new [attrs]` | `SUB 2 . NC_000913 100 3 ATG` |
| DEL | `DEL id parent seq pos size [attrs]` | `DEL 3 55 NC_000913 200 500` |
| INS | `INS id parent seq pos new [attrs]` | `INS 4 . NC_000913 300 ACGT` |
| MOB | `MOB id parent seq pos element strand dup [attrs]` | `MOB 5 . NC_000913 400 IS150 1 4` |
| AMP | `AMP id parent seq pos size copy [attrs]` | `AMP 6 . NC_000913 500 1000 2` |
| CON | `CON id parent seq pos size region [attrs]` | `CON 7 . NC_000913 600 100 NC_000913:1000-1100` |
| INV | `INV id parent seq pos size [attrs]` | `INV 8 . NC_000913 700 5000` |

### Evidence Types

| Type | Description | Links to |
|------|-------------|----------|
| RA | Read alignment | SNP/INS/DEL evidence |
| MC | Missing coverage | DEL evidence |
| JC | New junction | MOB/DEL/INV evidence |
| UN | Unknown base | Low coverage regions |

### Attribute Format

Key-value pairs after required fields:
```
SNP 1 54 NC_000913 67699 T frequency=0.95 gene_name=thrL
```
