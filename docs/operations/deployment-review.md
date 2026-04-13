# Deployment Review & Cloud-Native Roadmap

A review of the current ALEDB production deployment on an Azure VM, with a staged roadmap for improving robustness, security, and operational maturity — scoped for a 1-FTE team with no prior deployment experience.

## Current setup — what exists today

- **Single Azure VM** at 4.231.249.59 (aledb.org), nothing redundant.
- **Nginx on the host** terminates TLS (Let's Encrypt/Certbot) and reverse-proxies to a Django/Daphne container on :8000. See [/etc/nginx/sites-enabled/default](/etc/nginx/sites-enabled/default).
- **Database**: Azure Database for MySQL (managed) at `ale.mysql.database.azure.com` — already off the VM. Good.
- **Redis** in a container, port 6379 exposed on the host. No password.
- **Docker Compose** ([docker-compose-prod-asgi-host-nginx.yml](../../docker-compose-prod-asgi-host-nginx.yml)) with the source tree bind-mounted live into the container (`- .:/app`). The Dockerfile `COPY . /app` is overwritten at runtime.
- **`/data/aledata` is an Azure Blob Storage fuse mount** — bulk mutation data already lives in Azure Blob, not on VM disk. This is an important detail: it means the data layer is already partially cloud-native.
- **`/srv/alelog/uploads`** is on VM disk (raw pipeline uploads).
- **Secrets** live in `.docker/one.env`. `.gitignore` excludes `.docker/*.env` so current secrets are not in git. However, `git log --all -- '*.env'` shows a historical `app.env` that was committed — worth auditing whether old credentials leaked into git history.
- **Host mounts into the web container**: `/home/muyao/.ssh:/root/.ssh` for the /pipeline upload feature ([docker-compose-prod-asgi-host-nginx.yml:20](../../docker-compose-prod-asgi-host-nginx.yml#L20)). The web app has full SSH credentials to a personal account.
- **No CI, no staging, no IaC, no automated backup monitoring visible.** Deploys are manual `git pull && docker-compose restart web` (per [CLAUDE.md](../../CLAUDE.md)).

## Risks, ranked

1. **No staging environment.** Every schema change, dependency bump, or template edit ships straight to prod. For 1 FTE with no prior ops experience, this is the scariest thing on the list.
2. **No tested backups / no backup drill.** Azure MySQL has automated backups at the service level — verify they are enabled and do a **restore drill** once. Untested backups are not backups. `/data/aledata` is in Azure Blob (good), but confirm versioning / soft delete is enabled on the storage account so a bad fuse write can be undone. `/srv/alelog/uploads` still needs its own backup plan.
3. **No reproducible image.** Because `.:/app` bind-mounts the working tree, "what's running in prod" is literally whatever's in `/var/www/aledb` on the VM, including uncommitted changes. A rollback means `git checkout <sha>` on the server and hoping it still works. The Dockerfile is effectively untested.
4. **Personal SSH key mounted into the web container.** If the app is ever compromised (SSRF, RCE, dependency chain), the attacker has `muyao@` SSH credentials to wherever that key goes.
5. **Redis has no password and port 6379 is bound to the host.** Bind to `127.0.0.1:6379` only, or drop the `ports:` entry and let containers talk over the internal compose network.
6. **Secrets in a plaintext env file on disk.** Lower priority than the above, but worth fixing eventually.
7. **Single VM = single point of failure.** If Azure reboots the VM or the disk fails, the site is down until rebuild. No alerts.
8. **No monitoring / alerting.** Outages are discovered when users complain.

## Phase 1 — "stop bleeding" (1-2 weeks)

High-leverage items that do not require learning Terraform or cloud-native anything. Do these first.

- **Verify Azure MySQL automated backups are on**, and run a manual point-in-time restore into a test DB once. Write the steps down. This is the single most important item.
- **Verify Blob Storage versioning / soft delete** is enabled on the container behind `/data/aledata`. If it is, an accidental `rm` through the fuse mount is recoverable. If it is not, enable it.
- **Back up `/srv/alelog/uploads`.** Simplest option: nightly `azcopy sync` to an Azure Blob Storage account with lifecycle rules. Cron it, monitor it.
- **Stop bind-mounting source in prod.** Build a real image, tag it with the git SHA, and run that. The compose file becomes `image: aledb:<sha>` instead of `build: .` + `volumes: .:/app`. Deploys become "pull new image, restart." Rollbacks become "run the old tag."
- **Remove the `.ssh` bind mount** from the web container. If the pipeline uploader needs SSH, run it in a separate sidecar that the web app cannot reach, or move the upload flow to a signed-URL pattern.
- **Lock down Redis**: bind to `127.0.0.1` or remove the port publish entirely.
- **Audit git history for leaked secrets** (`git log --all -p -- '*.env' '*.ini' 'config.sh'`). If any real passwords appear, rotate them and consider a `git filter-repo` cleanup.
- **Set up uptime monitoring.** Free tier of UptimeRobot or Better Stack pinging `https://aledb.org/` every 5 minutes with email alerts. 15 minutes of work, catches 80% of outages.

## Phase 2 — "staging + CI" (2-4 weeks)

This is where deploys stop being scary.

- **Second Azure VM as staging**, same OS and Docker setup, pointed at a staging copy of the database. Stop the VM when unused to keep costs down. Use a `staging.aledb.org` DNS entry with a second Let's Encrypt cert.
- **Refresh staging DB nightly from a prod backup** (`az mysql flexible-server restore`). This also incidentally proves backups work.
- **GitHub Actions CI**: on every PR, build the Docker image, run `manage.py check` + any tests. On merge to `master`, push the image to Azure Container Registry tagged with the SHA. Staging auto-deploys on every master merge; prod deploys via a manual "promote" workflow. Roughly 100 lines of YAML, biggest productivity unlock on the list.
- **Document the runbook**: how to deploy, how to roll back, how to restore from backup, who to call. Put it alongside this doc in [docs/operations/](.).

## Phase 3 — "cloud native" (months, only if it actually helps)

- **Terraform for infra.** Worth doing **only after** Phase 1 and 2, because Terraform's value is reproducing infrastructure from scratch, and you need to understand what the infrastructure actually *is* first. Scope: two VMs (prod + staging), the MySQL server, the container registry, DNS, the storage accounts. Maybe 300-500 lines of HCL total. The real win is not day-one provisioning — it is being able to rebuild the whole stack in a new Azure region in half a day.
- **Azure App Service for Containers / Azure Container Apps** instead of a hand-managed VM. Gets you rolling deploys, zero-downtime restarts, auto-TLS, and horizontal scaling with almost no ops work. Downside: you lose the ability to bind-mount `/data/aledata` directly — but since it is already Azure Blob via fuse, the migration path is much shorter than it would be for true VM-disk data. The app would access Blob via the SDK or a signed URL pattern instead of a fuse mount. **Important workflow caveat — see section below.**
- **Azure Key Vault** for secrets. Straightforward once Terraform exists. Before that, not worth the complexity over a `chmod 600` env file.
- **Read replica / geographic failover** for MySQL. Likely overkill for a research database with modest traffic — skip unless there is a specific SLA.

## Should I use Terraform?

**Not yet.** For a 1-FTE beginner, the gap between "I have a VM that works" and "I have Terraform code that provisions the same VM" is several weeks of learning for roughly zero immediate operational improvement. The big wins are in Phase 1 and 2 — backups, staging, CI — and none of those require IaC. Come back to Terraform once you have felt the pain of manually recreating something, because then you will know what you actually want it to do.

## Should I move to Azure Container Apps?

**Probably not in the near term**, and the reason is workflow, not technology.

Today the team's workflow is "SSH into the VM and edit files." Config changes, template tweaks, even Python view edits are done directly on the server. `/data/aledata` is accessed via a FUSE blob mount. `/srv/alelog/uploads` lives on VM disk. The pipeline uploader mounts a personal SSH key.

**On Container Apps, all of that stops working.** There is no persistent filesystem to SSH into, no bind mount of the source tree, no FUSE support, no VM disk. The container is ephemeral — it can be destroyed and recreated by the platform at any time, and any hand-edited change disappears with it. The only way to change anything is: commit → CI builds image → push to registry → deploy new revision → wait 1-3 minutes. Even a one-character template fix goes through that loop.

### What specifically breaks

- **No live file editing.** The `- .:/app` bind mount does not exist on Container Apps.
- **`/data/aledata` FUSE mount does not work.** Container Apps does not support FUSE. Code paths that read from `ALE_DATA_ROOT_DIR` would need to be rewritten to use the Azure Blob SDK or pre-signed URLs.
- **`/srv/alelog/uploads` needs to move.** Either direct-to-Blob uploads via signed URLs, or an Azure Files volume.
- **The pipeline SSH upload flow** is not portable and would need a complete rethink.
- **`docker exec` for debugging** becomes `az containerapp exec` — works but is clunkier and sessions are short-lived.
- **Logs** move out of `/var/www/aledb/logs/` and into Azure Log Analytics, queried via KQL.

### What you get in return

- Atomic deploys, instant rollback by activating a previous revision.
- Zero-downtime rollouts.
- No server to patch, no kernel reboots, no certbot renewals.
- Auto-scale to zero or horizontally.
- A single correct answer to "what is running in prod": the image SHA.

### Honest read

Container Apps is a drastic workflow change happening at the same time as learning CI/CD, Terraform, and cloud-native patterns. That is a lot of simultaneous novelty for a 1-FTE team where the current mental model is "SSH in and edit files."

**The workflow discipline is the hard part. The platform migration is the easy part once the discipline exists.** Fix the discipline on the VM first, and you may find the VM is actually fine.

### Middle ground — "cattle, not pet" VM

This is what is actually recommended for the next 2-3 months:

- Keep the VM, but stop treating it as something you SSH into and edit.
- Image-based deploys driven by CI (identical workflow to what Container Apps would force on you).
- No manual file edits on the server — every change goes through PR → merge → CI → deploy.
- The VM is still SSH-accessible in emergencies, but the team agrees not to use that as a normal workflow.
- `/data/aledata` stays on the FUSE mount, `/srv/alelog/uploads` stays on disk — no data-layer migration needed.

You get ~80% of the discipline benefit of Container Apps without rewriting the `/data/aledata` access code or retraining the team on an entirely new operational model. If and when you outgrow the VM, the migration to Container Apps is then a platform swap — not a platform swap *plus* a workflow revolution *plus* a data-access rewrite all at once.

## Recommended ordering for a 1-FTE

- **Week 1**: verify and test-restore Azure MySQL backups. Confirm Blob versioning on the `/data/aledata` container. Set up UptimeRobot. Remove the `.ssh` mount and Redis port exposure.
- **Week 2**: build a real Docker image, tag it, deploy from the tagged image instead of bind-mount. **Agree as a team to stop editing files directly on the server** — this is the "cattle not pet" discipline shift that pays off regardless of future platform choices.
- **Weeks 3-4**: stand up a staging VM + GitHub Actions that builds on PR and deploys to staging on merge.
- **Month 2+**: revisit this doc. Only consider Container Apps if the VM is actively causing pain — by then the workflow discipline will be in place and the migration will be a platform swap rather than a workflow revolution.
