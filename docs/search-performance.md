# Search Performance — `/search/` slow on broad queries

The `/search/` page (and the homepage search form, which submits to the same
`search()` view) is slow for **broad** queries — a common gene or a common
strain that matches many experiments. Narrow queries are already fast. This
doc records what was measured, how, and the candidate fixes — none of which
should be implemented before the open measurement below is resolved.

## Guiding principle: measure before optimizing

Every step here was driven by instrumentation, not guesswork, and it kept
paying off — the first round of timers ruled out table-building entirely and
located the cost in the query+filter stage. Two rules followed for the rest of
this task, and should continue:

1. **Add a timer, look at real numbers, then decide.** Do not optimize a stage
   until a measurement shows it owns the time.
2. **Warm the cache.** The first run after a container restart pays cold-disk
   I/O (a 23s vs 8.8s swing was purely cold-vs-warm cache, not code). Run each
   case twice and keep the second.

## Instrumentation in place

`search/views.py` logs one `"search performance"` line per request to
`logs/debug.log` (JSON), split into stages:

- `time taken` — total
- `filter_seconds` — Stage 1: DB query + `filter_observed_mutations()`
- `build_seconds` — Stage 2: building the HTML mutation table (header + body)
- `skip_global_filter` / `skip_experiment_filter` — the toggle state, so
  filtered vs unfiltered runs are distinguishable in the log

Pull the timings (no `jq` on the host):

```bash
grep -h "search performance" /var/www/aledb/logs/debug.log | tail -10 | \
  grep -oE '"(time taken|filter_seconds|build_seconds|skip_global_filter|skip_experiment_filter|gene)": ?"?[^",}]*'
```

The toggles double as a profiling lever: `?show_global_filtered=1&show_exp_filtered=1`
runs the search with `skip_*=True`, bypassing the filter exclusions — comparing
that to the default isolates the cost of filtering.

## Measured baseline (2026-06-29, `gene=rpoB`, warm)

| Run | `filter_seconds` | `build_seconds` | toggles |
|---|---|---|---|
| Filtered | ~8.4–9.5 | ~0.04 | both off |
| Unfiltered | ~2.9–3.7 | ~0.06 | both on |

Decomposition of the ~9s filtered query:

- **~3.4s — DB query + row fetch** (`mutation__gene__contains='rpoB'`). Paid
  even when filters are skipped; the skip path runs the same query and
  materializes every matched row.
- **~5.6s — filtering overhead** (the Python gene loop **plus** the SQL
  `.exclude(q_queries)`). This is the part that disappears with both toggles on.
- **~0.05s — table build.** Confirmed negligible, always. Pagination of the
  *rendered* table would not help.

This profile only applies to **broad** queries. A narrow one (`strain=1718`)
returns in ~0.06s and never hits this path, so the optimization target is the
common/broad searches only.

## Open question — MEASURE BEFORE IMPLEMENTING

The ~5.6s "filtering overhead" lumps together two different things that have
**different fixes**:

- **A — SQL `.exclude(q_queries)`** in `filter/util.py` (global mutation-ID
  list OR'd with each experiment's frequency cutoffs / ignored mutation IDs).
- **B — the Python gene loop** at `filter/util.py:80-105` (iterates every
  matched row; per row calls `obs_mut.get_experiment_id()` — a 5-relation
  attribute walk — and `set(get_gene_list(mutation.gene))` string parsing).

We have **not** separated A from B. The next step is one more sub-timer around
just the `for obs_mut in queryset` block vs. the `.exclude()` evaluation. If the
time is mostly in A, the loop fixes below are wasted effort and the work shifts
to the query. **Do not implement any fix below until this is measured.**

## Candidate fixes (gated on the measurement above)

If B (the Python loop) is confirmed dominant:

1. **Short-circuit when no gene filters apply.** The loop only needs to run if
   `global_filter_genes` or some experiment's `ignored_genes` is non-empty. If
   the global filter holds only mutation IDs (no genes), this pass may be dead
   weight for most searches — tighten the guard.
2. **Kill the per-row relation walk.** Replace `obs_mut.get_experiment_id()`
   (5 attribute hops, called up to twice per row) with a queryset
   `.annotate()` of the experiment id, read as one attribute. Mechanical, no
   behavior change.
3. **Push gene filtering out of the per-request path.** Either precompute a
   normalized `mutation ↔ gene` table (indexed) so the "are all genes ignored?"
   test becomes a SQL anti-join, or memoize `get_gene_list(mutation.gene)` by
   `mutation.id` (the same mutation recurs across many observed rows, so the
   identical string is re-parsed repeatedly). The normalized-table option also
   addresses the separate ~3.4s `gene__contains` scan.

If A (the SQL exclude) is confirmed dominant, the work is in the query instead
— review the OR-joined per-experiment cutoff conditions in
`filter_observed_mutations()` and whether they can be simplified or indexed.

The ~3.4s `gene__contains` floor is a separate, smaller item: a non-indexable
substring match against a denormalized `gene` string. A proper gene index or
the normalized gene table (fix 3) is the real remedy.

## Memory: unbounded searches (2026-09-21 outage)

The profile above covers *time*. Unbounded searches have a separate *memory*
failure mode that the timers did not show, because the process dies after the
"search performance" line is written.

### What happened

An anonymous reference-only search (`ref_seq=NC_000913`, every other field
blank) was submitted at 04:28:07 container time on 2026-09-21. The view logged
completion at 04:29:09 (`filter_seconds` 36, `build_seconds` 7). At 04:29:40 the
kernel OOM-killed daphne at 27 GB resident on a 31 GB host with no swap, the
container exited, and with no restart policy the site returned 502 for ~24 h
until the container was recreated by hand.

The "table build negligible" finding above is true of the Python loop but not
of what follows it. For a broad search the cost is in **cells**, not rows:

| Search (public projects, anonymous) | observed | distinct mutations | distinct seq. experiments | cells |
|---|---|---|---|---|
| `ref_seq=NC_000913` only | 234,119 | 69,594 | 3,176 | 221 M |
| `strain=511145` only | 202,054 | 64,597 | 2,416 | 156 M |
| `ref_seq=NC_002947` only | 91,314 | 34,024 | 348 | 11.8 M |
| largest single project (124) | 29,545 | 17,952 | 737 | 13.2 M |

`get_mutation_table_body()` allocates a dense mutations x experiments matrix
(`_initialize_table`), copies each row on append, then the view `json.dumps`
the whole matrix, the template embeds it as a script literal, and the response
encodes it again. That is ~120 bytes per cell at peak across five copies, and
221 M cells x 120 B is the 27 GB observed. The page that would have resulted is
~7 GB of HTML, so the request was never going to be useful even if it had
finished.

### Current mitigation: refuse before building (in place)

`search/views.py` runs one aggregate query after parameter parsing and before
any row is materialised:

```
Count('mutation_id', distinct=True) x Count('sequencing_experiment_id', distinct=True)
```

If the product exceeds `MAX_TABLE_CELLS` (20,000,000) the view returns the
search page with a message naming the two counts and asking the user to narrow
by gene, project, position range or mutation type, and logs a warning
(`"search refused: result too large to build"`) with the counts. Otherwise the
search proceeds unchanged. Nothing is trimmed or sampled from an allowed
result; a search is either built in full or refused with an explanation.

Why 20 M: the largest project-scoped public search is 13.2 M cells and works
today (~1.6 GB peak); the smallest unbounded one is 156 M. 20 M keeps peak
memory near 3 GB and does not block any scoped search that currently exists.
The check costs ~7 s on the 221 M case (the one being refused), ~0.1-0.7 s on
normal searches. It counts the raw match, before global/experiment filters, so
it is a slight over-estimate; that only matters at the boundary.

Verified with Django's test client against production data (2026-09-22):
`ref_seq=NC_000913` and `strain=511145` are refused in 8 s and 2 s;
`project=15` and `gene=rpoB` build their tables as before.

### Host-side backstop (compose file)

Independent of the view: `mem_limit` on the web service so a runaway request
is killed inside the container instead of exhausting the host, and
`restart: unless-stopped` so the container comes back on its own. Status is
tracked in `docker-compose-prod-asgi-host-nginx.yml`; as of 2026-09-22 the
journald logging driver and daphne `--proxy-headers` are applied, the limit
and restart policy are not yet.

### Roadmap

1. **Long-form CSV download for refused searches** (next). Offer "download as
   CSV" on the refusal message instead of a dead end. Long form is one row per
   observed mutation (experiment, sample, reference, position, type, change,
   gene, frequency, frequency_gatk, breseq/gatk presence), *not* the wide
   sample matrix, so the size is proportional to observed rows (~234 k rows,
   ~50 MB for the NC_000913 case) rather than cells. Implementation notes:
   - New endpoint reusing `_get_search_params()` / `_get_mut_qryset()` so
     the search and the download can never disagree on what matches.
   - `StreamingHttpResponse` over `queryset.iterator()` with the same
     `select_related` as `filter_observed_mutations()`; constant memory.
   - `filter_observed_mutations()` builds a list; it needs a generator
     variant that applies the same global/experiment gene exclusion per row
     while streaming. Keep one implementation of the exclusion rule.
   - First byte arrives after the DB query (~36 s for NC_000913). nginx
     `proxy_read_timeout` is 3600 s; the page should say it may take a minute.
   - The existing `/export` feature is a ZIP of per-experiment CSVs driven by
     experiment selection, not by search parameters; it is not a shortcut.
   - Test with the two refused searches above and one allowed one.
2. **Serve table data from a separate endpoint** rather than embedding JSON in
   the page. Removes the template and encoding copies (about 3x less peak
   memory for every search size) and makes the page itself small. Prerequisite
   for raising `MAX_TABLE_CELLS` safely.
3. **Sparse cells or an aggregate view for wide searches.** Send only filled
   cells (rows and column indices) and let the JavaScript place them, or above
   some experiment count return one row per mutation with sample/experiment
   counts and a drill-down link. This is the only form in which a
   reference-wide search is both memory-safe and readable; 3,176 columns is
   not a usable table regardless of memory.

## Affected code

- `search/views.py` — `search()` (stage timers, toggle reading, `MAX_TABLE_CELLS`
  size check), `_get_observed_mutations()` (forwards skip flags)
- `seq/views/mutation_table_builder.py` — `_initialize_table()` (dense
  mutations x experiments matrix), `get_mutation_table_body()`
- `filter/util.py:14-105` — `filter_observed_mutations()`; SQL exclude at
  `filter/util.py:68`, Python gene loop at `filter/util.py:80-105`
- `seq/models.py:151` — `ObservedMutation.get_experiment_id()` (per-row
  relation walk)
- `genes/util.py:47` — `get_gene_list()` (per-row gene-string parsing)

## Related

- The same `filter_observed_mutations()` global/experiment filtering is what
  [ISSUE_1_orphaned_global_filter.md](ISSUE_1_orphaned_global_filter.md)
  documents on the feature side; `search/views.py` is its third call site.
- [home-page-performance.md](home-page-performance.md) covers a different set of
  bottlenecks (`get_strains()`, `get_ref_sequences()`, `get_user_projects()`).
