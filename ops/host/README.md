# Host configuration mirror

Files under `ops/host/` are copies of configuration that lives **outside the
container and outside the Django code**, on the production host. Git never
sees the live files, so this folder is the record of what they contain and
`docs/operations/host-changelog.md` is the record of when and why they changed.

| Repo copy | Live path on the host | What it controls |
|---|---|---|
| `etc/nginx/sites-available/default` | `/etc/nginx/sites-available/default` | Reverse proxy to daphne, TLS, `/aledata` and `/static` serving, forwarded headers |
| `etc/logrotate.d/nginx` | `/etc/logrotate.d/nginx` | nginx access/error log rotation and retention (60 days) |
| `etc/systemd/journald.conf.d/aledb.conf` | `/etc/systemd/journald.conf.d/aledb.conf` | Journal size cap and 2-month age limit (container stdout goes to journald) |
| `etc/cron.d/aledb-traffic-report` | `/etc/cron.d/aledb-traffic-report` | Weekly traffic report, Mondays 07:00 UTC |

Not mirrored, by design: anything with credentials (`.docker/one.env`,
Let's Encrypt keys) and per-machine Claude Code settings
(`.claude/settings.local.json`).

## Working rule

1. Edit the copy here first.
2. Copy it to the live path and reload the service that reads it.
3. Add a line to `docs/operations/host-changelog.md`.
4. Commit both.

Reload commands:

```bash
sudo cp ops/host/etc/nginx/sites-available/default /etc/nginx/sites-available/default && sudo nginx -t && sudo systemctl reload nginx
sudo cp ops/host/etc/logrotate.d/nginx /etc/logrotate.d/nginx            # read on the next daily run
sudo cp ops/host/etc/systemd/journald.conf.d/aledb.conf /etc/systemd/journald.conf.d/aledb.conf && sudo systemctl restart systemd-journald
sudo cp ops/host/etc/cron.d/aledb-traffic-report /etc/cron.d/aledb-traffic-report  # cron picks it up by itself
```

## Detecting drift

The weekly traffic report (`scripts/weekly_traffic_report.py`) compares every
file under `ops/host/` with its live path and raises a `host config drift`
flag when they differ or the live file is missing. To check by hand:

```bash
for f in $(find ops/host -type f -not -name README.md); do sudo diff -u "$f" "/${f#ops/host/}" && echo "match: /${f#ops/host/}"; done
```

If the live file is the one that is right (someone edited it on the host),
copy it back here and commit, with a changelog line saying so.
