# gdtools GD2VCF Testing Plan

This document provides a testing plan to evaluate how `gdtools GD2VCF` converts different GenomeDiff mutation types to VCF format.

## Objective

Determine which GD-specific features are preserved or lost when converting to VCF, to inform the hybrid architecture decision in [VCF_INTEGRATION_ARCHITECTURE.md](./VCF_INTEGRATION_ARCHITECTURE.md).

---

## Test Data Source

Test data is based on the [Breseq Tutorial (Clones)](https://github.com/barricklab/breseq/wiki/Tutorial-Clones), which uses:

- **Reference genome:** *E. coli* B strain REL606 (GenBank: NC_012967)
- **Sample:** ZDB83 from Ara-3 population (Lenski LTEE, 34,000 generations)

---

## Prerequisites

```bash
# Verify gdtools is installed (part of breseq suite)
gdtools --version

# Download reference genome from breseq tutorial
wget https://barricklab.org/release/breseq_tutorial/REL606.gbk.gz
gunzip REL606.gbk.gz

# Download curated GD files for Ara-3 population (29 clones)
wget https://barricklab.org/release/breseq_tutorial/curated_gd.tgz
tar -xzf curated_gd.tgz

# Download pre-generated ZDB83 output (includes output.gd)
wget https://barricklab.org/release/breseq_tutorial/ZDB83_output.tgz
tar -xzf ZDB83_output.tgz
```

---

## Test Files Setup

### Option A: Use Tutorial Output Directly

Use the ZDB83 output from the tutorial:

```bash
# The extracted ZDB83_output contains output/output.gd
gdtools GD2VCF -r REL606.gbk -o ZDB83.vcf ZDB83_output/output/output.gd
```

### Option B: Create Synthetic Test File

Create a test file with all mutation types at `tests/test_gd2vcf/all_types.gd`:

```
#=GENOME_DIFF 1.0
#=TIME 34000
#=POPULATION Ara-3
#=TREATMENT LTEE
#=CLONE ZDB83

# Basic mutations (should convert well)
SNP	1	.	REL606	1733865	A	frequency=1.00	gene_name=pykF
SUB	2	.	REL606	2103889	2	TG	frequency=1.00
DEL	3	.	REL606	1286857	1199	frequency=1.00
INS	4	.	REL606	3894997	G	frequency=1.00

# Complex mutations (may lose information)
MOB	5	.	REL606	3223025	IS150	-1	3	frequency=1.00	ins_start=1	ins_end=1443
AMP	6	.	REL606	625889	2933	4	frequency=1.00
CON	7	.	REL606	4100000	100	REL606:4200000-4200100	frequency=0.70
INV	8	.	REL606	1000000	5000	frequency=0.60

# Evidence records (should NOT appear in VCF)
RA	54	.	REL606	1733865	0	G	A	frequency=1.00	bias_e_value=4.5e-10
MC	55	.	REL606	1286857	1288056	1199	0	left_inside_cov=0	right_inside_cov=0
JC	56	.	REL606	3223025	1	REL606	3223026	-1	0	alignment_overlap=5
UN	57	.	REL606	900000	950000
```

**Note:** The AMP entry `AMP . . REL606 625889 2933 4` represents the famous *citT* amplification (Cit+ phenotype) from the LTEE experiment.

---

## Test Cases

### Test 1: Basic Conversion

**Command:**
```bash
gdtools GD2VCF -r reference.gb -o output.vcf all_types.gd
```

**Expected:** VCF file created without errors.

**Verification:**
```bash
# Check VCF is valid
bcftools view output.vcf | head -30

# Count variant records
grep -v "^#" output.vcf | wc -l
# Expected: 8 (one per mutation, no evidence records)
```

---

### Test 2: SNP Conversion

**Input GD:**
```
SNP	1	.	REL606	1733865	A	frequency=1.00	gene_name=pykF
```

**Expected VCF:**
```vcf
REL606	1733865	.	G	A	.	.	frequency=1.00	.	.
```

**Verification Checklist:**
- [ ] Position correct (1733865)
- [ ] REF base correct (G from reference genome)
- [ ] ALT base correct (A)
- [ ] frequency attribute preserved in INFO field
- [ ] gene_name (pykF) preserved?

---

### Test 3: SUB (Multi-nucleotide Substitution)

**Input GD:**
```
SUB	2	.	REL606	2103889	2	TG	frequency=1.00
```

**Expected VCF:** MNP (Multi-Nucleotide Polymorphism) representation
```vcf
REL606	2103889	.	XX	TG	.	.	frequency=1.00	.	.
```
(where XX is 2 bases from reference)

**Verification Checklist:**
- [ ] Position correct (2103889)
- [ ] REF length matches size field (2)
- [ ] ALT sequence correct (TG)
- [ ] Represented as single MNP or split into multiple SNPs?

---

### Test 4: DEL (Deletion)

**Input GD:**
```
DEL	3	.	REL606	1286857	1199	frequency=1.00
```

**Expected VCF:** Standard deletion format
```vcf
REL606	1286856	.	XYYY...	X	.	.	frequency=1.00	.	.
```
(VCF deletion includes preceding base; 1199 bp deletion)

**Verification Checklist:**
- [ ] Position adjusted for VCF convention (1286856, pos-1)
- [ ] REF includes anchor base + deleted sequence (1200 bp total)
- [ ] ALT is just anchor base
- [ ] Size preserved (can calculate from REF length - 1)

---

### Test 5: INS (Insertion)

**Input GD:**
```
INS	4	.	REL606	3894997	G	frequency=1.00
```

**Expected VCF:**
```vcf
REL606	3894997	.	X	XG	.	.	frequency=1.00	.	.
```
(VCF insertion includes anchor base)

**Verification Checklist:**
- [ ] Position correct (3894997)
- [ ] REF is anchor base only
- [ ] ALT includes anchor + inserted sequence (G)
- [ ] Insertion sequence preserved

---

### Test 6: MOB (Mobile Element Insertion)

**Input GD:**
```
MOB	5	.	REL606	3223025	IS150	-1	3	frequency=1.00	ins_start=1	ins_end=1443
```

**Expected:** This is complex - may require custom INFO fields or be converted to generic insertion.

**Verification Checklist:**
- [ ] Record present in VCF?
- [ ] Mobile element name (IS150) preserved?
- [ ] Strand (-1) preserved?
- [ ] Target site duplication (3 bp) preserved?
- [ ] `ins_start`, `ins_end` preserved?
- [ ] If converted to SV, what `SVTYPE` is used?

**Likely Loss:**
- Mobile element identity (IS150)
- Strand information
- Target site duplication details

---

### Test 7: AMP (Amplification/CNV)

**Input GD:** (The famous *citT* amplification enabling citrate utilization)
```
AMP	6	.	REL606	625889	2933	4	frequency=1.00
```

**Expected:** May be represented as DUP or CNV in VCF SV notation.

**Verification Checklist:**
- [ ] Record present in VCF?
- [ ] Position preserved (625889)?
- [ ] Size preserved (2933 bp)?
- [ ] Copy number (4) preserved?
- [ ] Uses `SVTYPE=DUP` or `SVTYPE=CNV`?
- [ ] Has `END=628822` INFO field (625889 + 2933)?

**Likely Loss:**
- Copy number semantics (VCF DUP typically means 1 extra copy, not 4 total)
- Representation may not be standard

---

### Test 8: CON (Gene Conversion)

**Input GD:**
```
CON	7	.	REL606	4100000	100	REL606:4200000-4200100	frequency=0.70
```

**Expected:** No standard VCF representation exists. Common in *rrl* and *rhs* genes.

**Verification Checklist:**
- [ ] Record present in VCF?
- [ ] How is source region (4200000-4200100) represented?
- [ ] Is this converted to a different type (SUB perhaps)?

**Likely Loss:**
- Source region information (critical for gene conversion)
- Gene conversion semantics

---

### Test 9: INV (Inversion)

**Input GD:**
```
INV	8	.	REL606	1000000	5000	frequency=0.60
```

**Expected VCF:** Should use SV notation with `SVTYPE=INV`.

```vcf
REL606	1000000	.	N	<INV>	.	.	SVTYPE=INV;END=1005000	.	.
```

**Verification Checklist:**
- [ ] Record present in VCF?
- [ ] Uses `SVTYPE=INV`?
- [ ] `END` position correct (1000000 + 5000 = 1005000)?
- [ ] Breakpoints represented correctly?

---

### Test 10: Evidence Records

**Input GD:**
```
RA	54	.	REL606	1733865	0	G	A	frequency=1.00	bias_e_value=4.5e-10
MC	55	.	REL606	1286857	1288056	1199	0	left_inside_cov=0
JC	56	.	REL606	3223025	1	REL606	3223026	-1	0
UN	57	.	REL606	900000	950000
```

**Expected:** Evidence records should NOT appear in VCF output. These link to HTML evidence visualizations in breseq output.

**Verification:**
```bash
# Count lines - should match mutation count only
grep -v "^#" output.vcf | wc -l
# Expected: 8 (mutations only, no RA/MC/JC/UN records)
```

---

### Test 11: Attribute Preservation

Check which GD attributes are preserved in VCF INFO field.

**Common GD attributes:**
| Attribute | Expected in VCF? |
|-----------|------------------|
| `frequency` | Yes (as AF or custom) |
| `gene_name` | Maybe (as ANN or custom) |
| `gene_position` | Maybe |
| `codon_ref_seq` | Unlikely |
| `codon_new_seq` | Unlikely |
| `aa_ref_seq` | Maybe (as AA_REF) |
| `aa_new_seq` | Maybe (as AA_ALT) |
| `snp_type` | Unlikely |

**Verification:**
```bash
# Extract INFO field content
grep -v "^#" output.vcf | cut -f8 | sort | uniq
```

---

## Test Execution Script

Create `tests/test_gd2vcf/run_tests.sh`:

```bash
#!/bin/bash
set -e

# Use REL606 reference from breseq tutorial
REFERENCE="REL606.gbk"
TEST_DIR="$(dirname "$0")"
OUTPUT_DIR="${TEST_DIR}/output"

# Download reference if not present
if [ ! -f "$REFERENCE" ]; then
    echo "Downloading REL606.gbk from breseq tutorial..."
    wget -q https://barricklab.org/release/breseq_tutorial/REL606.gbk.gz
    gunzip REL606.gbk.gz
fi

mkdir -p "$OUTPUT_DIR"

echo "=== GD2VCF Conversion Test ==="
echo "Reference: $REFERENCE (E. coli B strain REL606)"
echo ""

# Run conversion
echo "Converting all_types.gd to VCF..."
gdtools GD2VCF -r "$REFERENCE" -o "$OUTPUT_DIR/all_types.vcf" "$TEST_DIR/all_types.gd"

echo ""
echo "=== VCF Header ==="
grep "^##" "$OUTPUT_DIR/all_types.vcf"

echo ""
echo "=== VCF Records ==="
grep -v "^##" "$OUTPUT_DIR/all_types.vcf" | column -t

echo ""
echo "=== Summary ==="
echo "Input GD mutations: $(grep -E '^(SNP|SUB|DEL|INS|MOB|AMP|CON|INV)\s' "$TEST_DIR/all_types.gd" | wc -l)"
echo "Output VCF records: $(grep -v '^#' "$OUTPUT_DIR/all_types.vcf" | wc -l)"

echo ""
echo "=== Mutation Type Mapping ==="
echo "Checking which types appear in VCF..."

for type in SNP SUB DEL INS MOB AMP CON INV; do
    gd_count=$(grep -E "^${type}\s" "$TEST_DIR/all_types.gd" | wc -l)
    echo "$type in GD: $gd_count"
done

echo ""
echo "=== Evidence Records (should be 0 in VCF) ==="
for type in RA MC JC UN; do
    gd_count=$(grep -E "^${type}\s" "$TEST_DIR/all_types.gd" | wc -l)
    echo "$type in GD: $gd_count (should not appear in VCF)"
done
```

---

## Results Template

After running tests, document findings:

### Conversion Results Summary

| GD Type | Converts to VCF? | VCF Representation | Information Lost |
|---------|------------------|-------------------|------------------|
| SNP | | | |
| SUB | | | |
| DEL | | | |
| INS | | | |
| MOB | | | |
| AMP | | | |
| CON | | | |
| INV | | | |

### Attribute Preservation

| GD Attribute | Preserved in VCF? | VCF Field |
|--------------|-------------------|-----------|
| frequency | | |
| gene_name | | |
| aa_ref_seq | | |
| aa_new_seq | | |
| copy_number | | |

---

## Round-Trip Test

Test if GD → VCF → GD preserves information:

```bash
# Use ZDB83 output from tutorial as test data
REFERENCE="REL606.gbk"
ORIGINAL="ZDB83_output/output/output.gd"

# Convert GD to VCF
gdtools GD2VCF -r $REFERENCE -o step1.vcf $ORIGINAL

# Convert VCF back to GD
gdtools VCF2GD -o step2.gd step1.vcf

# Compare line counts
echo "Original GD mutations: $(grep -E '^(SNP|SUB|DEL|INS|MOB|AMP|CON|INV)\s' $ORIGINAL | wc -l)"
echo "Round-trip GD mutations: $(grep -E '^(SNP|SUB|DEL|INS|MOB|AMP|CON|INV)\s' step2.gd | wc -l)"

# Or use gdtools COMPARE for detailed comparison
gdtools COMPARE -r $REFERENCE $ORIGINAL step2.gd
```

**Expected losses in round-trip:**
- Evidence records (RA, MC, JC, UN) - always lost
- MOB element details (IS element identity, strand, TSD)
- CON source region
- Some attributes (gene_name, aa_ref_seq, etc.)

---

## Conclusion Template

After testing, fill in:

1. **Safe to convert (full fidelity):**
   - [ ] SNP
   - [ ] SUB
   - [ ] DEL
   - [ ] INS

2. **Partial conversion (some loss):**
   - [ ] MOB - loses: ___
   - [ ] AMP - loses: ___
   - [ ] INV - loses: ___

3. **Not supported:**
   - [ ] CON
   - [ ] Evidence records

4. **Recommendation:**
   Based on testing results, the hybrid approach in [VCF_INTEGRATION_ARCHITECTURE.md](./VCF_INTEGRATION_ARCHITECTURE.md) is/is not validated because:
   - _____

---

## Related Documentation

- [VCF_INTEGRATION_ARCHITECTURE.md](./VCF_INTEGRATION_ARCHITECTURE.md) - Architecture recommendations
- [UPLOAD_WORKFLOW.md](./UPLOAD_WORKFLOW.md) - Upload workflow details
- [Breseq Tutorial (Clones)](https://github.com/barricklab/breseq/wiki/Tutorial-Clones) - Source of test data
- [Breseq documentation](https://barricklab.org/twiki/bin/view/Lab/ToolsBacterialGenomeResequencing) - gdtools reference
- [Breseq GitHub issue #80](https://github.com/barricklab/breseq/issues/80) - Discussion on GD vs VCF format
