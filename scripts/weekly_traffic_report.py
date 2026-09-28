#!/usr/bin/env python3
"""
Weekly ALEdb traffic report from the host nginx access logs.

Summarises the last seven full days (UTC), classifies visitors into crawlers,
datacenter scripts, a rotating-proxy scraper and human-like browsers, compares
with the previous week's report, and raises flags for anything that looks
like an incident. Output is file-only; nothing is sent anywhere.

    sudo python3 scripts/weekly_traffic_report.py            # last 7 full days
    sudo python3 scripts/weekly_traffic_report.py --end 2026-09-28
    sudo python3 scripts/weekly_traffic_report.py --days 14

Writes to /data/ops_audit/traffic/ (private, not in git):
    YYYY-Www.md     human-readable report
    YYYY-Www.json   numbers, used for next week's comparison
    LATEST.md       copy of the newest report
    cron.log        one line per run

Needs root (nginx logs are root/adm readable; journalctl for OOM kills) and
the vendored geoip2fast package in scripts/_vendor (see scripts/README.md).
Complementary to scripts/usage_report.py, which reports from the Django logs.
"""

import argparse
import collections
import datetime as dt
import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_vendor"))
from geoip2fast import GeoIP2Fast  # noqa: E402

LOG_GLOB = "/var/log/nginx/access.log*"
OUT_DIR = "/data/ops_audit/traffic"

BOT = re.compile(
    r"bot|crawl|spider|slurp|python|curl|wget|httpx|go-http|java|scrapy|headless|"
    r"facebookexternalhit|petal|bytespider|semrush|ahrefs|mj12|dotbot|gptbot|claude|"
    r"ccbot|amazonbot|applebot|bingbot|yandex|baidu|duckduck|reflection|seranking|"
    r"archive|meta-external|okhttp|node-fetch|axios|libwww|perl|ruby|php|dataprovider|"
    r"censys|shodan|zgrab|masscan|nmap|nuclei|^-$|^$",
    re.I,
)
DATACENTER = re.compile(
    r"amazon|aws|google|microsoft|azure|alibaba|aliyun|hetzner|ovh|digitalocean|linode|"
    r"akamai|oracle|tencent|huawei|cloudflare|vultr|choopa|leaseweb|contabo|scaleway|"
    r"m247|datacamp|server|hosting|host|colo|ionos|godaddy|hostinger|kamatera|latitude|"
    r"packet|equinix|cloud|vps|dedicated|data ?cent|zenlayer|ucloud|kingsoft|baidu|bytedance",
    re.I,
)
ACADEMIC = re.compile(
    r"univ|college|\bedu|research|institute|academ|school|hospital|laborator|CNRS|CSIC|"
    r"CERNET|SUNET|Jisc|UCSD|UNAM|GEANT|RENATER|DFN|Haridus|Teadus|Vetenskap",
    re.I,
)
LINE = re.compile(
    r'^(\S+) \S+ \S+ \[(\d+)/(\w+)/(\d+):(\d\d):\d\d:\d\d [^\]]*\] '
    r'"(?:\S+ )?(\S*)[^"]*" (\d{3}) \S+ "[^"]*" "([^"]*)"'
)
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

# Flag thresholds
FIVEXX_WEEK = 0.01       # share of all requests
FIVEXX_HOUR = 0.10       # share within any single hour
DELTA = 0.50             # week-over-week change in requests or human-like visitors
HEAVY_ADDRESS = 100_000  # requests from one address in a week
DISK_FREE_MIN = 0.10     # free share of the root filesystem


def is_page(path):
    return not (path.startswith("/static") or path.startswith("/aledata")
                or path.startswith("/media") or path.endswith((".ico", ".js", ".css", ".png")))


def open_log(path):
    return gzip.open(path, "rt", errors="replace") if path.endswith(".gz") \
        else open(path, "r", errors="replace")


def parse(start, end):
    """Return per-address stats and per-hour counters for start <= day < end (UTC)."""
    per_ip = collections.defaultdict(lambda: {"hits": 0, "pages": 0, "static": 0, "bot": 0,
                                              "ua": "", "days": set(), "paths": collections.Counter()})
    hours = collections.defaultdict(lambda: {"total": 0, "fivexx": 0})
    status = collections.Counter()
    files = [f for f in glob.glob(LOG_GLOB)
             if dt.datetime.utcfromtimestamp(os.path.getmtime(f)).date() >= start]
    total = 0
    for f in sorted(files):
        with open_log(f) as fh:
            for line in fh:
                m = LINE.match(line)
                if not m:
                    continue
                ip, day, mon, year, hour, path, st, ua = m.groups()
                try:
                    d = dt.date(int(year), MONTHS[mon], int(day))
                except (KeyError, ValueError):
                    continue
                if not (start <= d < end):
                    continue
                total += 1
                status[st[0]] += 1
                h = hours["%s %sh" % (d.isoformat(), hour)]
                h["total"] += 1
                if st.startswith("5"):
                    h["fivexx"] += 1
                r = per_ip[ip]
                r["hits"] += 1
                r["days"].add(d)
                if BOT.search(ua):
                    r["bot"] += 1
                elif not r["ua"]:
                    r["ua"] = ua[:80]
                if path.startswith("/static"):
                    r["static"] += 1
                elif st.startswith("2") and is_page(path):
                    r["pages"] += 1
                    r["paths"][path.split("?")[0]] += 1
    return per_ip, hours, status, total, files


def classify(per_ip):
    country_db = GeoIP2Fast(geoip2fast_data_file=os.path.join(HERE, "_vendor", "geoip2fast", "geoip2fast.dat.gz"))
    asn_db = GeoIP2Fast(geoip2fast_data_file=os.path.join(HERE, "_vendor", "geoip2fast", "geoip2fast-asn.dat.gz"))
    rows = []
    for ip, r in per_ip.items():
        asn = asn_db.lookup(ip).asn_name or "?"
        country = country_db.lookup(ip).country_name or "?"
        if r["bot"]:
            cls = "crawler"
        elif DATACENTER.search(asn):
            cls = "datacenter"
        elif r["hits"] == 1 and r["static"] == 0:
            cls = "proxy-scraper"
        elif r["pages"] > 0 and r["static"] > 0:
            cls = "human-like"
        else:
            cls = "other"
        rows.append({"ip": ip, "hits": r["hits"], "pages": r["pages"], "days": len(r["days"]),
                     "country": country, "asn": asn, "cls": cls, "ua": r["ua"],
                     "paths": r["paths"].most_common(3)})
    return rows


def journal_oom(start, end):
    try:
        out = subprocess.run(
            ["journalctl", "-k", "--since", start.isoformat(), "--until", end.isoformat(),
             "--no-pager", "-o", "short-iso"], capture_output=True, text=True, timeout=120).stdout
    except Exception as e:  # journalctl missing or not permitted
        return ["journalctl unavailable: %s" % e]
    return [l[:19] + " " + l.split("kernel: ", 1)[-1][:90]
            for l in out.splitlines() if "Killed process" in l]


def port_8000_binding():
    try:
        out = subprocess.run(["ss", "-ltn"], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return "unknown"
    binds = [l.split()[3] for l in out.splitlines() if l.split() and l.split()[3].endswith(":8000")]
    return ", ".join(binds) or "not listening"


def fmt_int(n):
    return "{:,}".format(n)


def fmt_pct(x):
    return "%.2f %%" % (100 * x)


def delta(cur, prev):
    if prev in (None, 0):
        return "n/a"
    return "%+.0f %%" % (100 * (cur - prev) / prev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--end", help="first day NOT included (UTC, YYYY-MM-DD); default today")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()
    end = dt.date.fromisoformat(args.end) if args.end else dt.datetime.utcnow().date()
    start = end - dt.timedelta(days=args.days)
    iso = start.isocalendar()
    label = "%d-W%02d" % (iso[0], iso[1])
    os.makedirs(args.out, exist_ok=True)

    per_ip, hours, status, total, files = parse(start, end)
    rows = classify(per_ip)
    by_cls_ips = collections.Counter(r["cls"] for r in rows)
    by_cls_hits = collections.Counter()
    for r in rows:
        by_cls_hits[r["cls"]] += r["hits"]
    human = [r for r in rows if r["cls"] == "human-like"]
    human_country = collections.Counter(r["country"] for r in human)
    human_pages = collections.Counter()
    for r in human:
        human_pages[r["country"]] += r["pages"]
    academic = collections.Counter(r["asn"] for r in human if ACADEMIC.search(r["asn"]))
    fivexx = sum(h["fivexx"] for h in hours.values())
    worst_hour = max(hours.items(), key=lambda kv: kv[1]["fivexx"] / max(kv[1]["total"], 1),
                     default=(None, {"total": 1, "fivexx": 0}))
    worst_share = worst_hour[1]["fivexx"] / max(worst_hour[1]["total"], 1)
    heavy = sorted(rows, key=lambda r: -r["hits"])[:10]
    oom = journal_oom(start, end)
    port = port_8000_binding()
    disk = shutil.disk_usage("/")
    disk_free = disk.free / disk.total

    # Previous week for comparison
    prev = None
    prev_label = "%d-W%02d" % (start - dt.timedelta(days=7)).isocalendar()[:2]
    prev_path = os.path.join(args.out, prev_label + ".json")
    if os.path.exists(prev_path):
        with open(prev_path) as fh:
            prev = json.load(fh)
    p = (prev or {}).get
    n_human = len(human)

    flags = []
    if total and fivexx / total > FIVEXX_WEEK:
        flags.append("5xx share %s over the week" % fmt_pct(fivexx / total))
    if worst_share > FIVEXX_HOUR:
        flags.append("5xx share %s in hour %s" % (fmt_pct(worst_share), worst_hour[0]))
    for l in oom:
        flags.append("kernel OOM kill: %s" % l)
    if p("total") and abs(total - p("total")) / p("total") > DELTA:
        flags.append("requests %s vs last week" % delta(total, p("total")))
    if p("human_like") and abs(n_human - p("human_like")) / p("human_like") > DELTA:
        flags.append("human-like visitors %s vs last week" % delta(n_human, p("human_like")))
    for r in heavy:
        if r["hits"] > HEAVY_ADDRESS:
            flags.append("%s requests from one address (%s, %s, %s)" % (fmt_int(r["hits"]), r["ip"], r["country"], r["asn"][:30]))
    if "0.0.0.0:8000" in port or "[::]:8000" in port or "*:8000" in port:
        flags.append("daphne port 8000 is bound to all interfaces (%s)" % port)
    if disk_free < DISK_FREE_MIN:
        flags.append("root filesystem %s free" % fmt_pct(disk_free))
    if total == 0:
        flags.append("no nginx log lines found for the window")

    md = []
    md.append("# ALEdb weekly traffic, %s (%s to %s)\n" % (label, start.isoformat(), (end - dt.timedelta(days=1)).isoformat()))
    md.append("**Flags:** " + ("; ".join(flags) if flags else "none") + "\n")
    md.append("| Metric | This week | Last week | Change |")
    md.append("|---|---|---|---|")
    md.append("| Requests | %s | %s | %s |" % (fmt_int(total), fmt_int(p("total")) if p("total") is not None else "n/a", delta(total, p("total"))))
    md.append("| 5xx share | %s | %s | |" % (fmt_pct(fivexx / total) if total else "n/a", fmt_pct(p("fivexx_share")) if p("fivexx_share") is not None else "n/a"))
    md.append("| Human-like visitors | %s | %s | %s |" % (n_human, p("human_like") if p("human_like") is not None else "n/a", delta(n_human, p("human_like"))))
    md.append("| Human-like page views | %s | %s | |" % (fmt_int(sum(r["pages"] for r in human)), fmt_int(p("human_pages")) if p("human_pages") is not None else "n/a"))
    for cls in ("crawler", "proxy-scraper", "datacenter", "human-like", "other"):
        share = by_cls_hits[cls] / total if total else 0
        md.append("| %s: addresses / requests / share | %s / %s / %s | %s | |" % (
            cls, fmt_int(by_cls_ips[cls]), fmt_int(by_cls_hits[cls]), fmt_pct(share),
            fmt_pct(p("shares", {}).get(cls)) if p("shares") and p("shares").get(cls) is not None else "n/a"))
    md.append("")
    md.append("## Human-like visitors by country\n")
    md.append("| Country | Addresses | Page views |")
    md.append("|---|---|---|")
    for c, n in human_country.most_common(12):
        md.append("| %s | %d | %d |" % (c, n, human_pages[c]))
    md.append("")
    md.append("## Academic networks among human-like visitors\n")
    md.append("\n".join("- %s: %d" % (a[:60], n) for a, n in academic.most_common(10)) or "- none identified")
    md.append("")
    md.append("## Heaviest addresses\n")
    md.append("| Address | Requests | Class | Country | ASN | User agent |")
    md.append("|---|---|---|---|---|---|")
    for r in heavy:
        md.append("| %s | %s | %s | %s | %s | %s |" % (r["ip"], fmt_int(r["hits"]), r["cls"], r["country"], r["asn"][:35], (r["ua"] or "-")[:50].replace("|", "/")))
    md.append("")
    md.append("## Health\n")
    md.append("- 5xx responses: %s (%s); worst hour %s at %s" % (fmt_int(fivexx), fmt_pct(fivexx / total) if total else "n/a", worst_hour[0], fmt_pct(worst_share)))
    md.append("- Kernel OOM kills in window: %s" % (len(oom) if oom and not oom[0].startswith("journalctl unavailable") else (oom[0] if oom else 0)))
    md.append("- daphne port 8000 bound to: %s" % port)
    md.append("- Root filesystem free: %s" % fmt_pct(disk_free))
    md.append("- Log files read: %d; status classes: %s" % (len(files), ", ".join("%sxx=%s" % (k, fmt_int(v)) for k, v in sorted(status.items()))))
    md.append("")
    md.append("_Generated %s UTC by scripts/weekly_traffic_report.py. Classes: crawler = declared bot user agent; "
              "datacenter = browser user agent from a hosting ASN; proxy-scraper = browser user agent, one request, no assets; "
              "human-like = browser user agent, loaded a page and its static assets, non-hosting ASN._"
              % dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M"))

    md_path = os.path.join(args.out, label + ".md")
    with open(md_path, "w") as fh:
        fh.write("\n".join(md) + "\n")
    shutil.copyfile(md_path, os.path.join(args.out, "LATEST.md"))
    with open(os.path.join(args.out, label + ".json"), "w") as fh:
        json.dump({"label": label, "start": start.isoformat(), "end": end.isoformat(), "total": total,
                   "fivexx_share": (fivexx / total) if total else 0, "human_like": n_human,
                   "human_pages": sum(r["pages"] for r in human),
                   "shares": {c: (by_cls_hits[c] / total if total else 0) for c in by_cls_hits},
                   "human_country": dict(human_country.most_common(30)),
                   "flags": flags, "oom": oom, "port_8000": port}, fh, indent=1)
    with open(os.path.join(args.out, "cron.log"), "a") as fh:
        fh.write("%s %s requests=%d human=%d flags=%d -> %s\n" % (
            dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M"), label, total, n_human, len(flags), md_path))
    print("%s: %s requests, %d human-like visitors, flags: %s" % (label, fmt_int(total), n_human, "; ".join(flags) or "none"))
    print("report:", md_path)


if __name__ == "__main__":
    main()
