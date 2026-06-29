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

## Affected code

- `search/views.py` — `search()` (stage timers, toggle reading),
  `_get_observed_mutations()` (forwards skip flags)
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
