# Data Disk Migration — move Docker storage off the OS disk

Surfaced during the pre-publish credential rotation on 2026-06-04: the OS disk
filled to 100% mid-rotation and blocked `docker-compose up --build`. Symptom
was a `no space left on device` error while overlay2 tried to copy a 2026-05
debug log into a new image layer. A `docker system prune -af` reclaimed ~85 GB
and unblocked the build, but the underlying structural problem is that Docker
writes to the OS disk while a 1 TB data disk sits unmounted.

## Current disk state (2026-06-04)

```
NAME    SIZE   MOUNTED        ROLE
sda1    1024G  (unmounted)    Idle — the disk we want to migrate to
sdb1    128G   /              OS + everything else, was 100% full
sdc1    300G   /mnt           Azure ephemeral — wipes on deallocation,
                              suitable only for caches (blobfuse tmp dirs)
```

`/etc/fstab` has no entry for `sda1`. The partition exists but is not
formatted or mounted. Verify with `sudo file -s /dev/sda1` — if output is
literally just `data` it has no filesystem; if it shows `ext4 filesystem data`
or similar it already has one.

`/var/lib/docker` accumulates rapidly:

| Bucket | Typical size on this host |
|---|---|
| Unused images | tens of GB (51 images = 82 GB in the 2026-06-04 incident) |
| Build cache | a few GB |
| Container layers + overlay2 | grows with every `--build` |

Even with periodic pruning the OS disk will fill again under normal use. Moving
`/var/lib/docker` to the 1 TB disk eliminates the pressure permanently.

## Goal

Mount `sda1` at a stable path (e.g. `/mnt/data-disk` or `/data-disk`) and
relocate Docker's storage there via `data-root` in `/etc/docker/daemon.json`.

Optionally also move `/var/www/aledb/logs/` (684 MB of rotated debug logs on
the OS disk as of 2026-06-04) to the data disk via a bind mount or symlink.

## Pre-migration checks

- [ ] Schedule a maintenance window: this requires stopping the Docker daemon,
      which means `aledb-web`, Redis, and any other containers go down. Plan
      for ~10–20 min of full ALEdb downtime.
- [ ] Confirm `sda1` is healthy: `sudo smartctl -a /dev/sda 2>/dev/null` if
      smartmontools is installed; otherwise inspect Azure portal for the data
      disk's health and size.
- [ ] Snapshot the OS disk in Azure before starting (one-click in the portal),
      so a botched migration is recoverable.
- [ ] Confirm no in-flight pipeline runs (`/pipeline/` page) before stopping
      Docker.

## Migration sequence

1. **Format and mount sda1**
   ```bash
   # only if `sudo file -s /dev/sda1` shows "data" (no filesystem):
   sudo mkfs.ext4 -L data-disk /dev/sda1

   sudo mkdir -p /mnt/data-disk
   UUID=$(sudo blkid -s UUID -o value /dev/sda1)
   echo "UUID=$UUID  /mnt/data-disk  ext4  defaults,nofail  0 2" | sudo tee -a /etc/fstab
   sudo mount /mnt/data-disk
   df -h /mnt/data-disk    # expect ~1 TB available
   ```

2. **Stop Docker and copy existing data**
   ```bash
   sudo systemctl stop docker
   sudo systemctl stop docker.socket
   sudo rsync -aHAX /var/lib/docker/ /mnt/data-disk/docker/
   # verify size matches:
   sudo du -sh /var/lib/docker /mnt/data-disk/docker
   ```

3. **Point Docker at the new path**
   ```bash
   sudo install -m 0644 -o root -g root /dev/null /etc/docker/daemon.json
   # write minimal config; merge with any existing keys if /etc/docker/daemon.json was non-empty
   sudo tee /etc/docker/daemon.json <<'EOF'
   {
     "data-root": "/mnt/data-disk/docker"
   }
   EOF
   ```

4. **Move the old dir aside (don't delete yet) and restart Docker**
   ```bash
   sudo mv /var/lib/docker /var/lib/docker.old
   sudo systemctl start docker
   sudo docker info | grep "Docker Root Dir"   # should print /mnt/data-disk/docker
   ```

5. **Bring containers back up**
   ```bash
   cd /var/www/aledb
   sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml up -d
   sudo docker ps        # aledb-web and aledb-redis should be running
   ```

6. **Functional check**
   - Hit https://aledb.org/ — should load.
   - Hit `/pipeline/` (logged in as staff) — output folders list populates,
     which means Azure SDK + storage key still working.
   - Existing pipeline runs visible.

7. **Reclaim space from the OS disk**
   ```bash
   sudo rm -rf /var/lib/docker.old
   df -h /
   ```

## Optional follow-up — relocate `/var/www/aledb/logs`

The aledb-web container writes Django debug logs into `/var/www/aledb/logs/`
(bind-mounted via `volumes: - .:/app`). These rotated daily and accumulate
hundreds of MB per month. Move the directory to the data disk:

```bash
# stop the container, move the dir, symlink, restart
sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml stop web
sudo mv /var/www/aledb/logs /mnt/data-disk/aledb-logs
sudo ln -s /mnt/data-disk/aledb-logs /var/www/aledb/logs
sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml start web
```

Caveats:
- The symlink must resolve from inside the container too — confirm `docker exec
  aledb-web ls /app/logs/` lists the same content.
- Consider also configuring Django's log rotation to **delete** files older
  than N days, instead of just rotating indefinitely (that's a separate task
  in [logging configuration](../home-page-performance.md) — not actually,
  there's no logging-config doc yet; create one if you go down this path).

## Risks

- **Downtime during step 2** (`rsync /var/lib/docker`). On 100+ GB of layers
  this can take 5–15 minutes.
- **Forgetting `nofail` in fstab**: if the data disk fails to attach on next
  reboot and the entry is mandatory, the system may drop to emergency mode.
- **daemon.json merge**: if `/etc/docker/daemon.json` already exists with
  other keys (e.g. logging driver, registry mirrors), the `tee` above will
  clobber them. Always check existing contents first.

## Why this matters

- **Reliability:** the rotation work nearly stalled because the OS disk hit
  100%. The same condition could take aledb offline (Daphne would fail to
  write its own logs, Django sessions would fail to save).
- **Operability:** the operator running rotations or upgrades shouldn't have
  to first triage disk space.
- **Cost:** the 1 TB data disk is already paid for; not using it is wasted
  spend.

## Cross-references

- [rotation_runbook.md](../rotation_runbook.md) — the rotation work that
  surfaced this.
- [core_dump_audit.md](../core_dump_audit.md) — related lesson about
  unbounded files on the OS disk.
- [docker-migration-todo.md](docker-migration-todo.md) — existing notes on
  Docker setup; revisit before executing.
