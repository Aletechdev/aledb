# Host changelog

Changes made on the production host that are **not** visible in git: system
configuration, cron jobs, packages, one-off commands. Newest first. Each entry
says what changed, where, why, and how to verify or undo it. Repo copies of the
configuration files live under `ops/host/` (see its README for the working rule).

Do not record secrets here. Paths and settings are fine; passwords, keys and
tokens are not.

## 2026-09-28

- **Weekly traffic report scheduled.** New `/etc/cron.d/aledb-traffic-report`
  runs `scripts/weekly_traffic_report.py` as root every Monday 07:00 UTC and
  writes to `/data/ops_audit/traffic/`. Repo copy: `ops/host/etc/cron.d/`.
  Verify: `cat /etc/cron.d/aledb-traffic-report`; `tail /data/ops_audit/traffic/cron.log`.
  Undo: delete the cron file.
- **Vendored geo lookup package.** `pip install --target scripts/_vendor geoip2fast`
  (git-ignored). Needed by the report; bundles offline country + ASN data.
  Undo: `rm -rf scripts/_vendor`.
- **Claude Code SessionStart hook.** `.claude/settings.local.json` (git-ignored,
  server-local) prints the latest report's Flags line at session start. What to
  do with it is in `CLAUDE.md` § Weekly traffic report.
- **journald retention pinned.** New drop-in `/etc/systemd/journald.conf.d/aledb.conf`
  with `SystemMaxUse=4G` and `MaxRetentionSec=2month`; `systemctl restart systemd-journald`.
  Before: defaults only (10 % of disk capped at 4 GB, no age limit). Repo copy:
  `ops/host/etc/systemd/journald.conf.d/`. Verify: `journalctl --disk-usage`.
- **nginx log retention 14 → 60 days.** `/etc/logrotate.d/nginx`: `rotate 14` → `rotate 60`.
  Reason: only two weeks of visitor addresses survived, which made the Aug 28 – Sep 13
  traffic question unanswerable (GitHub #84). ~10 MB/day compressed. Repo copy:
  `ops/host/etc/logrotate.d/nginx`.
- **daphne bound to localhost.** Compose change (in git, `a8837a8f`) applied with
  `docker compose ... up -d web`; container recreated 09:58 UTC. Host effect:
  `ss -ltn` shows `127.0.0.1:8000` instead of `0.0.0.0:8000`.
- **Django log retention 5 → 9 weekly backups.** In git (`a8837a8f`); listed here
  because it only took effect with the container recreate above.

## 2026-09-22

- **nginx site config rewritten.** `/etc/nginx/sites-available/default` replaced;
  previous version kept as `default.bak-2026-09-22` (dated 2025-05-28). Changes:
  `X-Forwarded-For` now set to `$remote_addr` (overwrite, not append) so a client
  cannot spoof its address; comments explaining the header handling. Repo copy:
  `ops/host/etc/nginx/sites-available/default`.
- **Container recreated with `--proxy-headers` and journald logging.** Compose change
  in git (`f0d329d6`). From this point the Django logs and the journal record real
  client addresses; before it every request was logged as `172.18.0.1`.
- **Search memory fix deployed** (`2ed00abf`) after the 2026-09-21 outage
  (daphne OOM-killed at 27 GB; ~24 h of 502s). Write-up: `docs/search-performance.md`.

## 2025-05-28

- **nginx site config** last modified before the 2026-09-22 rewrite (date from the
  backup file's mtime; content in `default.bak-2026-09-22` on the host). Details of
  that change were not recorded.
