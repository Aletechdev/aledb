# ALEdb Project Notes

## Git
- Remote is SSH (`git@github.com:Aletechdev/aledb.git`) — switched from HTTPS at some point on 2026-06-04 or earlier
- `git push` and `git pull` must be run by the user from their interactive terminal — that shell has SSH keys + `known_hosts` for `github.com`; Claude Code's session does not (you'll see "Host key verification failed" if you try `git fetch`/`push` from a Claude Code tool call)
- The previous HTTPS-era note said "do not switch to SSH — may affect other users on this server"; the switch happened anyway and prod git operations are working. If anyone else on the server pushes/pulls and hits issues, the fallback is `git -C /var/www/aledb remote set-url origin https://github.com/Aletechdev/aledb.git`

## Key References
- Export architecture: see `docs/export-architecture.md`
- Home page performance: see `docs/home-page-performance.md`
- Docker setup: container `aledb-web`, `/data/aledata` mounted at same path, `/data/export` is NOT mounted
- Templates reload without restart; Python view changes require: `sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml restart web`
