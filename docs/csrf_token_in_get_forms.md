# CSRF token leaking into GET request URLs

## Summary

Several templates include `{% csrf_token %}` inside `<form method="get">` forms. Since CSRF protection is only needed for POST/PUT/DELETE requests, the token is unnecessarily appended to the URL query string on form submission.

## Example

The mutations table page (`templates/base_table_template.html`) has a GET form with `{% csrf_token %}`:

```
https://aledb.org/mutations/?csrfmiddlewaretoken=tH5LCFGA1bYi...&ale_experiment_id=748&ale_no=all&sample_type=all&tag_select=All+Tags
```

The `csrfmiddlewaretoken` parameter has no effect on GET requests — Django only checks it on POST.

## Affected templates

- `templates/base_table_template.html` (line 53) — mutations table filter form

## Impact

- **No security risk** — the token is session-specific and changes per request
- **URL clutter** — long token string makes URLs harder to read and share
- **No functional impact** — Django ignores the token on GET requests

## Fix

Remove `{% csrf_token %}` from any `<form method="get">` elements. The CSRF tag should only be used inside POST forms.
