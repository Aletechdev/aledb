# Redis auth + binding hardening — deferred follow-up

Investigated during the pre-publish rotation on 2026-06-04 and **deferred**.
Public exposure is currently blocked at the Azure NSG layer, so the leaked
Redis password is operationally harmless today. This doc captures the
investigation and the fix plan so the work can be picked up later without
having to re-discover everything.

## Investigation summary (2026-06-04)

The audit at [../pre_publish_secret_audit.md](../pre_publish_secret_audit.md)
classified the Redis password as "Buffered — rotate carefully, not gating
the publish." The investigation found:

| Property | Finding |
|---|---|
| `requirepass` on running Redis | **empty** — no authentication enforced (`redis-cli CONFIG GET requirepass` returns blank) |
| Leaked password (was hardcoded as a fallback in source) | **not in use** — `defaults.py` falls back to it only if `REDIS_URL` env is missing; production sets `REDIS_URL=redis://aledb-redis` (no password) in `.docker/one.env`, so the fallback was dead code |
| Tracked source locations of leaked literal (as of investigation) | `aleinfo/defaults.py:364`, `redis.conf:509`, `.docker/app-private.env:22` — all three since cleaned, see **Quick-fix 2026-06-08** below |
| Host port binding | `0.0.0.0:6379` (all interfaces of the public-IP host) |
| Host firewall (ufw) | inactive |
| `iptables INPUT` default policy | ACCEPT |
| **Azure NSG inbound rule for 6379** | **none — port blocked from public internet** ← *the only thing protecting Redis today* |

So the current state is: Redis is reachable from anywhere on the host
network with no authentication, but external network access is blocked by
the cloud-level firewall.

## Quick-fix 2026-06-08 — leaked literal removed from HEAD

The full two-layer hardening (Layer 1 + Layer 2 below) remains deferred,
but the leaked password literal has been scrubbed from all tracked source
files in HEAD so the repo can be made public without exposing the
dead-but-still-published value:

- `aleinfo/defaults.py:363` — the `DEFENDER_REDIS_URL` line was refactored
  from `os.environ.get('REDIS_URL', 'redis://:<leaked>@aledb-redis:6379/1')`
  to `os.environ['REDIS_URL']` (no fallback; fail loud at import). Matches
  the env-var pattern used for the Azure secrets and `DJANGO_SECRET_KEY`.
- `redis.conf` (entire file) — **deleted**. It was a 1373-line copy of the
  stock Redis sample config with only one custom edit (the `requirepass`
  line) and was not loaded by any running container. Anyone who needs a
  Redis config template in the future can grab the upstream sample from
  redis.io.
- `.docker/app-private.env` — untracked from HEAD as part of the broader
  `.docker/*.env` cleanup (same commit that added
  [`.docker/app.env.example`](../../.docker/app.env.example)). Historical
  commits still contain the file; per the audit doc, history rewrite is
  optional since the leaked value is functionally dead anyway.

**Functional state after this quick fix:** unchanged. Redis still has no
`requirepass`, the host port is still bound to `0.0.0.0`, the host
firewall is still inactive, and the NSG is still the only barrier. The
quick fix is purely a HEAD-cleanup operation; the actual hardening below
is still pending.

## Why it's safe to defer

- The leaked literal is not enforcing anything; nothing breaks if it goes
  public.
- The NSG block means no path from the internet to port 6379 today.
- ALEdb's Redis use is light: django-defender lockout state + (potentially)
  Django session cache. Both are self-healing if the data is corrupted.

## Why it's worth doing eventually

- **One NSG rule change away from full exposure.** If anyone ever adds an
  inbound rule for 6379 (e.g., for one-off debugging from a laptop), Redis
  is immediately reachable from that IP — with no password.
- **Host-firewall layer is missing.** The host's `ufw` is inactive and
  `iptables` defaults to ACCEPT. A typical defense-in-depth setup would
  have host-level filtering even with cloud NSG in front. Today there's
  only one barrier.
- **Public-IP binding is over-broad.** Aledb-web reaches Redis via the
  Docker bridge (`aledb-redis:6379`); it doesn't need the host port at all.
  The `ports:` mapping in compose exists for operator convenience and is
  not load-bearing.

## Fix plan (two layers, do both in one pass)

### Layer 1 — tighten the host port binding

In [docker-compose-prod-asgi-host-nginx.yml](../../docker-compose-prod-asgi-host-nginx.yml):

```yaml
  redis:
    container_name: aledb-redis
    image: redis
    ports:
      - "127.0.0.1:6379:6379"   # was: - 6379:6379
```

This binds the host port to loopback only — Docker bridge keeps working
(aledb-web still resolves `aledb-redis:6379` via the internal network),
host operator can still `redis-cli` from the host, but the public IP
no longer exposes the port regardless of NSG state.

### Layer 2 — add a real password

In [docker-compose-prod-asgi-host-nginx.yml](../../docker-compose-prod-asgi-host-nginx.yml):

```yaml
  redis:
    container_name: aledb-redis
    image: redis
    env_file:
      - .docker/one.env
    command: sh -c 'redis-server --requirepass "$$REDIS_PASSWORD"'
    ports:
      - "127.0.0.1:6379:6379"
```

`$$REDIS_PASSWORD` is compose-escape for a literal `$REDIS_PASSWORD` — the
container's `sh` expands it from the env at startup (set via `env_file`),
so the actual password value never appears in compose YAML or in the
Docker image.

In `.docker/one.env` (gitignored):

```
REDIS_PASSWORD=<new 32+ char random value>
REDIS_URL=redis://:<the same value>@aledb-redis:6379/0
```

(env_file lines are literal `KEY=VALUE`; no interpolation between lines,
so the password value appears in two lines verbatim.)

In [aleinfo/defaults.py:364](../../aleinfo/defaults.py#L364):

```python
DEFENDER_REDIS_URL = os.environ['REDIS_URL']    # no fallback — fail loud
```

Removes the hardcoded fallback (matches the `DJANGO_SECRET_KEY`
refactor pattern from 2026-06-04).

### Cleanup of leaked literal in tracked files

Three places still hold the dead leaked-password literal:

| File | Action |
|---|---|
| `aleinfo/defaults.py:364` | Handled by Layer 2 refactor (line gets rewritten) |
| `redis.conf:509` (the `requirepass <leaked>` line) | Delete the line. The file is not loaded by any running container (verified — no `redis-server -c redis.conf` anywhere). Consider deleting the whole file as a follow-up if it's confirmed unused. |
| `.docker/app-private.env:22` (`REDIS_URL=redis://:<leaked>@...`) | This file is **tracked** despite `.gitignore` (added before the rule). Audit doc's broader cleanup step is `git rm --cached .docker/app.env .docker/app-private.env .docker/app-public.env .docker/db.env` — best to do that whole batch together rather than sanitize this one file in place. |

## Smoke test after applying

```bash
# unauthenticated ping should fail
sudo docker exec aledb-redis redis-cli ping
# expect: NOAUTH Authentication required.

# authenticated ping should work
sudo docker exec aledb-redis redis-cli -a "$(grep '^REDIS_PASSWORD=' .docker/one.env | cut -d= -f2-)" ping 2>/dev/null
# expect: PONG

# aledb-web can still reach redis (uses the URL with embedded password)
sudo docker exec aledb-web python -c "
import django; django.setup()
from django.core.cache import cache
cache.set('redis-auth-test', 'ok', 5); print(cache.get('redis-auth-test'))
"
# expect: ok

# public exposure gone
nmap -p 6379 4.231.249.59  # from outside the host: expect filtered/closed
```

## When to revisit

- Before any NSG rule change that might open 6379 (the NSG block is the
  only barrier today).
- As part of the broader audit cleanup of tracked `.docker/*.env` files
  (`git rm --cached` step in the audit) — natural moment to also strip the
  Redis literal.
- Before extending Redis use beyond django-defender (e.g., real session
  cache, queue backend) — at that point the data becomes more valuable to
  protect.

## Cross-references

- [../pre_publish_secret_audit.md](../pre_publish_secret_audit.md) — the
  parent audit; "Buffered" tier item for Redis.
- [../rotation_runbook.md](../rotation_runbook.md) — credential-rotation
  patterns; this doc's Layer 2 follows the same env-var refactor approach.
- [data_disk_migration.md](data_disk_migration.md),
  [batch_managed_identity_migration.md](batch_managed_identity_migration.md)
  — sibling deferred-task docs.
