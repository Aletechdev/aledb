# ALEdb Project Notes

## Git
- Remote is SSH (`git@github.com:Aletechdev/aledb.git`) — switched from HTTPS at some point on 2026-06-04 or earlier
- `git push` and `git pull` must be run by the user from their interactive terminal — that shell has SSH keys + `known_hosts` for `github.com`; Claude Code's session does not (you'll see "Host key verification failed" if you try `git fetch`/`push` from a Claude Code tool call)
- The previous HTTPS-era note said "do not switch to SSH — may affect other users on this server"; the switch happened anyway and prod git operations are working. If anyone else on the server pushes/pulls and hits issues, the fallback is `git -C /var/www/aledb remote set-url origin https://github.com/Aletechdev/aledb.git`

## Weekly traffic report
- `scripts/weekly_traffic_report.py` runs from `/etc/cron.d/aledb-traffic-report` every Monday 07:00 UTC and writes `/data/ops_audit/traffic/<YYYY-Www>.md` (+ `.json`, `LATEST.md`, `cron.log`). File-only; no email.
- A SessionStart hook (`.claude/settings.local.json`, server-local) prints the latest report's `**Flags:**` line. **At the start of a session, read that line.** If it is anything other than `none`, open `LATEST.md`, check the Health and Heaviest-addresses sections, and tell the user what the irregular pattern is and whether it threatens the service (5xx share, OOM kill, a single address above 100k requests, port 8000 exposed, low disk). Also flag it if the `last run` date is more than 8 days old — that means the cron job stopped.
- The report is private ops data (contains visitor IPs). Never paste it into the public repo or a GitHub issue; aggregate numbers only.
- Traffic context: ~85 % of requests are crawlers and a rotating-proxy scraper; genuine human visitors are 20–75 addresses/day. A jump in raw request counts is not, by itself, a usage increase. See GitHub issue #84.

## Host-side changes (outside git)
- Anything changed on the host itself (nginx, logrotate, journald, cron, packages) is recorded in `docs/operations/host-changelog.md`, and the config files are mirrored under `ops/host/` (same path layout as `/etc`). Rule: edit the repo copy, copy it to the live path, add a changelog line, commit both. The weekly traffic report flags `host config drift` when a live file stops matching its repo copy.

## Key References
- Export architecture: see `docs/export-architecture.md`
- Home page performance: see `docs/home-page-performance.md`
- Docker setup: container `aledb-web`, `/data/aledata` mounted at same path, `/data/export` is NOT mounted
- Templates reload without restart; Python view changes require: `sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml restart web`
