# Homepage Data Dashboard

Replace the static stats table and text blurb with interactive visualizations.
Builds on top of the ideas in [home-page-modernization.md](home-page-modernization.md).

- View: [home/views.py](../home/views.py) (lines 26-54)
- Template: [templates/home/index.html](../templates/home/index.html) (stats block: lines 195-256)

## Prior analysis

Additional growth analytics and visualizations were explored in the
[aledb_growth_analytics](https://github.com/Aletechdev/aledb_growth_analytics/blob/update-growth-2026mar04/aledb_growth.ipynb)
notebook (branch `update-growth-2026mar04`). That notebook includes trends like
project/isolate/mutation growth over time, strain distribution, and publication
timelines. Ideally the homepage dashboard would surface a live version of these
insights rather than static snapshots — the Tier 1 and Tier 3 approaches below
both support this since they query the database directly.

## Current state

The `#stats` section is a two-column grid:

1. **Left** — an 8-row HTML `<table>` listing observed vs. unique counts per mutation type (substitutions, deletions, insertions, etc.)
2. **Right** — the "largest collection" headline plus a one-liner with totals

All data is already computed server-side via `ObservedMutationCounts`, `UniqueMutationCounts`, and `get_general_count_dict()`.

## Tier 1 — In-page interactive charts (recommended first)

### What changes

| Component | Current | Proposed |
|-----------|---------|----------|
| Stats table | Static HTML `<table>` | Plotly.js / Chart.js charts |
| Headline numbers | Inline text | Animated KPI counter cards |
| Data source | Django template variables | Same data, serialized to JSON via `{{ data\|json_script:"stats-data" }}` |

### Suggested visualizations

1. **KPI cards** (top row) — total observed mutations, unique mutations, isolates, projects, publications. Use a lightweight counter animation on page load (e.g. `countUp.js` or a small vanilla JS tween).
2. **Donut / pie chart** — mutation type breakdown (observed). Hover shows count + percentage. Plotly.js or Chart.js.
3. **Grouped bar chart** — observed vs. unique side-by-side per mutation type. Replaces the table directly.
4. *(Optional)* **Treemap** — mutation types sized by count. Good for showing how dominant single-base substitutions are.
5. **Growth over time** — line chart showing cumulative projects, isolates, or mutations added over time (mirrors the growth trends from the [aledb_growth notebook](https://github.com/Aletechdev/aledb_growth_analytics/blob/update-growth-2026mar04/aledb_growth.ipynb), but live from the database instead of a static snapshot).
6. **Strain / organism distribution** — horizontal bar or treemap of most-studied organisms. Also explored in the notebook.

### Implementation steps

1. **Serialize context to JSON** in `home/views.py`:
   ```python
   import json

   mutation_type_labels = [
       "Single Base Substitutions", "Multiple Base Substitutions",
       "Deletions", "Insertions", "Mobile Element Insertions",
       "Amplifications", "Gene Conversions", "Inversions",
   ]
   observed_values = [
       observed_mutation_counts.single_base_substitution,
       observed_mutation_counts.multiple_base_substitution,
       observed_mutation_counts.deletion,
       observed_mutation_counts.insertion,
       observed_mutation_counts.mobile_element_insertion,
       observed_mutation_counts.amplification,
       observed_mutation_counts.gene_conversion,
       observed_mutation_counts.inversion,
   ]
   unique_values = [
       unique_mutation_counts.single_base_substitution,
       # ... same fields ...
   ]

   context["chart_data"] = json.dumps({
       "labels": mutation_type_labels,
       "observed": observed_values,
       "unique": unique_values,
       "totals": {
           "observed": observed_mutation_counts.total,
           "unique": unique_mutation_counts.total,
           "isolates": general_count_dict["isolate"],
           "projects": general_count_dict["project"],
           "publications": get_unique_publication_count,
       },
   })
   ```

2. **Add chart library** — pick one:
   | Library | Size (min+gz) | Pros | Cons |
   |---------|---------------|------|------|
   | Chart.js 4 | ~70 KB | Simple API, lightweight | Less scientific-looking |
   | Plotly.js (basic) | ~1 MB | Interactive zoom/pan/export, publication-quality | Heavier |
   | Apache ECharts | ~400 KB | Rich chart types, good perf | Steeper learning curve |

   Recommendation: **Plotly.js basic bundle** — the audience is researchers who are used to Plotly from Python notebooks, and the export-to-PNG button is a nice freebie.

   Load via CDN or self-host under `static/js/`:
   ```html
   <script src="https://cdn.plot.ly/plotly-basic-2.35.0.min.js"></script>
   ```

3. **Replace the `#stats` block** in the template:
   ```html
   {# KPI cards #}
   <div class="kpi-row">
     <div class="kpi-card">
       <span class="kpi-value" data-target="{{ count_dict.observed }}">0</span>
       <span class="kpi-label">Observed Mutations</span>
     </div>
     {# ... repeat for unique, isolates, projects, publications #}
   </div>

   {# Charts #}
   <div id="mutation-donut" style="height:400px;"></div>
   <div id="mutation-bar"   style="height:400px;"></div>

   {{ chart_data|json_script:"chart-data" }}

   <script>
     const data = JSON.parse(
       document.getElementById('chart-data').textContent
     );

     // Donut
     Plotly.newPlot('mutation-donut', [{
       labels: data.labels,
       values: data.observed,
       type: 'pie',
       hole: 0.45,
     }], { title: 'Observed Mutations by Type' });

     // Grouped bar
     Plotly.newPlot('mutation-bar', [
       { x: data.labels, y: data.observed, name: 'Observed', type: 'bar' },
       { x: data.labels, y: data.unique,   name: 'Unique',   type: 'bar' },
     ], { barmode: 'group', title: 'Observed vs Unique' });
   </script>
   ```

4. **Style the KPI cards** — minimal CSS:
   ```css
   .kpi-row { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
   .kpi-card { text-align: center; padding: 1.5rem; min-width: 140px;
               border: 1px solid #ddd; border-radius: 8px; }
   .kpi-value { font-size: 2rem; font-weight: 700; display: block; }
   .kpi-label { font-size: 0.85rem; color: #666; }
   ```

5. **Counter animation** (vanilla JS, no dependency):
   ```js
   document.querySelectorAll('.kpi-value').forEach(el => {
     const target = parseInt(el.dataset.target, 10);
     const duration = 1200; // ms
     const start = performance.now();
     (function tick(now) {
       const progress = Math.min((now - start) / duration, 1);
       el.textContent = Math.floor(progress * target).toLocaleString();
       if (progress < 1) requestAnimationFrame(tick);
     })(start);
   });
   ```

### Effort estimate

- View changes: ~30 min
- Template + JS: ~2-3 hours
- CSS polish: ~1 hour
- Testing in Docker container: ~30 min

**Total: roughly half a day.** No new services, no data sync, no licensing.

## Tier 3 (optional) — Self-hosted dashboard tool

If more complex analytics are needed later (filters, drill-downs, user-built dashboards), add a self-hosted BI tool that connects directly to the existing PostgreSQL database.

### Tool comparison

| Tool | License | Docker image | DB connector | Embed support |
|------|---------|-------------|-------------|---------------|
| **Metabase** | AGPL (free self-host) | `metabase/metabase` | Native Postgres | iframe embed, public links |
| **Apache Superset** | Apache 2.0 | `apache/superset` | SQLAlchemy (Postgres) | iframe embed |
| **Grafana** | AGPL | `grafana/grafana` | Native Postgres | iframe embed, panel embed |

Recommendation: **Metabase** — simplest setup, most intuitive for non-technical users (researchers can build their own charts), and the iframe embed is straightforward.

### Implementation steps

1. **Add a Metabase container** to `docker-compose-prod-asgi-host-nginx.yml`:
   ```yaml
   metabase:
     image: metabase/metabase:latest
     container_name: aledb-metabase
     ports:
       - "127.0.0.1:3000:3000"
     environment:
       MB_DB_TYPE: postgres
       MB_DB_DBNAME: metabase_appdb   # Metabase's own metadata DB
       MB_DB_PORT: 5432
       MB_DB_USER: metabase
       MB_DB_PASS: <secret>
       MB_DB_HOST: db
     depends_on:
       - db
     restart: unless-stopped
   ```

2. **Create a read-only Postgres role** for Metabase to query ALEdb data:
   ```sql
   CREATE ROLE metabase_reader WITH LOGIN PASSWORD '<secret>';
   GRANT CONNECT ON DATABASE aledb TO metabase_reader;
   GRANT USAGE ON SCHEMA public TO metabase_reader;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO metabase_reader;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public
     GRANT SELECT ON TABLES TO metabase_reader;
   ```

3. **Configure Metabase** — add the ALEdb database as a data source using the read-only role. Build dashboards for mutation breakdowns, project growth over time, strain distribution, etc.

4. **Proxy through Nginx** (keep Metabase off a public port):
   ```nginx
   location /dashboards/ {
       proxy_pass http://127.0.0.1:3000/;
       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   }
   ```

5. **Embed in the homepage** (or a dedicated `/analytics` page):
   ```html
   <iframe
     src="/dashboards/public/dashboard/<uuid>"
     width="100%" height="600"
     frameborder="0" allowfullscreen>
   </iframe>
   ```

### Effort estimate

- Docker + Nginx config: ~2 hours
- Postgres read-only role: ~15 min
- Building dashboards in Metabase: ~half a day (depends on how many)
- Embed + styling: ~1 hour

**Total: ~1 day** for a basic setup, plus ongoing time designing dashboards.

### Considerations

- Metabase stores its own metadata (questions, dashboards, users) in a separate Postgres database — this needs to be backed up
- Metabase auto-syncs the DB schema periodically; no manual data pipeline needed
- Public embeds do not require Metabase user accounts for viewers
- Metabase's AGPL license allows free self-hosting; no per-user fees

## Recommended rollout

1. **Phase 1** — Tier 1 charts. Quick win, no infrastructure changes. Ship it.
2. **Phase 2** — If researchers want to explore data interactively beyond the homepage, stand up Metabase and link to it from a new "Explore Data" nav item.

Phase 1 and Phase 2 are independent — the Plotly charts on the homepage can coexist with a Metabase instance. Phase 1 serves the "at a glance" story; Phase 2 serves the "let me dig in" use case.
