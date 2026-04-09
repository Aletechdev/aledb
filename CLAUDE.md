# ALEdb Project Notes

## Key References
- Export architecture: see `docs/export-architecture.md`
- Docker setup: container `aledb-web`, `/data/aledata` mounted at same path, `/data/export` is NOT mounted
- Templates reload without restart; Python view changes require: `sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml restart web`
