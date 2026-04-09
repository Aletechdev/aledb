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
