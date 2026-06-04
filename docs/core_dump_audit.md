# Core Dump Audit — `/var/www/aledb/core`

A 987 MB Python core dump from September 2024 was found on disk during the
[pre-publish secret audit](pre_publish_secret_audit.md). This document explains
what it is, why it contained secrets, why it landed where it did, and how to
prevent future occurrences before deleting the existing file.

## Forensic snapshot

| Field | Value |
|---|---|
| Path | `/var/www/aledb/core` |
| Size | 987,389,952 bytes (~941 MiB) |
| Owner | `aleadmin:aleadmin`, mode `600` |
| Date | 2024-09-21 |
| Source process | `/usr/local/bin/python /usr/local/bin/daphne -b 0.0.0.0 -p 8000 aleinfo.asgi:app` |
| Effective uid/gid | `0` / `0` (root inside container) |
| Git status | Untracked, gitignored via `.gitignore` line 31 (`core`). Never committed. |

## What a core dump is

When a Linux process is terminated by a **dump-producing signal** — most
commonly `SIGSEGV` (segfault), `SIGABRT` (assert / `os.abort()`), `SIGFPE`,
`SIGBUS`, `SIGILL` — the kernel snapshots the entire address space of the
process to a file before tearing it down. The file is the "core dump."

Pure-Python failures (uncaught exceptions, `KeyError`, etc.) do **not** produce
core dumps; Python handles those itself and prints a traceback. Core dumps come
from C-level failures: a segfault in a C extension, a bug in CPython's runtime,
a corrupted heap, or `os.abort()`. The Daphne crash that produced this file was
one of those — likely an issue in an `azure-*` SDK C extension or in the
`cryptography` library.

## Why it contains the Azure secrets

A core dump captures **every byte the process had mapped**: heap, stack,
environment block, loaded code, loaded data. At the moment of the crash, the
Daphne process had imported `pipeline.config`, which held the Azure secrets as
Python `str` objects on the heap. Those bytes sat in RAM and were copied
verbatim into the dump.

This is the reason the secret-fragment grep found them in this file. It's also
the reason the env-var refactor in `pipeline/config.py` (commit `5ce206b`) does
**not** prevent the same exposure in a future dump: the values still get loaded
into process memory. Only credential rotation actually neutralizes leaked
secrets — refactoring removes them from source, not from RAM.

## Why it landed at `/var/www/aledb/core` specifically

The kernel decides where dumps go via `/proc/sys/kernel/core_pattern`. On this
host:

```
core_pattern = |/usr/share/apport/apport -p%p -s%s -c%c -d%d -P%P -u%u -g%g -F%F -- %E
```

The leading `|` means dumps are piped into a handler (Ubuntu's `apport` crash
reporter, which normally writes to `/var/crash/`). However, `core_pattern` is a
**kernel-global** setting — every container shares the host's value — while
the path it points to is resolved from inside the **container's** filesystem.
`/usr/share/apport/apport` does not exist inside the `aledb-web` container.

When the pipe handler fails to execute, the kernel falls back to writing
`./core` in the **process's current working directory**. For Daphne, that was
`/app` inside the container, which is bind-mounted from `/var/www/aledb` on the
host (`volumes: - .:/app` in
[docker-compose-prod-asgi-host-nginx.yml](../docker-compose-prod-asgi-host-nginx.yml)).
So `/app/core` in the container == `/var/www/aledb/core` on the host.

Three things had to align for this file to be created:

1. Daphne crashed with a dump-producing signal.
2. The container's `ulimit -c` was high enough to permit the dump. Docker's
   default for the root user inside a container is `ulimit -c = unlimited`.
3. The host's `core_pattern` pointed to a handler that wasn't reachable from
   inside the container, causing fallback to cwd.

## Preventing future dumps

The narrowest, cleanest fix is to disable core dumps for the `web` service in
the compose file, by adding:

```yaml
  web:
    container_name: aledb-web
    ...
    ulimits:
      core: 0      # disable core dumps; prevents secrets-in-memory from hitting disk
```

to [docker-compose-prod-asgi-host-nginx.yml](../docker-compose-prod-asgi-host-nginx.yml).
After applying and recreating the container, verify:

```bash
sudo docker exec aledb-web bash -c 'ulimit -c'    # should print 0
```

From then on, future Daphne crashes will still log a traceback (or get killed
silently in the case of pure C crashes), but no `core` file will ever be
written to disk again.

Alternatives (rejected as too broad):

- **Set `core_pattern` on the host** to always work, or disable apport. Affects
  every container and every host process — broader blast radius than necessary.
- **Set `ulimit -c 0` in the container's entrypoint command.** Works, but
  buries the policy in a long bash line; less discoverable than `ulimits:` in
  compose.

## Trade-off

Core dumps exist for debuggability. If Daphne segfaults again, a dump is the
fastest path to a root-cause diagnosis. The recommended policy is:

- **Production:** `ulimits: core: 0`. Dumps are a security hazard, and the same
  crash usually reproduces in dev where re-enabling them is trivial.
- **Development / staging:** allow dumps temporarily when actively
  investigating a C-level crash.

For ALEdb's current situation (pending public release, no crash investigation
open), production-disabled is correct.

## Cleanup checklist

Once the items below are done, the existing core dump can be removed safely.

- [ ] Add `ulimits: core: 0` to the `web` service in
      [docker-compose-prod-asgi-host-nginx.yml](../docker-compose-prod-asgi-host-nginx.yml).
- [ ] Recreate the container:
      `sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml up -d --force-recreate web`.
- [ ] Verify: `sudo docker exec aledb-web bash -c 'ulimit -c'` prints `0`.
- [ ] Confirm credential rotation is complete (see
      [pre_publish_secret_audit.md](pre_publish_secret_audit.md)) — the dump's
      contents become dead strings only after rotation.
- [ ] `sudo rm /var/www/aledb/core` — frees ~941 MiB.

## Exposure context

- The file is `mode 600`, owned by `aleadmin`. Only `aleadmin` and `root` can
  read it.
- It is **not** in the git repository (gitignored, never committed). Making
  `aledb` public does not expose this file.
- Anyone with a host backup tarball that includes `/var/www/aledb/` would have
  a copy. Verify backup retention and consider whether existing backups need
  to be scrubbed post-rotation.
