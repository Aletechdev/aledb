# Home Page Modernization Ideas

Notes on modernizing the landing page at `/` / `/home`.

- View: [home/views.py](../home/views.py)
- Template: [templates/home/index.html](../templates/home/index.html)

## Current state

- Bootstrap 3.3.7 + jQuery 1.12 + SB Admin 2 theme
- Select2 4.0.3, metisMenu 2.5.2, DataTables 1.10.12 — all loaded from public CDNs
- `gitcdn.github.io` bootstrap-toggle CSS/JS link in [templates/home/index.html:452-453](../templates/home/index.html#L452-L453) — this CDN host has been shut down, so the requests currently 404 on every page load
- A large commented-out sidebar block ([templates/home/index.html:82-137](../templates/home/index.html#L82-L137)) and an unused `toggle_sidebar()` JS function — dead code
- 8-row stats table buries the headline numbers that [home/views.py:29-47](../home/views.py#L29-L47) is already computing
- Monolithic template — does not use `{% extends %}` over a shared `base.html`
- Wall-of-text license section dominates the fold

## Low effort — visual refresh, keep stack

- Replace the hero `table_sample.jpeg` with a short auto-playing WebM/MP4 loop of a real mutation table interaction
- Swap gray-on-white typography for a system font stack + a single accent color
- Collapse the stats table into KPI "cards" (Observed / Unique / Isolates / Projects / Publications)
- Delete the dead sidebar HTML comment block and the `toggle_sidebar` JS
- Wrap the license text in `<details>` collapsed by default

## Medium effort — dependency modernization

- Drop the dead `gitcdn.github.io` bootstrap-toggle link (line 452-453)
- Self-host Bootstrap/jQuery/Select2 via `{% static %}` instead of public CDNs — cleaner CSP story, works offline in dev
- Bootstrap 3 → Bootstrap 5: drops the jQuery requirement, brings flex/grid and modern form controls. Ripples into every other template that extends base styles, so treat as a project, not a PR.

## Higher effort — structural

- Split the monolithic template into `base.html` + `home/index.html` via `{% extends %}`. Every page currently duplicates the header, which is why the landing page still carries sidebar HTML it doesn't use.
- Move the inline search form ([templates/home/index.html:265-356](../templates/home/index.html#L265-L356)) into a small Alpine.js or HTMX island so results can preview inline without a full page nav. The form is the main interactive element on the landing page and would benefit most from this.

## Tradeoff

A pure CSS reskin is a weekend's work. A Bootstrap 3 → 5 upgrade touches every template in the repo and risks breaking experiment/stats/mutations pages.

Suggested ordering: start with dead-code removal + KPI cards + self-hosting CDNs (safe, visible wins). Only tackle the Bootstrap 5 upgrade if there's appetite for a multi-day cross-template effort.
