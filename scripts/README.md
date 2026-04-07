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

Note: IP tracking is currently unreliable — most traffic shows `172.18.0.1` (Docker bridge) because the host nginx is missing proxy headers. See https://github.com/Aletechdev/aledb/issues/61

## check_active_users.py

Check active Django users and login activity.

## reset.sh / seq_reset.sh

Database reset helpers (dev use).
