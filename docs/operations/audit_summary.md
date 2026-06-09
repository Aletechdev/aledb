# Pre-publish security audit summary

Publish-safe record of the credential audit ALEdb went through before
flipping from a private to a public GitHub repository on 2026-06-08.

This is the high-level inventory and outcome. The operational working
log (live credential values, server-specific commands, full rotation
chronology) was kept as an operator-local document and is not tracked
in this repository.

## Scope

Eight credential categories were inventoried, plus several non-secret
items that were also worth scrubbing from the public-bound source.

## Priority tiering

Credentials were classified into two tiers based on real-world
exploitability if leaked to the public internet.

### Top priority — exploitable from a public-internet leak

These authenticated against services reachable from any IP. A leaked
value was immediately usable. Rotation was a hard gate before flipping
the repository public.

| # | Credential | What it controlled |
|---|---|---|
| 1 | Azure Storage account key | Full read / write to all blob containers (data, output, aledata, images) |
| 2 | Azure Batch account key | Full control of the Batch account — submit / cancel jobs, read job data, manage pools |
| 3 | Azure Service Principal client secret | Authentication as the SP; combined with the SP's role assignments, equivalent of Contributor on the Azure resource group |
| 4 | Django `SECRET_KEY` | Forging session cookies and CSRF / password-reset tokens against `aledb.org` — bypass authentication entirely |

### Buffered — rotate carefully, not gating publish

These authenticated against services behind a network buffer (Azure
NSG, MySQL firewall) or had become functionally dead via vendor
deprecation. Repository exposure was a hygiene concern, not an
immediate-exploit concern.

| # | Credential | Buffer |
|---|---|---|
| 5 | Azure MySQL user `ale` password | Azure MySQL firewall (IP allowlist) limits which IPs can connect |
| 6 | Gmail SMTP password (account `aledbsoftware@gmail.com`) | **Functionally dead** — Google removed Less Secure App Access for consumer Gmail on 30 May 2022; the credential stopped authenticating then |
| 7 | Redis password (hardcoded as fallback) | `requirepass` was never actually enforced on the running Redis; host port 6379 is blocked from the public internet by the Azure NSG |
| 8 | Local-Docker MySQL root password (`MYSQL_ROOT_PASSWORD`) | Dev-only default; only meaningful if reaching the local Docker MySQL container |

## Non-secrets also addressed

- Tenant-identifying Azure values (tenant ID, subscription ID, resource
  group name, gallery + image names) — moved from `pipeline/config.py`
  source into environment variables (`.docker/one.env`, gitignored).
- An outdated cloud server IP in Django's `ALLOWED_HOSTS` — removed; the
  setting now references only the live `aledb.org` deployment.
- A separate finding: a 987 MB process core dump containing in-memory
  snapshots of live secrets was sitting at the repository root.
  Documented in [`../core_dump_audit.md`](../core_dump_audit.md).

## Outcome

All eight credentials were either rotated, made functionally dead, or
declared non-actionable:

- **All four top-priority credentials rotated.** The old SP credential
  was fully deleted from the App Registration. The SP's role
  assignments were tightened to least privilege (Contributor on the
  specific Batch account + Reader on the specific image gallery,
  instead of broader Contributor on the resource group). See
  [`../rotation_runbook.md`](../rotation_runbook.md) for procedures.
- **Azure MySQL `ale` password rotated** via `SET PASSWORD` while
  connected as the user itself.
- **Gmail SMTP** — account is unrecoverable (cannot log in to rotate);
  applied a minimum-change refactor that removed the leaked passphrase
  as a fallback in source — the env var is now required with no
  default. The credential was already operationally dead via the 2022
  LSA deprecation. Rebuild tracked at
  [issue #74](https://github.com/Aletechdev/aledb/issues/74) and
  [`email_subsystem_review.md`](email_subsystem_review.md).
- **Redis password** — scrubbed from source HEAD; the proper
  authentication-enforcement hardening (bind 127.0.0.1 + add a real
  password) is deferred to
  [`redis_auth_hardening.md`](redis_auth_hardening.md).
- **Local-Docker MySQL root password** — dev-only default; not a
  publish gate; new deployments override per
  [`.docker/app.env.example`](../../.docker/app.env.example).

In addition, after all rotations completed, `git filter-repo` was used
to remove the historical literal occurrences AND bulk PII (Django
password hashes + dated session logs) from the git history. The
rewritten history was force-pushed to origin. Post-scrub `gitleaks`
scan dropped from **43,910 findings to 2** (both false positives in a
genomic test fixture flagged by `gitleaks`' generic-API-key regex).

## Exposure context

The repository accumulated credentials over ~8 years (2017–2026) via
patterns typical of small research-software projects:

- Most credentials entered through `.docker/*.env` files committed
  before `.gitignore` patterns caught them.
- Several lived as hardcoded fallbacks in Python source — a common
  pattern for "make local development work without env setup," which
  silently became a public-repo risk once the codebase grew contributors.
- The Gmail SMTP credential had been operationally dead since 2022 but
  stayed in source because the only feature that used it
  (`mail.mail_admins` for admin lockout notifications) failed silently
  via Django's `fail_silently=True` for ~4 years.

The repository was **private the entire time** these credentials were
committed. Exposure was limited to people who had repository access —
current / former team members and external collaborators added over
the years. The risk this audit mitigated was *future* exposure when
flipping the repository public.

## Lessons / patterns for future contributors

1. **No hardcoded fallback values for secrets.** Use
   `os.environ['SECRET_NAME']` (raises `KeyError` at import if missing)
   instead of `os.environ.get('SECRET_NAME', 'fallback')`. The fallback
   pattern hides missing configuration AND leaks a value if a real
   secret ever ends up in the fallback.
2. **`.env` files belong in `.gitignore` BEFORE the first commit.** Use
   `.env.example` (tracked) and `.env` (gitignored, copied from
   example by operators). The repository now has
   [`.docker/app.env.example`](../../.docker/app.env.example) as that
   template.
3. **Periodically scan with a secret scanner.** `gitleaks` (free, fast)
   or `trufflehog`. ALEdb's pre-publish scan revealed 43,910 historical
   findings — most from an accidentally-tracked database dump.
   PR-level scans would prevent that kind of accumulation.
4. **Inspect `fail_silently=True` paths.** Anywhere that swallows
   exceptions is a place where breakage can hide for years — as
   happened here with `mail_admins()` after Google's auth-method
   removal.

## Cross-references

- [`../rotation_runbook.md`](../rotation_runbook.md) — step-by-step
  procedures for the four Azure rotations + SP role tightening.
- [`redis_auth_hardening.md`](redis_auth_hardening.md) — deferred
  hardening plan for the Buffered Redis credential.
- [`data_disk_migration.md`](data_disk_migration.md) — structural
  follow-up surfaced during the audit (1 TB data disk sat unmounted;
  OS disk hit 100% mid-rotation).
- [`batch_managed_identity_migration.md`](batch_managed_identity_migration.md)
  — eliminate Azure Batch shared-key auth in favor of managed identity.
- [`email_subsystem_review.md`](email_subsystem_review.md) — deferred
  rebuild plan for the dead Gmail SMTP path. Also tracked at
  [issue #74](https://github.com/Aletechdev/aledb/issues/74).
- [`../core_dump_audit.md`](../core_dump_audit.md) — separate audit of a
  process core dump containing live in-memory secrets.
- The README's "Project history and provenance" section — public-facing
  one-paragraph explanation of the scrub.
