#!/usr/bin/env python3
"""
Generate ALEdb monthly usage report from local application logs.

Usage:
    # Extract March logs to archive, then generate report:
    python3 scripts/usage_report.py --month 2026-03 --extract

    # Generate report from already-extracted archive:
    python3 scripts/usage_report.py --archive /data/export/logs_2026-03.jsonl

    # Generate report from live logs (no archive):
    python3 scripts/usage_report.py --month 2026-03

    # Save report to file:
    python3 scripts/usage_report.py --archive /data/export/logs_2026-03.jsonl > /data/export/REPORT_2026-03_usage.txt
"""

import argparse
import collections
import glob
import gzip
import json
import os
import sys
from datetime import datetime, timedelta

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
EXPORT_DIR = '/data/export/usage_reports'


def get_month_range(month_str):
    """Return (start_date, end_date) as 'YYYY-MM-DD' strings for a given 'YYYY-MM'."""
    year, month = int(month_str[:4]), int(month_str[5:7])
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"
    # end is exclusive, so last valid day is the day before
    end_dt = datetime(int(end[:4]), int(end[5:7]), int(end[8:10])) - timedelta(days=1)
    end_inclusive = end_dt.strftime('%Y-%m-%d')
    return start, end_inclusive


def iter_live_logs(start_date, end_date):
    """Yield JSON entries from live debug.log* files within the date range."""
    log_files = sorted(glob.glob(os.path.join(LOG_DIR, 'debug.log*')))
    # Filter out non-log files like debug.log.py
    log_files = [f for f in log_files if not f.endswith('.py')]

    for f in log_files:
        for line in open(f):
            try:
                entry = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            ts = entry.get('asctime', '')[:10]
            if start_date <= ts <= end_date:
                yield entry


def iter_archive(archive_path):
    """Yield JSON entries from an archived .jsonl or .jsonl.gz file."""
    opener = gzip.open if archive_path.endswith('.gz') else open
    with opener(archive_path, 'rt') as f:
        for line in f:
            try:
                yield json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue


def extract_logs(month_str, compress=True):
    """Extract log entries for a given month into a .jsonl(.gz) archive file."""
    start_date, end_date = get_month_range(month_str)
    ext = '.jsonl.gz' if compress else '.jsonl'
    archive_path = os.path.join(EXPORT_DIR, f'logs_{month_str}{ext}')

    opener = gzip.open if compress else open
    count = 0
    with opener(archive_path, 'wt') as out:
        for entry in iter_live_logs(start_date, end_date):
            out.write(json.dumps(entry) + '\n')
            count += 1

    size_mb = os.path.getsize(archive_path) / (1024 * 1024)
    print(f"Extracted {count:,} entries to {archive_path} ({size_mb:.1f} MB)", file=sys.stderr)
    return archive_path


def parse_entries(entries):
    """Parse log entries into report data."""
    daily_hits = collections.Counter()
    path_hits = collections.Counter()
    user_hits = collections.Counter()
    ip_hits = collections.Counter()
    daily_unique_ips = collections.defaultdict(set)
    daily_unique_users = collections.defaultdict(set)
    func_hits = collections.Counter()
    error_count = 0
    total = 0
    anon_count = 0
    auth_count = 0

    for entry in entries:
        total += 1
        ts = entry.get('asctime', '')[:10]
        path = entry.get('path', '')
        ui = entry.get('userinfo', {})
        user = str(ui.get('username', ''))
        ip = ui.get('ip-addr', '')
        level = entry.get('levelname', '')
        func = entry.get('funcName', '')
        module = entry.get('name', '')

        if not path:
            continue

        daily_hits[ts] += 1
        path_hits[path] += 1
        ip_hits[ip] += 1
        daily_unique_ips[ts].add(ip)

        if user and user != 'AnonymousUser':
            user_hits[user] += 1
            auth_count += 1
            daily_unique_users[ts].add(user)
        else:
            anon_count += 1

        feature = f"{module}:{func}" if module != 'root' else func
        func_hits[feature] += 1

        if level in ('ERROR', 'CRITICAL'):
            error_count += 1

    return {
        'daily_hits': daily_hits,
        'path_hits': path_hits,
        'user_hits': user_hits,
        'ip_hits': ip_hits,
        'daily_unique_ips': daily_unique_ips,
        'daily_unique_users': daily_unique_users,
        'func_hits': func_hits,
        'error_count': error_count,
        'total': total,
        'anon_count': anon_count,
        'auth_count': auth_count,
    }


def print_report(data, title):
    print("=" * 75)
    print(f"ALEDB USAGE REPORT — {title}")
    print("=" * 75)

    # --- Summary ---
    print(f"\n{'SUMMARY':^75}")
    print("-" * 75)
    total_days = len(data['daily_hits'])
    print(f"  Total log entries:        {data['total']:>12,}")
    print(f"  Total errors:             {data['error_count']:>12,}")
    print(f"  Active days:              {total_days:>12}")
    print(f"  Avg requests/day:         {data['total'] // max(total_days, 1):>12,}")
    print(f"  Anonymous requests:       {data['anon_count']:>12,}")
    print(f"  Authenticated requests:   {data['auth_count']:>12,}")
    print(f"  Unique authenticated users: {len(data['user_hits']):>10}")

    # --- Daily traffic ---
    print(f"\n{'DAILY TRAFFIC':^75}")
    print("-" * 75)
    print(f"  {'Date':<14} {'Requests':>10} {'Unique IPs':>12} {'Unique Users':>14}")
    print(f"  {'----':<14} {'--------':>10} {'----------':>12} {'------------':>14}")
    for day in sorted(data['daily_hits'].keys()):
        print(f"  {day:<14} {data['daily_hits'][day]:>10,} "
              f"{len(data['daily_unique_ips'][day]):>12,} "
              f"{len(data['daily_unique_users'].get(day, set())):>14,}")

    # --- Weekly summary ---
    print(f"\n{'WEEKLY SUMMARY':^75}")
    print("-" * 75)
    weekly = collections.defaultdict(lambda: {'requests': 0, 'ips': set(), 'users': set()})
    for day in sorted(data['daily_hits'].keys()):
        dt = datetime.strptime(day, '%Y-%m-%d')
        week_start = (dt - timedelta(days=dt.weekday())).strftime('%Y-%m-%d')
        weekly[week_start]['requests'] += data['daily_hits'][day]
        weekly[week_start]['ips'].update(data['daily_unique_ips'][day])
        weekly[week_start]['users'].update(data['daily_unique_users'].get(day, set()))

    print(f"  {'Week of':<14} {'Requests':>10} {'Unique IPs':>12} {'Unique Users':>14}")
    print(f"  {'-------':<14} {'--------':>10} {'----------':>12} {'------------':>14}")
    for week in sorted(weekly.keys()):
        w = weekly[week]
        print(f"  {week:<14} {w['requests']:>10,} {len(w['ips']):>12,} {len(w['users']):>14,}")

    # --- Top endpoints ---
    print(f"\n{'TOP 25 ENDPOINTS':^75}")
    print("-" * 75)
    print(f"  {'Requests':>10}  {'Endpoint'}")
    print(f"  {'--------':>10}  {'--------'}")
    for path, count in data['path_hits'].most_common(25):
        print(f"  {count:>10,}  {path}")

    # --- Top endpoints (excluding interop API) ---
    print(f"\n{'TOP 20 ENDPOINTS (excluding /interop-query)':^75}")
    print("-" * 75)
    print(f"  {'Requests':>10}  {'Endpoint'}")
    print(f"  {'--------':>10}  {'--------'}")
    non_interop = [(p, c) for p, c in data['path_hits'].most_common(50)
                   if not p.startswith('/interop-query')]
    for path, count in non_interop[:20]:
        print(f"  {count:>10,}  {path}")

    # --- Authenticated users ---
    print(f"\n{'AUTHENTICATED USERS':^75}")
    print("-" * 75)
    print(f"  {'Requests':>10}  {'Username'}")
    print(f"  {'--------':>10}  {'--------'}")
    for user, count in data['user_hits'].most_common(30):
        print(f"  {count:>10,}  {user}")

    # --- Top IPs ---
    print(f"\n{'TOP 15 IP ADDRESSES':^75}")
    print("-" * 75)
    print(f"  {'Requests':>10}  {'IP Address'}")
    print(f"  {'--------':>10}  {'----------'}")
    for ip, count in data['ip_hits'].most_common(15):
        print(f"  {count:>10,}  {ip}")

    # --- Top features ---
    print(f"\n{'TOP 20 FEATURES / VIEW FUNCTIONS':^75}")
    print("-" * 75)
    print(f"  {'Requests':>10}  {'Module:Function'}")
    print(f"  {'--------':>10}  {'---------------'}")
    for feat, count in data['func_hits'].most_common(20):
        print(f"  {count:>10,}  {feat}")

    print("\n" + "=" * 75)
    print("Note: Most traffic shows IP 172.18.0.1 (Docker bridge) due to missing")
    print("proxy headers in nginx config. See https://github.com/Aletechdev/aledb/issues/61")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description='Generate ALEdb monthly usage report')
    parser.add_argument('--month', help='Month to report on (YYYY-MM), e.g. 2026-03')
    parser.add_argument('--archive', help='Path to archived .jsonl or .jsonl.gz file to read from')
    parser.add_argument('--extract', action='store_true',
                        help='Extract log entries for the given month into /data/export/logs_YYYY-MM.jsonl.gz')
    parser.add_argument('--no-compress', action='store_true',
                        help='Do not gzip the extracted archive')
    args = parser.parse_args()

    if not args.month and not args.archive:
        parser.error('Provide --month YYYY-MM and/or --archive <path>')

    # Step 1: Extract if requested
    if args.extract:
        if not args.month:
            parser.error('--extract requires --month')
        archive_path = extract_logs(args.month, compress=not args.no_compress)
        # If no --archive was given, use the freshly extracted one
        if not args.archive:
            args.archive = archive_path

    # Step 2: Build entry iterator
    if args.archive:
        entries = iter_archive(args.archive)
        title = os.path.basename(args.archive)
    else:
        start_date, end_date = get_month_range(args.month)
        entries = iter_live_logs(start_date, end_date)
        title = args.month

    # Step 3: Parse and report
    data = parse_entries(entries)

    # Format title nicely
    if args.month:
        dt = datetime.strptime(args.month, '%Y-%m')
        title = dt.strftime('%B %Y')

    print_report(data, title)


if __name__ == '__main__':
    main()
