# Home Page Performance Issues

The home page (`/home`) loads slowly due to several bottlenecks.

## Critical — Full table scans in Python

1. **`get_strains()`** (`ale/utils.py`) — loads ALL `AleId.objects.all()` into memory, then extracts strains via Python set comprehension instead of using `.values_list('strain', flat=True).distinct()` at the DB level.

2. **`get_ref_sequences()`** (`seq/util.py`) — loads ALL `Mutation.objects.all()` into memory to extract the `reseq_reference` field. With potentially millions of mutation rows, this is likely the main culprit.

## Significant — N+1 queries in permission checks

3. **`get_user_projects()`** (`ale/utils.py`) — loops over every project and calls `user.has_perm()` individually, resulting in 2N+ permission queries with no batching. See [optimize-get-user-projects.md](optimize-get-user-projects.md) for proposed fix.

## Moderate — No caching

4. Django's cache framework is configured but none of these expensive queries are cached. The strain list, reference sequences, and counts rarely change but are recomputed on every page load.

## Minor — External resources

5. 7+ external CDN resources (Bootstrap, jQuery, DataTables, Select2, Font Awesome) loaded in the template.

## Suggested fixes (in priority order)

- Fix #1 and #2 by using `.values_list().distinct()` instead of loading full objects
- Add caching for count stats and dropdown data
- Batch permission checks in `get_user_projects()`

## Note: permission filtering for strains and ref sequences

Currently `get_strains()` and `get_ref_sequences()` return all values regardless of user permissions — they expose strain/reference names from private experiments in the dropdowns. Once #3 is solved with an efficient permission check, the same approach should be applied to filter strains and ref sequences to only those the user can access.
