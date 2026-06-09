# Git history scrub — runbook

The runbook for the `git filter-repo` + force-push operation ALEdb went
through on 2026-06-08 to remove historical user data (password hashes +
session logs) and rotated credential literals from git history before
flipping to public. This is preserved as a
template — anyone forking ALEdb (or another small academic OSS project
with a similar credential-accumulation history) can adapt this for their
own scrub.

> **Note:** This is the publish-safe version. Specific credential
> literal values that appear in `--replace-text` mappings are replaced
> with category descriptions. The operator's working copy retained the
> originals during the live run. Researcher names + emails were
> deliberately *kept* — see the README's "Project history and
> provenance" section and the parent [`audit_summary.md`](audit_summary.md).

## Why a history scrub was warranted

A `gitleaks` history scan (2026-06-08) surfaced **43,910 findings
across 6 files** in past commits. The credential literals (Azure /
Gmail / Redis / MySQL / Django) were all rotated and dead — those
alone would have been discretionary to scrub. But
`.docker/data/db_dump.sql` and `mysql/ale_db_*.sql` contained
`auth_user` rows with **Django password hashes** that are crackable,
and `logs/info.log.*` files contained Django request logs with
session IDs and IPs. Those *cannot be rotated* — they are historical
user data. Going public without scrubbing them would have meant
publishing hashes that could be brute-forced to recover 2018-era
user passwords (which may still be in use elsewhere via password reuse).

## Scope

### Paths removed from history entirely (`--invert-paths`)

| Path | Reason |
|---|---|
| `.docker/data/` | Contained `db_dump.sql` — 6 versions × 18-37 MB, full production DB dump with `auth_user` hashes + research data. Directory was already gitignored; nothing in HEAD referenced it. |
| `mysql/` | Contained 2015-era DB dumps (`ale_db_11022015.sql`, `_11042015.sql`, `_11072015.sql`) + schema files. ~37 `gitleaks` findings; contained researcher names and `auth_user` data. Nothing in HEAD under this path. |
| `logs/*.log*` (glob) | Dated app log files (e.g. `info.log.2019-01-15`). JSON request logs with IPs, session IDs, usernames. `gitleaks` didn't flag these (session-ID format didn't match its regexes), but they're large dated artifacts that shouldn't be in a public repo. `logs/__init__.py`, `logs/aledb_logger.py`, `logs/log-backup.sh` (the logger module) stayed in HEAD — only the dated `.log*` files were scrubbed. |
| `ale_info.db` | SQLite snapshot. Not flagged by `gitleaks` (binary; skipped). Removed for consistency with the other dump-style files. |
| `docs/pre_publish_secret_audit.md` | Operator's working audit log; contained live credential values during the rotation period. Untracked at HEAD via a prior commit, but earlier commits still held copies. Cleaner to drop the whole file from history than to scrub each per-commit redaction state. |

### Credential literals redacted from remaining file content (`--replace-text`)

All rotated / functionally dead. Redacted as a "while we're already
running filter-repo" cosmetic cleanup. The values appeared in
historical commits of `pipeline/config.py` (rotated 2026-06-03),
`aleinfo/defaults.py` (Django + Redis rotated mid-2026-06), and the
tracked `.docker/*.env` files (untracked 2026-06-04).

| Literal category | Replaced with |
|---|---|
| 88-char Azure Batch account key | `<AZURE_BATCH_KEY_REDACTED>` |
| 12-char Azure Batch key prefix (referenced in older runbook grep examples) | `<AZURE_BATCH_KEY_PREFIX_REDACTED>` |
| 88-char Azure Storage account key | `<AZURE_STORAGE_KEY_REDACTED>` |
| 32-char Azure Service Principal client secret | `<SP_SECRET_REDACTED>` |
| Gmail SMTP passphrase (account `aledbsoftware@gmail.com`) | `<GMAIL_PASSPHRASE_REDACTED>` |
| Azure MySQL user `ale` password | `<MYSQL_USER_PW_REDACTED>` |
| Redis password (hardcoded fallback) | `<REDIS_PW_REDACTED>` |
| Django `SECRET_KEY` | `<DJANGO_KEY_REDACTED>` |

The replacements file (`/tmp/replacements.txt` during the operation)
had each literal on its own line in `LITERAL==>MARKER` format. The
12-char Batch prefix entry was added during the dry-run after the
first pass left 2 residual hits — `gitleaks` had found the prefix
as a standalone fragment in older versions of `docs/rotation_runbook.md`
that the full 88-char key replacement didn't match.

### What was NOT scrubbed (intentional)

- **Researcher names** — provenance value for academic citation.
- **Institutional email addresses** — already public via lab websites + papers.
- **Git author / committer metadata** — preserves contribution history.
- **The genomic `output.gd` test fixture** flagged by `gitleaks` as a
  false positive — `NC_000913__*__TAACATG...` style E. coli genomic
  coordinates trip the `generic-api-key` regex but are not secrets.

## Pre-flight

```bash
# 1. Install git-filter-repo (into the project venv to avoid system-wide install)
source /var/www/aledb/venv/bin/activate
pip install git-filter-repo
which git-filter-repo   # → /var/www/aledb/venv/bin/git-filter-repo

# 2. Mirror backup of the live repo — recovery point if filter-repo
#    misbehaves or the force-push needs to be reverted
rm -rf /tmp/aledb-prescrub-backup.git
git -C /var/www/aledb clone --mirror . /tmp/aledb-prescrub-backup.git

# 3. Build the replacements file at /tmp/replacements.txt — one literal
#    per line in LITERAL==>MARKER format (do NOT commit this file; it
#    contains the live values).
```

## Dry-run on the mirror backup (do this first)

```bash
# Make a separate mirror for the dry-run; do not reuse the recovery backup
rm -rf /tmp/aledb-scrub.git
git -C /var/www/aledb clone --mirror . /tmp/aledb-scrub.git
cd /tmp/aledb-scrub.git

/var/www/aledb/venv/bin/git-filter-repo \
  --invert-paths \
  --path .docker/data/ \
  --path mysql/ \
  --path-glob 'logs/*.log*' \
  --path ale_info.db \
  --path docs/pre_publish_secret_audit.md \
  --replace-text /tmp/replacements.txt \
  --force

# Verify path removal (expect 0 for each)
for path in ".docker/data/" "mysql/" "logs/info.log" "ale_info.db"; do
  count=$(git log --all --pretty=format: --name-only | grep -c "^$path")
  echo "$path → $count refs in history"
done

# Verify literal redaction — illustrative; substitute the actual prefixes
# from the project's replacements.txt. Expect 0 occurrences for each.
for frag in "<batch-key-prefix>" "<storage-key-prefix>" "<passphrase>" "<other-prefixes>"; do
  count=$(git log --all -p 2>/dev/null | grep -c "$frag")
  echo "'$frag' → $count occurrences"
done

# Verify size reduction
git gc --aggressive --prune=now
du -sh /tmp/aledb-scrub.git   # expect significantly smaller than pre-scrub
```

## Live operation (only after dry-run verifies clean)

**Coordinate first** with any team members who hold local clones,
because every commit SHA from the first affected commit onwards changes.
They'll need to `git reset --hard origin/master` or re-clone after the
push.

```bash
# 1. Apply to the live repo
cd /var/www/aledb
/var/www/aledb/venv/bin/git-filter-repo \
  --invert-paths \
  --path .docker/data/ \
  --path mysql/ \
  --path-glob 'logs/*.log*' \
  --path ale_info.db \
  --path docs/pre_publish_secret_audit.md \
  --replace-text /tmp/replacements.txt \
  --force

# 2. filter-repo strips the remote by default; re-add it
git remote add origin git@github.com:Aletechdev/aledb.git

# 3. Force-push every branch + tags (must run from a shell with SSH
#    keys configured for github.com)
git push --force --all origin
git push --force --tags
```

Note: `--force-with-lease` was tried first on this run but rejected,
because `filter-repo` had rewritten the local `refs/remotes/origin/*`
tracking refs to the post-scrub SHAs — making the lease check think
local-and-remote diverged. After `git fetch` re-synced the tracking
refs, `--force-with-lease` would have worked; we used plain `--force`
to push all branches at once for simplicity.

## Post-scrub verification

```bash
# 1. Site still works (working tree files are unchanged by filter-repo
#    when the only edits are history-rewriting; templates reload without
#    container restart, but a verification curl is cheap)
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8000/    # expect 200

# 2. No leaked-fragment prefixes remain at HEAD or in history
git log --all -p | grep -cE "<prefix1>|<prefix2>|<prefix3>"  # expect 0

# 3. Re-run gitleaks against the cleaned repo
sudo docker run --rm -v /var/www/aledb:/repo \
  -v /tmp/gitleaks-out:/out \
  zricethezav/gitleaks:latest \
  detect --source /repo --no-banner --report-format json --report-path /out/report-post-scrub.json
# For ALEdb the 2026-06-08 post-scrub scan dropped from 43,910 → 2
# findings; the 2 remaining are false positives in builder/tests/.../output.gd
```

## Team notification template

```
Subject: <repo> master was force-pushed — please reset your local clone

Hi team,

I just force-pushed to <repo>'s master to scrub historical user data
before the repo goes public (Django password hashes, app logs with
session data, rotated credential literals). Every commit hash from
<year> onwards has changed.

If you have a local clone, run:

    cd path/to/<repo>
    git fetch origin
    git reset --hard origin/master

Or just re-clone:

    git clone git@github.com:Aletechdev/<repo>.git

Researcher attribution is preserved — your commits still show you as
author, just at different SHAs. Only data dumps, dated log files, and
already-rotated credential literals were removed.

If you have an open feature branch and need help rebasing onto the new
master, ping me. Otherwise, sorry for the disruption and thanks for
re-syncing.
```

(ALEdb didn't end up sending this — the wider team didn't have local
clones, so a reset notice wasn't needed. Kept here for any fork that
does need to coordinate.)

## Recovery if things go wrong

Three layers of safety net, in order of preference:

1. **Mirror backup at `/tmp/aledb-prescrub-backup.git`**: full
   pre-scrub clone. If the live `filter-repo` over-matches or breaks
   something, force-push this mirror back to origin to restore:
   `git -C /tmp/aledb-prescrub-backup.git push --force --mirror`.
2. **Local reflog**: `git reflog` on the live repo retains the
   original commits for ~90 days; `git reset --hard <pre-scrub-sha>`
   recovers them locally. (Won't help if origin is already
   force-pushed; combine with the mirror backup push.)
3. **GitHub orphan-commit retention**: GitHub keeps unreachable
   commits accessible by SHA for weeks-to-indefinitely after
   force-push. Last resort: identify old SHAs via the mirror backup,
   fetch them directly from GitHub.

## Outcome (ALEdb, 2026-06-08)

- Pre-scrub history: 2,973 commits; repo `.git/` ≈ 30 MB.
- Post-scrub history: 2,958 commits (15 dropped because they only
  touched paths that were removed and became empty); repo `.git/` ≈ 12 MB.
- All 7 documented credential literals: 0 occurrences anywhere in
  history (verified per the loop in the post-scrub verification).
- `gitleaks` rescan: 43,910 findings → 2 (both false positives in
  `builder/tests/.../output.gd`).
- Site (https://aledb.org) continued serving HTTP 200 throughout
  (filter-repo doesn't change working-tree file content when the
  edits are history-only).

## Cross-references

- [`audit_summary.md`](audit_summary.md) — parent audit; credential
  inventory + priority tiering + rotation outcome.
- [`../rotation_runbook.md`](../rotation_runbook.md) — credential
  rotation procedures whose outputs were the now-redacted literals.
- [`redis_auth_hardening.md`](redis_auth_hardening.md),
  [`data_disk_migration.md`](data_disk_migration.md),
  [`batch_managed_identity_migration.md`](batch_managed_identity_migration.md),
  [`email_subsystem_review.md`](email_subsystem_review.md) — sibling
  deferred-task docs.
- The README's "Project history and provenance" section — short
  public-facing explanation of the scrub.
