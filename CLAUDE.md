# ALEdb Project Notes

## Git
- Remote is HTTPS (`https://github.com/Aletechdev/aledb.git`), which does not work from Claude Code (no credential helper configured)
- `git push` and `git pull` must be run by the user from their terminal (SSH key forwarding works there)
- Do not switch remote to SSH — it may affect other users on this server

## Key References
- Export architecture: see `docs/export-architecture.md`
- Home page performance: see `docs/home-page-performance.md`
- Docker setup: container `aledb-web`, `/data/aledata` mounted at same path, `/data/export` is NOT mounted
- Templates reload without restart; Python view changes require: `sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml restart web`
