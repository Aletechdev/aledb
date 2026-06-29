# Django admin search bars are broken across multiple admins #73

## Summary

Four `ModelAdmin` classes have invalid `search_fields` configurations: bare ForeignKey names and (in one case) nonexistent fields. Typing in the admin search box for these pages either returns a `FieldError` or silently fails — the list view itself still loads because `search_fields` is only consulted when the user submits a search.

## Affected admins

| File:line | Admin | Current `search_fields` | Problem |
|---|---|---|---|
| `filter/admin.py:10` | `FilterAdmin` (`AleExperimentFilter`) | `('id', 'ale_experiment')` | `ale_experiment` is a FK → `icontains` against a FK column raises `Related Field got invalid lookup: icontains` |
| `ale/admin.py:18` | `AleExperimentAdmin` | `('name', 'person', 'project')` | `project` is a FK to `Project` — same issue |
| `ale/admin.py:24` | `ProjectAdmin` | `('name', 'user')` | `user` is a FK to `auth.User` — same issue |
| `ale/admin.py:31` | `MediaAdmin` | `('name', 'user')` | **Neither field exists** on `Media` (which only has `description`, `temperature`, `volume`, `substrate`, `stirring_speed`) |

## Why this is silent

`search_fields` is only consulted when a search term is submitted via the admin's `?q=` query string. The default unfiltered list view runs `ORDER BY` only, so all 4 admins appear to work normally until a user actually types into the search bar.

## Suggested fix

Replace bare FK names with related-field paths that point to text columns. Use the `=` prefix on integer columns to switch from `icontains` (which is meaningless on integers) to `exact`.

```python
# filter/admin.py:10
search_fields = ('=id', 'ale_experiment__name', 'ale_experiment__ale_id')

# ale/admin.py:18  (AleExperimentAdmin)
search_fields = ('name', 'person', 'project__name')

# ale/admin.py:24  (ProjectAdmin)
search_fields = ('name', 'user__username', 'user__email')

# ale/admin.py:31  (MediaAdmin)  —  pick fields that actually exist on Media
search_fields = ('description', 'substrate')
```

## Affected code

- `filter/admin.py:7-10`
- `ale/admin.py:13-18` — `AleExperimentAdmin`
- `ale/admin.py:21-25` — `ProjectAdmin`
- `ale/admin.py:28-32` — `MediaAdmin`
