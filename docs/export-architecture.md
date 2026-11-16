# Export Architecture

The Export dropdown is on the Experiment List (`/ale/experiments/`) and Project pages (`/ale/project/<id>`).

## Routing

Top-level in `aleinfo/urls.py`: `/export` → `export/urls.py`, `/md_export` → `md_export/urls.py`

## Backend

| Export Option | URL | View | File |
|---|---|---|---|
| Mutations | `/export` | `export.views.export` | `export/views.py` |
| Converged Mutations | `/export` | `export.views.export` | `export/views.py` |
| Fixed Mutations | `/export` | `export.views.export` | `export/views.py` |
| Metadata | `/md_export` | `md_export.views.md_export` | `md_export/views.py` |
| Experiment List | `/export/experiment_index` | `export.views.export_experiment_index` | `export/views.py` |

The three mutation exports share one view, differentiated by `mut_type` GET parameter (`mut`, `converged_mut`, `fixed_mut`).

## Frontend

- Buttons & JS: `templates/ale/experiment_datatables.js`
- Included by: `templates/ale/experiments.html` and `templates/ale/project_detail.html`
- All exports require selecting experiments first
- `project_id` JS variable: `null` on experiments page, numeric on project detail page

## Output Formats

- Mutations, Converged/Fixed Mutations, Metadata → ZIP of per-experiment CSVs
- Experiment List → single CSV

## Per-experiment file names (since 2026-11-04)

All per-experiment CSVs (mutations, fixed, converged, metadata) are named by
`export_filename()` in `export/views.py`:

```
PUBLIC_ProjID24_ExpID2698_mut_Proj_<project name>_Exp_<experiment name>.csv
PRIVATE_ProjID405_ExpID2700_converged_mut_Proj_<project name>_Exp_<experiment name>.csv
md_PUBLIC_ProjID24_ExpID2698_Proj_<project name>_Exp_<experiment name>.csv
```

- `PUBLIC`/`PRIVATE` is the owning project's `is_public` at download time.
  Visibility is a project property; experiments and mutations inherit it.
- Names are sanitised to `[A-Za-z0-9_-]` and may themselves contain `_`, so
  **do not split on underscores**. Parse the fixed prefix with:

```
^(?:md_)?(PUBLIC|PRIVATE)_ProjID(\d+)_ExpID(\d+)(?:_(mut|fixed_mut|converged_mut))?_Proj_.*\.csv$
```

- Join to `experiment_index.csv` (Experiment List export) on `ale_id` = ExpID.
- Before 2026-11-04 the pattern was `Proj_<name>_Exp_<name>_ExpID<id>_<type>.csv`
  and `md_Proj_<name>_Exp_<name>_ExpID<id>.csv`, with no visibility or project ID.
