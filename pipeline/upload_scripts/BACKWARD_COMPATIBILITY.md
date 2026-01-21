# Backward Compatibility Guide: Adding New Mutation Sources

This document describes how to add a new mutation calling tool (e.g., DeepVariant, Freebayes) while maintaining backward compatibility with existing experiments that only have Breseq and GATK/CNVnator data.

## Problem Statement

- **Old experiments**: Have 2 frequency sources (Breseq, GATK/CNVnator)
- **New experiments**: Will have 3 frequency sources (Breseq, GATK/CNVnator, NewTool)

The system must:
1. Display old experiments correctly (without errors from missing data)
2. Display new experiments with all 3 sources
3. Allow filtering and searching to work for both

---

## 1. Database Model Changes

**File:** `seq/models.py`

Use `null=True` and `default=None` for all new fields:

```python
class ResequencingExperiment(models.Model):
    # Existing fields (unchanged)
    location = models.CharField(max_length=200, blank=True, null=True)
    gatk_location = models.CharField(max_length=200, blank=True, null=True)

    # NEW: Must allow null for old records
    newtool_location = models.CharField(
        max_length=200,
        blank=True,
        null=True  # <-- Critical: old records will have NULL
    )


class ObservedMutation(models.Model):
    # Existing fields (unchanged)
    breseq_present = models.BooleanField(null=True)
    gatk_present = models.BooleanField(null=True)
    frequency = models.DecimalField(null=True, max_digits=5, decimal_places=4)
    frequency_gatk = models.DecimalField(null=True, max_digits=5, decimal_places=4)
    evidence = models.CharField(max_length=400, blank=True, null=True)
    gatk_evidence = models.CharField(max_length=400, blank=True, null=True)

    # NEW fields - all must allow null
    newtool_present = models.BooleanField(
        null=True,
        default=None  # <-- Old records will have NULL, not False
    )

    frequency_newtool = models.DecimalField(
        null=True,
        default=None,  # <-- Old records will have NULL, not 0
        max_digits=5,
        decimal_places=4
    )

    newtool_evidence = models.CharField(
        max_length=400,
        blank=True,
        null=True  # <-- Old records will have NULL
    )
```

### Migration

After updating the model:

```bash
python manage.py makemigrations seq
python manage.py migrate
```

The migration will add new columns with NULL values for all existing records.

---

## 2. Template Changes (Conditional Display)

**File:** `templates/evidence/evidence.html`

Only display the new tool section if data exists:

```html
<h4>Breseq alignment</h4>
{{ evidence_html_breseq|safe }}

<h4>GATK/CNVnator alignment</h4>
{{ evidence_html_gatkcnvnator|safe }}

{# NEW: Only show if newtool evidence exists #}
{% if evidence_html_newtool and evidence_html_newtool != "N/A" %}
    <h4>NewTool alignment</h4>
    {{ evidence_html_newtool|safe }}
{% endif %}
```

### For mutation tables, show `-` for missing data:

```html
<td>
    {% if observed_mutation.frequency_newtool is not None %}
        {{ observed_mutation.frequency_newtool }}
    {% else %}
        -
    {% endif %}
</td>
```

---

## 3. View Changes (Handle None Gracefully)

**File:** `evidence/views.py`

```python
def evidence(request, *args, **kwargs):
    # ... existing code ...

    # Handle newtool evidence - may not exist for old experiments
    evidence_html_newtool = None

    newtool_evidence = getattr(observed_mutation, 'newtool_evidence', None)
    newtool_location = getattr(resequencing_experiment, 'newtool_location', None)

    if newtool_evidence and newtool_location:
        try:
            newtool_evidence_path = os.path.join(
                DATA_MOUNT_LOCATION,
                newtool_location,
                'evidence',
                newtool_evidence
            )
            with open(newtool_evidence_path, 'r') as f:
                evidence_html_newtool = f.read()
        except (FileNotFoundError, TypeError, AttributeError):
            evidence_html_newtool = "N/A"

    context.update({
        # ... existing context ...
        'evidence_html_newtool': evidence_html_newtool,
    })
```

---

## 4. Filter Changes (Optional Filtering)

**File:** `filter/util.py`

Only apply newtool filter when the field has data:

```python
def build_filter_query(exp_filter):
    q_exp = Q()

    # Existing breseq filter
    if exp_filter.min_cutoff:
        q_exp.add(Q(frequency__lt=exp_filter.min_cutoff / 100), Q.AND)

    # Existing GATK filter
    if exp_filter.gatk_min_cutoff:
        q_exp.add(Q(frequency_gatk__lt=exp_filter.gatk_min_cutoff / 100), Q.AND)

    # NEW: Only filter if newtool frequency exists (not NULL)
    if hasattr(exp_filter, 'newtool_min_cutoff') and exp_filter.newtool_min_cutoff:
        q_exp.add(
            Q(frequency_newtool__isnull=False) &  # <-- Skip NULL records
            Q(frequency_newtool__lt=exp_filter.newtool_min_cutoff / 100),
            Q.AND
        )

    return q_exp
```

---

## 5. Upload Code Changes

**File:** `builder/upload.py`

### 5.1 Frequency Extraction

```python
def _get_mutation_freq(mutation_dict):
    frequency = DEFAULT_CLONAL_FREQ
    frequency_gatk = DEFAULT_GATK_FREQ
    frequency_newtool = None  # <-- Use None, not 0, for missing data

    for key in mutation_dict.keys():
        if key.startswith('frequency_'):
            if key.endswith('breseq') or key.endswith('output'):
                if isinstance(mutation_dict[key], (float, int)):
                    frequency = mutation_dict[key]
            elif key.endswith('GATK_CNVnator'):
                if isinstance(mutation_dict[key], (float, int)):
                    frequency_gatk = mutation_dict[key]
            elif key.endswith('newtool'):  # NEW
                if isinstance(mutation_dict[key], (float, int)):
                    frequency_newtool = mutation_dict[key]

    return [frequency, frequency_gatk, frequency_newtool]
```

### 5.2 ObservedMutation Creation

```python
frequencies = _get_mutation_freq(mutation_dict[mut_num])

# Only set newtool fields if data exists
newtool_present = frequencies[2] is not None
newtool_evidence = None
if newtool_present:
    if mutation_type == "AMP" or (mutation_type == "DEL" and feature_length > 190):
        newtool_evidence = f"{position}.png"
    else:
        newtool_evidence = f"{position}.html"

observed_mutation = ObservedMutation(
    sequencing_experiment=seq_experiment,
    mutation=mut,
    breseq_present=True,
    gatk_present=True,
    newtool_present=newtool_present if newtool_present else None,  # None, not False
    evidence=evidence,
    gatk_evidence=gatk_evidence,
    newtool_evidence=newtool_evidence,  # Will be None for old experiments
    frequency=frequencies[0],
    frequency_gatk=frequencies[1],
    frequency_newtool=frequencies[2],  # Will be None for old experiments
)
```

---

## 6. API/Interop Changes

**File:** `interop_query/views.py`

Handle mixed data in frequency display:

```python
def format_frequency_display(observed_mutation):
    """Format frequency for display, handling NULL values."""

    def fmt(val):
        if val is None:
            return '-'
        return f"{float(val):.3f}"

    freq_breseq = fmt(observed_mutation.frequency)
    freq_gatk = fmt(observed_mutation.frequency_gatk)
    freq_newtool = fmt(getattr(observed_mutation, 'frequency_newtool', None))

    # Old experiments: "0.950/0.920/-"
    # New experiments: "0.950/0.920/0.880"
    return f"{freq_breseq}/{freq_gatk}/{freq_newtool}"
```

For JSON API responses:

```python
def serialize_mutation(observed_mutation):
    return {
        'position': observed_mutation.mutation.position,
        'frequency_breseq': observed_mutation.frequency,
        'frequency_gatk': observed_mutation.frequency_gatk,
        'frequency_newtool': observed_mutation.frequency_newtool,  # Returns null in JSON
        # ...
    }
```

---

## 7. Dashboard Display

If the dashboard shows frequency columns, update the column headers dynamically:

```python
def get_frequency_columns(experiment):
    """Determine which frequency columns to show based on experiment data."""
    columns = ['Breseq Freq', 'GATK Freq']

    # Check if any mutations in this experiment have newtool data
    has_newtool = ObservedMutation.objects.filter(
        sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment=experiment,
        frequency_newtool__isnull=False
    ).exists()

    if has_newtool:
        columns.append('NewTool Freq')

    return columns
```

---

## Summary: Key Principles

| Concern | Solution |
|---------|----------|
| Old records missing new fields | `null=True, default=None` in model |
| Template display | `{% if field %}` conditional blocks |
| View data access | Try/except or `if field:` checks |
| Filtering | Skip filter if field is NULL |
| Frequency display | Show `-` or empty for NULL values |
| API responses | Return `null` not `0` for missing data |
| Boolean flags | Use `None` not `False` for "unknown/not applicable" |

---

## Testing Backward Compatibility

### Test Case 1: Old Experiment Display

```python
def test_old_experiment_displays_without_newtool(self):
    """Old experiments should display correctly without newtool data."""
    # Create mutation without newtool fields
    obs_mut = ObservedMutation.objects.create(
        frequency=0.95,
        frequency_gatk=0.92,
        frequency_newtool=None,  # Simulates old record
        newtool_present=None,
    )

    # Verify display doesn't error
    response = self.client.get(f'/mutations/details?observed_mut_id={obs_mut.id}')
    self.assertEqual(response.status_code, 200)
    self.assertNotContains(response, 'NewTool alignment')
```

### Test Case 2: New Experiment Display

```python
def test_new_experiment_displays_all_sources(self):
    """New experiments should display all 3 frequency sources."""
    obs_mut = ObservedMutation.objects.create(
        frequency=0.95,
        frequency_gatk=0.92,
        frequency_newtool=0.88,
        newtool_present=True,
    )

    response = self.client.get(f'/mutations/details?observed_mut_id={obs_mut.id}')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'NewTool alignment')
```

### Test Case 3: Mixed Query

```python
def test_query_returns_both_old_and_new(self):
    """Queries should return both old and new experiments."""
    # Create old and new mutations
    old_mut = ObservedMutation.objects.create(frequency=0.95, frequency_newtool=None)
    new_mut = ObservedMutation.objects.create(frequency=0.95, frequency_newtool=0.88)

    # Query all mutations
    results = ObservedMutation.objects.filter(frequency__gte=0.9)

    self.assertEqual(results.count(), 2)
```

---

## Related Documentation

- [UPLOAD_WORKFLOW.md](./UPLOAD_WORKFLOW.md) - Complete upload workflow documentation
- [AMP Pipeline Docs](../../../amp/docs/) - Pipeline documentation for adding new tools
