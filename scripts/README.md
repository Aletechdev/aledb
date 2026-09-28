# Scripts

## usage_report.py

Generate monthly usage reports from Django application logs (`logs/debug.log*`).

Logs rotate weekly (5 backups kept), so **extract before they rotate away**.

```bash
# Extract & archive a month's logs to /data/export/usage_reports/:
python3 scripts/usage_report.py --month 2026-03 --extract

# Re-generate report from archive (reproducible after logs rotate):
python3 scripts/usage_report.py --archive /data/export/usage_reports/logs_2026-03.jsonl.gz

# Report from live logs without archiving:
python3 scripts/usage_report.py --month 2026-04

# Save report to file:
python3 scripts/usage_report.py --month 2026-03 --archive /data/export/usage_reports/logs_2026-03.jsonl.gz > /data/export/usage_reports/REPORT_2026-03_usage.txt
```

Note: before 2026-09-22 the Django logs recorded every visitor as `172.18.0.1` (Docker bridge), so reports for earlier months cannot be attributed by address. Fixed by `f0d329d6` (daphne `--proxy-headers`); see https://github.com/Aletechdev/aledb/issues/61 and #84.

## weekly_traffic_report.py

Weekly visitor report from the **host nginx access logs** (real client IPs, user agents, status codes). Classifies addresses as crawler / datacenter / rotating-proxy scraper / human-like, compares with the previous week, and raises flags for 5xx spikes, kernel OOM kills of daphne, week-over-week swings, single heavy addresses, port 8000 exposure and low disk. File-only output, nothing is sent anywhere.

```bash
sudo python3 scripts/weekly_traffic_report.py                 # last 7 full days (UTC)
sudo python3 scripts/weekly_traffic_report.py --end 2026-09-21 # a specific week
```

- Output: `/data/ops_audit/traffic/<YYYY-Www>.md` and `.json`, plus `LATEST.md` and `cron.log`. Private ops data (contains IPs); keep out of the public repo.
- Scheduled by `/etc/cron.d/aledb-traffic-report`, Monday 07:00 UTC.
- Needs root (nginx logs, `journalctl`) and the vendored geo package:
  `python3 -m pip install --target scripts/_vendor geoip2fast` (`scripts/_vendor/` is git-ignored; country + ASN databases are bundled, no network at run time).
- A Claude Code SessionStart hook (`.claude/settings.local.json`) surfaces the latest Flags line; see `CLAUDE.md` § Weekly traffic report.
- Complementary to `usage_report.py`, which is monthly and reads the Django logs.

## check_active_users.py

Check active Django users and login activity.

## reset.sh / seq_reset.sh

Database reset helpers (dev use).
