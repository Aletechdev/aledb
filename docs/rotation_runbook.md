# Secret Rotation Runbook — Pre-Publish

Sequenced commands for rotating the three Azure secrets (Storage key, Batch
key, service-principal secret) and the SAS token, then committing the new
values into the (private) `batch-amp` repo. Verification follows
[pre_publish_secret_audit.md](pre_publish_secret_audit.md) Answer B: the
rotation itself is the verification — if we missed a consumer, rotating the
old key surfaces the omission as 403s in logs.

## Context

Each secret has two simultaneous consumers:

| Secret | Consumer 1 (aledb) | Consumer 2 (batch-amp, dormant) |
|---|---|---|
| Storage key | `.docker/one.env`, `/cfg/azure_aledata.{cfg,yaml}`, `/cfg/azure_pipeline_in.cfg`, `/cfg/azure_pipeline_out.cfg` | `/var/www/pipeline/batch-amp/src/config.py:_STORAGE_ACCOUNT_KEY` |
| Batch key   | `.docker/one.env` | `/var/www/pipeline/batch-amp/src/config.py:_BATCH_ACCOUNT_KEY` |
| SP secret   | `.docker/one.env` | `/var/www/pipeline/batch-amp/src/config.py:SECRET` |
| SAS token (output container) | `/upload/.azure-env` | (none) |

batch-amp is dormant (no running process) but the user wants its source kept in
sync with the rotated values for future use. batch-amp's commits get pushed
manually to its private repo (`github.com/Aletechdev/batch-amp.git`).

Confirmed via md5 comparison that aledb and batch-amp use **the same value**
for each shared secret today.

## Prerequisites

### Permissions — **check BEFORE starting Rotation 3**

The four rotations need different permission scopes. Don't discover this
mid-rotation:

| Rotation | What it modifies | Required role |
|---|---|---|
| 1. Storage key | Storage account resource | *Storage Account Contributor* (or higher) on `aledata` |
| 2. Batch key | Batch account resource | *Contributor* on the batch account `ale` |
| 3. **SP secret** | **App registration in Entra ID** | **Owner of the App Registration**, OR Entra ID role *Application Administrator* / *Cloud Application Administrator* / *Global Administrator*. **Subscription-level Contributor is NOT sufficient** — the SP credential lives in the directory plane, not the resource plane. |
| 4. SAS regeneration | Storage account resource (uses key1) | Same as Rotation 1; usually done by whoever ran Rotation 1 |

If you don't hold the role for Rotation 3, you'll be blocked at
`az ad app credential reset` with `Insufficient privileges to complete the
operation` (HTTP 403 against the `/applications/.../addPassword` Graph
endpoint). The fix is one of:

- Ask a tenant admin to **add you as an Owner of the App Registration**
  (`e4fccc0f-8557-4534-82cd-bffe18ff2de9`). One-time grant, future rotations
  unblocked. Best long-term answer.
- Ask the admin to **run Rotation 3 themselves** and hand you the new password
  value out-of-band (a sealed message, a password manager share, etc.).
  Faster for a one-off, but doesn't help next rotation.

Either path works; (a) is preferred for the operator who owns the rotation
runbook going forward.

### az CLI setup

```bash
# az CLI installed and logged in as a subscription/Entra ID admin
az account show         # must succeed
az account set --subscription aee8556f-d2fd-4efd-a6bd-f341a90fa76e

# verify resource locations (note: batch account RG may differ from storage's)
az storage account show --name aledata --query '{rg:resourceGroup,id:id}' -o table
az batch account list --query '[?name==`ale`].{name:name,rg:resourceGroup}' -o table

# install jq if not present (only used to format outputs cleanly)
which jq || sudo apt install -y jq
```

Set shell variables once (no secrets in here yet):

```bash
STORAGE_RG=rg-ALEdb
STORAGE_ACCOUNT=aledata
BATCH_RG=$(az batch account list --query "[?name=='ale'].resourceGroup" -o tsv)
BATCH_ACCOUNT=ale
SP_OBJECT_ID=e4fccc0f-8557-4534-82cd-bffe18ff2de9
```

## Rotation 1 — Storage account key (key2 pattern)

The leaked value is currently active (in use by all consumers). Standard
"rotate the standby first" pattern:

### 1a. Identify which key is the leaked one

```bash
LEAKED=$(grep "^AZURE_STORAGE_ACCOUNT_KEY=" /var/www/aledb/.docker/one.env | cut -d= -f2-)
LEAKED_KEYNAME=$(az storage account keys list --resource-group "$STORAGE_RG" --account-name "$STORAGE_ACCOUNT" \
  --query "[?value=='$LEAKED'].keyName" -o tsv)
echo "Leaked key is: $LEAKED_KEYNAME"   # expect key1 or key2
STANDBY_KEYNAME=$([ "$LEAKED_KEYNAME" = "key1" ] && echo key2 || echo key1)
unset LEAKED
```

### 1b. Regenerate the standby (no impact — it's not in use anywhere)

```bash
NEW_KEY=$(az storage account keys renew \
  --resource-group "$STORAGE_RG" --account-name "$STORAGE_ACCOUNT" \
  --key "$STANDBY_KEYNAME" --query 'value' -o tsv)
echo "new $STANDBY_KEYNAME captured, length: ${#NEW_KEY}"   # expect 88
```

### 1c. Swap all six storage-key locations

```bash
# aledb container env
sudo sed -i "s|^AZURE_STORAGE_ACCOUNT_KEY=.*|AZURE_STORAGE_ACCOUNT_KEY=$NEW_KEY|" \
  /var/www/aledb/.docker/one.env

# blobfuse configs (3 active, 1 dormant yaml)
sudo sed -i "s|^accountKey .*|accountKey $NEW_KEY|" \
  /cfg/azure_aledata.cfg \
  /cfg/azure_pipeline_in.cfg \
  /cfg/azure_pipeline_out.cfg
sudo sed -i "s|^\([[:space:]]*account-key:[[:space:]]*\).*|\1$NEW_KEY|" \
  /cfg/azure_aledata.yaml

# batch-amp source (single-quoted in Python)
sudo sed -i "s|^_STORAGE_ACCOUNT_KEY .*|_STORAGE_ACCOUNT_KEY = '$NEW_KEY'|" \
  /var/www/pipeline/batch-amp/src/config.py

# confirm replacements happened (no value printed)
sudo grep -c "^AZURE_STORAGE_ACCOUNT_KEY=" /var/www/aledb/.docker/one.env
sudo grep -c "^accountKey " /cfg/azure_aledata.cfg /cfg/azure_pipeline_in.cfg /cfg/azure_pipeline_out.cfg
sudo grep -c "^_STORAGE_ACCOUNT_KEY" /var/www/pipeline/batch-amp/src/config.py
```

### 1d. Restart consumers

```bash
# aledb-web (env_file changes need --force-recreate, not restart)
sudo docker-compose -f /var/www/aledb/docker-compose-prod-asgi-host-nginx.yml \
  up -d --force-recreate web

# remount each blobfuse mount (kills old process, starts new one with updated cfg)
for mnt in /data /output /pipeline_inputs; do
  cfg=$(ps auxww | grep "blobfuse $mnt" | grep -v grep | grep -oE "config-file=[^ ]+" | cut -d= -f2)
  tmp=$(ps auxww | grep "blobfuse $mnt" | grep -v grep | grep -oE "tmp-path=[^ ]+" | cut -d= -f2)
  echo "remounting $mnt with $cfg, tmp=$tmp"
  sudo fusermount -u "$mnt"
  sudo blobfuse "$mnt" --tmp-path="$tmp" --config-file="$cfg" \
    -o allow_other -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120
done
```

### 1e. Smoke-test (still on leaked key — should pass)

```bash
# the leaked key is still valid at this point; everything should work as before
sudo docker exec aledb-web python -c "import pipeline.config; print('OK')"
ls /data/aledata/ | head -3
ls /output/ | head -3
ls /pipeline_inputs/ | head -3
```

In the browser, hit `/pipeline/` (must be logged in as staff) and confirm the
output folder list populates. Optionally submit a small pipeline run.

### 1f. Regenerate the leaked key — this is the actual rotation moment

```bash
az storage account keys renew \
  --resource-group "$STORAGE_RG" --account-name "$STORAGE_ACCOUNT" \
  --key "$LEAKED_KEYNAME"
# discard the output; nothing should be using this key anymore
```

### 1g. Re-sync the Batch account's auto-storage key cache (CRITICAL)

The Batch account has a **linked auto-storage account** (`aledata`). Batch
holds its own *cached copy* of one of the storage account keys and uses it to
authenticate when a pool's start-task references blobs via
`autoStorageContainerName` (e.g. ALEdb's pools download `amp.tar` from the
`images` container this way). That cache does **not** auto-refresh when you
rotate the underlying storage key. New nodes will fail their start-task with
`ResourceContainerAccessDenied` until you force a re-sync.

This is not theoretical — it bit us on 2026-06-04 during the first rotation.
The pool that hosted the smoke-test pipeline run after step 1f returned:

```
errorCode: ResourceContainerAccessDenied
errorMsg:  Access for one of the specified Azure Blob container(s) is denied
state:     starttaskfailed
```

Fix immediately — pick one of:

**Portal:** Batch account → *Storage account* (or *Auto-storage account*) →
click **"Sync keys"** (or re-select the linked account and save).

**`az` (no portal needed):**

```bash
az rest --method POST --url \
  "https://management.azure.com/subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-aledb/providers/Microsoft.Batch/batchAccounts/ale/syncAutoStorageKeys?api-version=2024-07-01"
```

After re-syncing, delete any pools that have nodes stuck in
`starttaskfailed` / `unusable` — they won't self-recover, the start-task
result is cached per node:

```bash
sudo docker exec aledb-web python -c "
from pipeline import config
from azure.batch import BatchServiceClient
from azure.batch.batch_auth import SharedKeyCredentials
c = BatchServiceClient(SharedKeyCredentials(config.BATCH_ACCOUNT_NAME, config.BATCH_ACCOUNT_KEY),
                       batch_url=config.BATCH_ACCOUNT_URL)
for p in c.pool.list():
    nodes = list(c.compute_node.list(p.id))
    bad = [n.id for n in nodes if n.state in ('starttaskfailed','unusable')]
    if bad:
        print(f'deleting pool {p.id} (had {len(bad)} broken node(s))')
        c.pool.delete(p.id)
"
```

Then resubmit any pipeline run that was running against the broken pool. The
new pool's start-task will see the refreshed cache and succeed.

### Long-term fix — move Batch auto-storage off shared-key auth

The Batch account's `autoStorage.authenticationMode` defaults to `StorageKeys`,
which is precisely why the rotation broke it. The structural fix is to switch
it to `BatchAccountManagedIdentity`:

- Enable a system-assigned (or user-assigned) managed identity on the Batch
  account.
- Grant that identity `Storage Blob Data Contributor` on `aledata` (or
  scoped to specific containers if that's tight enough).
- Update the Batch account's auto-storage configuration to
  `authenticationMode: BatchAccountManagedIdentity`, referencing the MI.

Once switched, Batch authenticates to `aledata` via AAD instead of a cached
shared key. Future storage-key rotations stop affecting Batch entirely. Same
direction as the env-var / SP-secret cleanup in this runbook — eliminate
shared secrets where AAD identities can do the job.

Not done in this rotation (would have been mid-flight risk). Tracked as a
follow-up — file under [`docs/operations/`](operations/) as a separate task.

### 1h. Watch logs 5–15 min for residual 403s

```bash
# Three terminals or three tail commands in one screen
sudo docker logs -f --since 1m aledb-web 2>&1 | grep -iE "403|401|authoriz|denied|sas|invalid|key"
sudo journalctl -f --since "1 minute ago" | grep -iE "blobfuse|403|fuse|denied"
mount | grep blobfuse                     # all 3 still mounted?
ps -o pid,etime,cmd -C blobfuse           # processes started after the remount?
```

If any 403 appears, the missing consumer is named in the log line. Update it,
restart it, errors stop. If logs stay quiet for 15 min, rotation complete.

```bash
unset NEW_KEY STANDBY_KEYNAME LEAKED_KEYNAME
```

## Rotation 2 — Batch account key

Same pattern. Batch accounts also have `primary` + `secondary` keys.

```bash
LEAKED=$(grep "^AZURE_BATCH_ACCOUNT_KEY=" /var/www/aledb/.docker/one.env | cut -d= -f2-)
LEAKED_KEYNAME=$(az batch account keys list --resource-group "$BATCH_RG" --name "$BATCH_ACCOUNT" \
  --query "{primary:primary, secondary:secondary} | [?value=='$LEAKED']" -o tsv)
# az returns this in a slightly different shape; if the above doesn't work:
az batch account keys list --resource-group "$BATCH_RG" --name "$BATCH_ACCOUNT" -o json
# then by inspection determine which (primary|secondary) matches LEAKED
# set: LEAKED_KEYNAME and STANDBY_KEYNAME accordingly
unset LEAKED

# regenerate standby
NEW_BATCH_KEY=$(az batch account keys renew \
  --resource-group "$BATCH_RG" --name "$BATCH_ACCOUNT" \
  --key-name "$STANDBY_KEYNAME" --query "$STANDBY_KEYNAME" -o tsv)
echo "new $STANDBY_KEYNAME captured, length: ${#NEW_BATCH_KEY}"

# update both consumers
sudo sed -i "s|^AZURE_BATCH_ACCOUNT_KEY=.*|AZURE_BATCH_ACCOUNT_KEY=$NEW_BATCH_KEY|" \
  /var/www/aledb/.docker/one.env
sudo sed -i "s|^_BATCH_ACCOUNT_KEY .*|_BATCH_ACCOUNT_KEY = '$NEW_BATCH_KEY'|" \
  /var/www/pipeline/batch-amp/src/config.py

# recreate aledb-web
sudo docker-compose -f /var/www/aledb/docker-compose-prod-asgi-host-nginx.yml \
  up -d --force-recreate web

# smoke test: trigger a new pipeline run from the web UI
# this exercises BATCH_ACCOUNT_KEY via pool creation

# rotate the leaked key
az batch account keys renew --resource-group "$BATCH_RG" --name "$BATCH_ACCOUNT" \
  --key-name "$LEAKED_KEYNAME"

# watch logs
sudo docker logs -f --since 1m aledb-web 2>&1 | grep -iE "batch|403|401|authoriz"

unset NEW_BATCH_KEY STANDBY_KEYNAME LEAKED_KEYNAME
```

## Rotation 3 — Service principal secret (append-new pattern)

`--append` adds a new credential without removing existing ones, so the old SP
secret keeps working until we explicitly delete it. Mirrors the key2 pattern:
add the new credential → swap configs → verify → delete the old credential.

### Permission requirement (NEW — see "Permissions" note below)

Rotations 1 and 2 only need **resource-level RBAC** on the Storage / Batch
accounts (e.g. *Storage Account Contributor*, *Contributor* on the resource
group), which most operator accounts already have. Rotation 3 is different:
it modifies the application registration in **Microsoft Entra ID (Azure AD)**,
which is a *directory-level* operation. Resource-level RBAC does not grant it.

To run `az ad app credential reset` / `az ad app credential delete` on the
ALEdb service principal, the executing identity must hold **at least one** of:

- Ownership of the App Registration (`e4fccc0f-8557-4534-82cd-bffe18ff2de9`)
  — granted under Entra ID → App registrations → that app → Owners.
- The Entra ID role **Application Administrator** or **Cloud Application
  Administrator** (scoped to the tenant). Less invasive than Global Admin and
  the right choice for the operator who handles SP rotation regularly.
- The Entra ID role **Global Administrator** (works but over-privileged for
  this task).
- Microsoft Graph application permission `Application.ReadWrite.All` with
  admin consent, if rotating via a script identity rather than a human user.

A common failure mode encountered in practice: an operator with full
Subscription Contributor rights still cannot rotate the SP secret, because
"Contributor" is a resource-plane role and the SP credential lives in the
directory plane. The error from `az` typically reads
`Insufficient privileges to complete the operation` or HTTP 403 against the
`/applications/<id>/addPassword` Graph endpoint.

**Workaround if you don't have the role yourself:** ask a tenant admin to do
either (a) grant you ownership of the App Registration once so future
rotations don't need them, or (b) run the `credential reset` + `credential delete`
commands themselves and hand you the new password value out-of-band. Option
(a) is much better for ongoing operations.

```bash
# append a new client secret (output contains the new value once)
NEW_SP_SECRET=$(az ad app credential reset --id "$SP_OBJECT_ID" --append --years 1 \
  --query 'password' -o tsv)
echo "new SP secret captured, length: ${#NEW_SP_SECRET}"   # expect ~32-40 chars

# also capture the new credential's keyId so we know which is which when deleting later
az ad app credential list --id "$SP_OBJECT_ID" --query '[].{keyId:keyId,start:startDateTime,end:endDateTime}' -o table

# update both consumers
sudo sed -i "s|^AZURE_CLIENT_SECRET=.*|AZURE_CLIENT_SECRET=$NEW_SP_SECRET|" \
  /var/www/aledb/.docker/one.env
sudo sed -i "s|^SECRET = .*|SECRET = \"$NEW_SP_SECRET\"|" \
  /var/www/pipeline/batch-amp/src/config.py

# recreate aledb-web
sudo docker-compose -f /var/www/aledb/docker-compose-prod-asgi-host-nginx.yml \
  up -d --force-recreate web

# smoke test: trigger a pipeline run, confirm pool creation succeeds (SP auth path)

# now delete the OLD credential by keyId
# (find the keyId of the old one — it's the one with the older startDateTime)
OLD_SP_KEYID=<the older keyId from the list above>
az ad app credential delete --id "$SP_OBJECT_ID" --key-id "$OLD_SP_KEYID"

# watch logs for SP auth failures
sudo docker logs -f --since 1m aledb-web 2>&1 | grep -iE "AADSTS|service.?principal|client.?secret|invalid.?secret|401"

unset NEW_SP_SECRET OLD_SP_KEYID
```

### Interim mitigation when full deletion is admin-blocked

If you hit the permission wall described above and the admin is slow to grant
deletion rights, there's a useful **partial mitigation** that any
resource-scope owner can do today: **remove the SP's role assignments** at
the scope(s) you control.

The SP's old credential value (e.g. `affafabf-...`) remains technically valid
for AAD authentication — but with no role bindings, an attacker who decoded
the leaked secret can't *do* anything with it. They can call
`/oauth2/token` and get an access token, but every subsequent Azure API call
returns 403.

**Caveats:**

- Role removal affects **every credential on the SP**, including the new one
  you just rotated to. So this only works if either (a) you're going to
  re-grant the role to the SP after the old credential is fully deleted, or
  (b) the SP's role assignments are no longer needed and you're effectively
  decommissioning the SP.
- For ALEdb this means: if you remove the SP's roles, pipeline runs will
  start failing until the role is restored. So either time the removal for a
  maintenance window, or use a *temporary alternate identity* for ALEdb while
  the old credential is awaiting deletion.
- This is *not* a replacement for credential deletion — it's a way to make
  the public-push safe while the deletion paperwork moves through IT.

**Decision recorded 2026-06-04:** for the ALEdb rotation, the role on the
old SP credential `affafabf-...` was removed pending admin access to the
full deletion. Pipeline operations continue to work because the new SP
credential's role bindings are unaffected (different role assignment at the
relevant scope — verify this in your case before applying).

## Rotation 4 — SAS token regeneration

Rotation 1 invalidated the existing SAS (any SAS signed by the old key dies
with that key). Issue a new SAS signed with the new key.

> **Decision recorded 2026-06-04: skipped for ALEdb.** `transfer.sh` is not
> used by the webapp (the upload button calls `webapp-upload.sh` against the
> blobfuse `/output` mount, not the SAS). The last manual invocation of
> `transfer.sh` per `~/.bash_history` was in September 2024. The dead SAS in
> `/upload/.azure-env` is harmless. If `transfer.sh` is ever needed again,
> regenerate the SAS using the commands below — no need to do this
> proactively.

```bash
# regenerate SAS for the output container with the same permissions
# (racwdxltf = read, add, create, write, delete, execute, list, tag, filter)
# expiry: pick a sensible date; the old one was 2034 which is too long
NEW_SAS=$(az storage container generate-sas \
  --account-name aledata --name output \
  --permissions racwdxltf \
  --expiry $(date -u -d '+1 year' '+%Y-%m-%dT%H:%MZ') \
  --auth-mode key \
  -o tsv)
echo "new SAS captured, length: ${#NEW_SAS}"

# update /upload/.azure-env
sudo bash -c "cat > /upload/.azure-env <<EOF
export AZURE_OUTPUT_CONTAINER_SAS='$NEW_SAS'
EOF"
sudo chmod 600 /upload/.azure-env

# smoke-test transfer.sh
source /upload/.azure-env
bash /upload/transfer.sh some-existing-output-folder
# ctrl-c once azcopy starts streaming; if you see "AuthenticationFailed" it didn't take

unset NEW_SAS
```

If transfer.sh is not actually used anymore (the webapp upload button calls
`webapp-upload.sh`, which reads via blobfuse, not via SAS), you can skip this
step entirely and let the SAS stay dead.

## Tighten the SP's role assignments (least privilege)

Independent of any single rotation: a one-time hygiene pass to shrink what
the SP can do, so that a future leak has a smaller blast radius.

### What the SP actually needs

The web app and operator scripts only use the SP for two kinds of operation:

| Operation | API surface | Permission needed |
|---|---|---|
| pool/job/task CRUD, file reads from tasks | Batch data plane (`*.batch.azure.com`) | `Microsoft.Batch/batchAccounts/*` on the Batch account |
| `pool.add` with a custom image from a shared gallery | Batch data plane (validation) | `Microsoft.Compute/galleries/images/versions/read` on the gallery image |

The second one is non-obvious: even when the Batch account is in
`BatchService` mode (pool VMs run in Microsoft's subscription, not yours),
the Batch API still validates that **the caller** has read permission on
any custom image referenced in `imageReference.virtualMachineImageId`. If
that role is missing, `pool.add` fails with:

```
InsufficientPermissions: The user identity used for this operation does not
have the required privelege Microsoft.Compute/galleries/images/versions/read
on the specified resource <gallery-image-version-resource-id>
```

This is *separate* from the role that Microsoft's own Batch service principal
needs to actually read the image bytes — that's configured on the gallery
side, one-time. The SP-side `read` is an authorization gate at submission
time.

### Minimum role profile

| Role | Scope | Why |
|---|---|---|
| `Contributor` | `/subscriptions/<sub>/resourceGroups/rg-aledb/providers/Microsoft.Batch/batchAccounts/ale` | All Batch data-plane API calls |
| `Reader` | `/subscriptions/<sub>/resourceGroups/rg-ALEdb/providers/Microsoft.Compute/galleries/ensembleamp` | Authorize `pool.add` referencing any image version in this gallery |

Two assignments, both narrow. **No subscription-wide or RG-wide roles are
required.**

If `Contributor` on the Batch account is still too permissive (it grants
`listKeys` and `regenerateKey` on the Batch account, which the SP doesn't
need), define a custom role with just the data actions you use:

```bash
BATCH_ID=$(az batch account show -g rg-aledb -n ale --query id -o tsv)

az role definition create --role-definition '{
  "Name": "ALEdb Batch Data Plane",
  "AssignableScopes": ["'"$BATCH_ID"'"],
  "Actions": [],
  "DataActions": [
    "Microsoft.Batch/batchAccounts/pools/*",
    "Microsoft.Batch/batchAccounts/jobs/*",
    "Microsoft.Batch/batchAccounts/jobs/tasks/*",
    "Microsoft.Batch/batchAccounts/jobs/tasks/files/read"
  ],
  "NotActions": [],
  "NotDataActions": []
}'
```

Then use `"ALEdb Batch Data Plane"` in place of `Contributor` in the first
role assignment.

### Apply (safe additive-then-subtract sequence)

```bash
SP_ID=e4fccc0f-8557-4534-82cd-bffe18ff2de9
BATCH_ID=$(az batch account show -g rg-aledb -n ale --query id -o tsv)
GALLERY_ID=$(az sig show -g rg-ALEdb -r ensembleamp --query id -o tsv)

# 1) ADD the narrow assignments first
az role assignment create --assignee "$SP_ID" --role Contributor --scope "$BATCH_ID"
az role assignment create --assignee "$SP_ID" --role Reader      --scope "$GALLERY_ID"

# 2) SMOKE-TEST: submit a pipeline run from the UI. If pool.add succeeds, the
#    two narrow assignments are sufficient and you can safely strip anything
#    broader.

# 3) Inspect what else the SP currently holds; remove broader assignments ONE
#    AT A TIME, smoke-testing between each removal.
az role assignment list --assignee "$SP_ID" \
  --query '[].{role:roleDefinitionName, scope:scope, id:id}' -o table --all

# example removal — replace <id> with the assignment id from the list above:
# az role assignment delete --ids <id>
```

### Common pitfall — discovered 2026-06-04

When tightening, it's tempting to scope `Reader` to the *specific image*
(`/.../images/eAMP_Ubuntu24.04_open`) rather than the gallery
(`/.../galleries/ensembleamp`). Both work today, but image-scoped means
every new image you publish in the gallery would also need a new role
assignment. Gallery-scoped is the pragmatic choice for a single-purpose
gallery like `ensembleamp`. Scope to the specific image only if the gallery
holds images you don't want this SP to enumerate.

Also: gallery-image read is *not* the same as gallery-image-version read.
A role at gallery scope inherits down to all `images/*` and
`images/*/versions/*` paths — you don't need separate version-level grants.

### Verification

After tightening, you should see only the two narrow assignments:

```bash
az role assignment list --assignee "$SP_ID" \
  --query '[].{role:roleDefinitionName, scope:scope}' -o table --all
```

Expected output:

```
Role           Scope
-------------  --------------------------------------------------------
Contributor    /subscriptions/.../batchAccounts/ale
Reader         /subscriptions/.../galleries/ensembleamp
```

And one final functional check: submit a real pipeline run end-to-end (pool
creation, job submission, log retrieval) to exercise every Batch API call
the SP makes.

## batch-amp commit and push

After Rotations 1–3, batch-amp's source has three new values. Commit and push:

```bash
cd /var/www/pipeline/batch-amp
git diff src/config.py    # confirm only the three credential lines changed
git add src/config.py
git commit -m "chore: rotate Azure credentials (storage, batch, SP)"
# push from your local terminal — same as aledb, the remote needs your creds
git push
```

## Post-rotation cleanup

After all four rotations complete and logs are clean:

- [ ] `sudo rm /var/www/aledb/core` — the secret strings in it are now dead.
      See [core_dump_audit.md](core_dump_audit.md) — also apply
      `ulimits: core: 0` from that doc before the cleanup to prevent recurrence.
- [ ] Tick off the items in [pre_publish_secret_audit.md](pre_publish_secret_audit.md).
- [ ] (Optional) `git filter-repo` to scrub the old values from aledb's history.
      Not required for safety once rotation is done — the leaked strings are dead.
- [ ] Consider re-running a fragment sweep with a prefix of each leaked
      credential (capture the prefixes from a private notebook before
      rotating; do not paste them into this runbook) after rotation, to
      confirm no live system still holds an old value in memory or a
      cached config file.

## Failure recovery

If the rotation goes sideways mid-sequence:

- **Wrong key written to a config file:** the rotation is idempotent —
  re-fetch the current `$STANDBY_KEYNAME` value from `az storage account keys list`
  and `sed -i` the correct value in.
- **Container won't start (KeyError on import):** check
  `sudo docker exec aledb-web env | grep AZURE_` — env_file changes
  require `--force-recreate`, not `restart`.
- **Blobfuse mount stuck:** `sudo fusermount -u -z <mount>` (lazy unmount),
  then re-mount. If still stuck, `sudo umount -l <mount>`.
- **Storage rotation made `output` mount fail but you already rotated the old
  key:** the new key is the one you captured in `$NEW_KEY` (already in the four
  config files). Just remount with the current cfg and you're fine.
- **You can't tell which SP credential is the old one:** `az ad app credential list`
  shows `startDateTime` for each; the smaller one is older.

## Why this is safe to do under time pressure

Each rotation is self-verifying: the act of regenerating the leaked key
surfaces any forgotten consumer as a 403 in logs within seconds. There's no
silent failure mode. Worst case is "noisy logs that name what was missed";
the fix is to update that config and restart. Total downtime per rotation is
on the order of seconds (one container recreate + one blobfuse remount cycle).