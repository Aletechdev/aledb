# Email subsystem review and modernization — nice-to-have

Surfaced during the pre-publish credential audit on 2026-06-04. The Gmail
account that powered Django's SMTP path is **unrecoverable**, the leaked
credential (a memorable passphrase from 2018; the operator's local-only
audit doc retains the literal value if needed) has been functionally dead
since **30 May 2022** (Google removed Less Secure App Access for consumer Gmail),
and the only feature using SMTP — admin lockout notifications via
`mail.mail_admins` — has been silently failing for ~4 years. The interim
fix landed in commit `<TBD>`: removed the leaked passphrase as a fallback
in [aleinfo/defaults.py:333](../../aleinfo/defaults.py#L333), now requires
`EMAIL_HOST_PASSWORD` as an env var with no default.

That's the minimum change. The proper fix — rebuild the email subsystem
end-to-end — is captured here as a nice-to-have. Not blocking the public
push.

## Current state (as of 2026-06-04)

| Component | State |
|---|---|
| Django `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` (SMTP via Gmail) |
| `EMAIL_HOST` | `smtp.gmail.com:587`, TLS |
| `EMAIL_HOST_USER` | `aledbsoftware@gmail.com` — **account unrecoverable** |
| `EMAIL_HOST_PASSWORD` | Reads `os.environ['EMAIL_HOST_PASSWORD']`; current `.docker/one.env` value is the dead 2018-era passphrase; Gmail rejects it with `535 5.7.8` |
| Code path actually using SMTP | Single call in [accounts/defender_middleware.py:97](../../accounts/defender_middleware.py#L97): `mail.mail_admins("user locked out", ...)` when django-defender locks out a user |
| Behavior today | Lockout happens normally; the `mail_admins` call attempts SMTP, fails, gets swallowed by `fail_silently` semantics, nothing is logged or alerted |

## Why a full review is warranted

- **Account dead, no path to recover.** Whoever owned `aledbsoftware@gmail.com` is unreachable / left the team / Google support unavailable. So you can't just "rotate the app password" — there's no Gmail-side to rotate from.
- **The single use case (admin lockout notifications) hasn't been serving its purpose since 2022.** No human knows when a user gets locked out, despite django-defender being configured to lock people out. Either that feature is important (and needs a working SMTP path) or it isn't (and the `mail_admins` call should be removed).
- **The repo is going public.** Inheriting a dead Gmail integration into a public-facing codebase is a footgun for downstream forks — they'd inherit broken email defaults and not know why.
- **No tests cover the email path** (confirmed via grep for `test_email`, `test_send_mail` — no matches). So if someone fixes it in the future, there's no harness to verify.

## What a proper review would cover

### 1. Use-case audit — what do we actually want email for?

- **Admin lockout notifications** — currently the only configured path. Question: do admins actually want these alerts? If lockouts are rare, an email per event is fine. If they're frequent, maybe a daily digest or Slack webhook is better than SMTP-per-event.
- **Password reset** — Django ships a contrib.auth password-reset view, but `urls.py` does not currently wire it up. Adding it would create a *second* email dependency. Decision: do we want users to be able to reset passwords via email, or is admin-managed reset acceptable for a small academic-user base?
- **System status / health alerts** — currently zero. Future-state: alerts on pipeline failures, blob storage quota, MySQL errors, etc. Probably belongs to an observability tool (Grafana / PagerDuty / Slack), not Django's email path.
- **Outbound email to users** — newsletters, dataset publication notices, etc. Currently zero; mention only if planned.

### 2. Provider selection

Three reasonable choices, each with different trade-offs:

| Provider | Pros | Cons |
|---|---|---|
| **A new Gmail account + app password** | Familiar; free for low volume; admin-and-team can read sent mail | Same single-point-of-failure (one account, one app password); subject to the same deprecations |
| **A transactional-email service** (SendGrid, Postmark, Amazon SES, Mailgun) | Higher reliability; built for app-sent mail; deliverability is better; webhooks for bounces; modern auth (API key, not password) | Costs money at scale (free tier usually generous); one more vendor; needs DNS setup (SPF/DKIM/DMARC) for from-aledb.org |
| **University SMTP relay** (if UCSD provides one) | Free; institutionally maintained; addresses the "we're an academic project" alignment | UCSD's relay may have rate limits, restricted From: addresses, IP allowlist requirements |

### 3. Defaults that make sense for a public repo

Whichever provider is picked, the source defaults should be **off** rather than pointing at a specific provider. Recommended:

```python
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
```

That makes the default behaviour "print emails to stdout" — useful for development, harmless for fresh deployments, doesn't pretend to send mail when no creds are configured. Production then overrides `EMAIL_BACKEND` plus the provider-specific settings via env vars.

### 4. Test coverage

Whatever lands should have at least one happy-path test using Django's `mail.outbox` (the locmem backend captures sent mail without a real SMTP round-trip), so future refactors don't silently re-break the path:

```python
# tests/test_email.py
from django.test import TestCase, override_settings
from django.core import mail

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class LockoutEmailTest(TestCase):
    def test_lockout_triggers_admin_email(self):
        # simulate enough failed logins to trip django-defender
        # assert len(mail.outbox) >= 1
        ...
```

### 5. Cleanup of dead Gmail references

Once a new provider is configured:

- Remove the Gmail-specific lines from [aleinfo/defaults.py:328-333](../../aleinfo/defaults.py#L328-L333) (or generalize them).
- Remove the `EMAIL_HOST_*` lines from `.docker/app.env` / `app-private.env` / `app-public.env` (those files are already on the audit's `git rm --cached` cleanup list).
- Update [aleinfo/defaults.py:335](../../aleinfo/defaults.py#L335) `SERVER_EMAIL = 'aledbsoftware+admin@gmail.com'` to whatever sender address you settle on.
- Consider removing the `mail.mail_admins` call in [accounts/defender_middleware.py:97](../../accounts/defender_middleware.py#L97) if lockout notifications are decided to not be valuable enough to maintain.

## Why this is nice-to-have, not gating

The repo can go public without doing any of the above. The minimum-change refactor (commit `<TBD>`) removed the leaked passphrase from being a hardcoded fallback. Whatever a fork sets `EMAIL_HOST_PASSWORD` to is their concern. The dead Gmail account is documented here as context for anyone who notices the config and wonders why it doesn't work.

## When to revisit

- Before extending Django to send any new email (e.g., enabling password reset).
- If admins start asking "why aren't we getting lockout alerts?"
- As part of any broader observability / alerting redesign (lockout events likely belong on the same channel as other operator alerts, not on a separate SMTP path).
- Before the next pre-publish audit, since the question will come up again.

## Cross-references

- [../pre_publish_secret_audit.md](../pre_publish_secret_audit.md) — the audit that surfaced this, including the 2026-06-04 SMTP test that confirmed the credential is dead.
- [data_disk_migration.md](data_disk_migration.md), [batch_managed_identity_migration.md](batch_managed_identity_migration.md), [redis_auth_hardening.md](redis_auth_hardening.md) — sibling deferred-task docs.
