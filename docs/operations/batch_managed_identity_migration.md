# Migrate Batch auto-storage from `StorageKeys` to `BatchAccountManagedIdentity`

Surfaced on 2026-06-04 during the storage-key rotation: the Batch account `ale`
caches a copy of one of `aledata`'s shared keys and uses it to authenticate to
blob containers referenced via `autoStorageContainerName` in pool start-tasks
(e.g. the `images` container, which holds `amp.tar`). When key1 was rotated,
the cache went stale and any new pool's start-task failed with
`ResourceContainerAccessDenied`, regardless of how clean the rest of the
rotation was. The immediate fix (re-syncing the cache via `az rest .../syncAutoStorageKeys`)
is in [../rotation_runbook.md](../rotation_runbook.md) step 1g.

The **structural fix** — and the subject of this doc — is to stop using
shared keys for the Batch ↔ Storage link entirely.

## Why this matters

- Every future storage-key rotation breaks pool start-tasks until someone
  remembers to re-sync the Batch cache. Easy to forget; bites silently on
  the next run, not at rotation time.
- Same direction as the env-var refactor (`pipeline/config.py` → `.docker/one.env`)
  and the SP-secret rotation: get off shared secrets where AAD identities can
  do the same job. Defense in depth.
- One less thing in the rotation runbook.

## What changes

Today:

```
Batch account `ale`
  └─ autoStorage.authenticationMode = "StorageKeys"
     ↓
     cached storage account key (silently goes stale on rotation)
     ↓
     reads blobs in `aledata` (e.g. images/amp.tar)
```

After migration:

```
Batch account `ale`
  └─ system-assigned (or user-assigned) Managed Identity
  └─ autoStorage.authenticationMode = "BatchAccountManagedIdentity"
     ↓
     authenticates via Azure AD using the MI
     ↓
     `aledata` has the MI granted "Storage Blob Data Reader" (or Contributor)
     ↓
     reads blobs in `aledata`
```

No more shared keys in the picture for Batch↔Storage. Storage key rotations
become irrelevant to Batch.

## Migration plan

1. **Enable a system-assigned managed identity on the Batch account.**

   Portal: Batch account `ale` → *Identity* → System assigned → On → Save.

   `az`:
   ```bash
   az batch account identity assign \
     --resource-group rg-aledb --name ale --system-assigned
   ```

   Capture the new principal ID:
   ```bash
   BATCH_MI=$(az batch account show -g rg-aledb -n ale \
     --query 'identity.principalId' -o tsv)
   ```

2. **Grant the MI access to `aledata`.**

   The minimum role that lets start-tasks read blob containers is
   `Storage Blob Data Reader`. Use `Storage Blob Data Contributor` if any
   Batch task ever needs to write to `aledata` containers (e.g. uploading
   output). Recommend Contributor scoped to the specific containers
   (`data`, `output`, `images`, `reference`) rather than the whole account.

   ```bash
   STORAGE_ID=$(az storage account show -g rg-ALEdb -n aledata --query id -o tsv)

   az role assignment create \
     --assignee-object-id "$BATCH_MI" \
     --assignee-principal-type ServicePrincipal \
     --role "Storage Blob Data Contributor" \
     --scope "$STORAGE_ID"
   ```

3. **Flip `autoStorage.authenticationMode` to `BatchAccountManagedIdentity`.**

   There's no first-class `az batch account` flag for this as of writing —
   patch via REST:

   ```bash
   SUB=$(az account show --query id -o tsv)
   STORAGE_ID=$(az storage account show -g rg-ALEdb -n aledata --query id -o tsv)

   az rest --method PATCH \
     --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/rg-aledb/providers/Microsoft.Batch/batchAccounts/ale?api-version=2024-07-01" \
     --body "{
       \"properties\": {
         \"autoStorage\": {
           \"storageAccountId\": \"$STORAGE_ID\",
           \"authenticationMode\": \"BatchAccountManagedIdentity\"
         }
       }
     }"
   ```

4. **Verify.**

   ```bash
   az batch account show -g rg-aledb -n ale \
     --query 'autoStorage.{mode:authenticationMode,account:storageAccountId}' -o json
   # expect: { "mode": "BatchAccountManagedIdentity", "account": "<storage-id>" }
   ```

5. **Smoke test by submitting a pipeline run.**

   The new pool's start-task should pull `amp.tar` from the `images`
   container using the MI's AAD token, not a cached storage key. If
   `ResourceContainerAccessDenied` re-appears, the role assignment in step 2
   hasn't propagated yet (Azure RBAC can take 5–15 min) or is scoped too
   narrowly — broaden to the storage account, retry, then tighten once
   working.

6. **Optional — delete any cached auto-storage key reference.**

   Once `authenticationMode` is `BatchAccountManagedIdentity`, the cached
   key is unused. No explicit "delete cached key" command is needed; the
   PATCH in step 3 stops Batch from referring to it.

## Risks

- **RBAC propagation lag.** Role assignments can take minutes to become
  effective. Don't immediately delete the old shared-key auth path if you
  can avoid it; verify the MI path works first.
- **Pool template assumptions.** If any existing pool template or task
  definition explicitly references a SAS URL signed by the old key
  (separate from auto-storage), this migration won't fix those. Audit
  the codebase for hand-built SAS URLs in `pipeline/azure_pipeline_util.py`
  and `pipeline/batch_amp.py` — those may need their own conversion to MI
  or AAD-based SAS (`generate_user_delegation_sas`).
- **Same identity for user-subscription pool VMs?** The existing SP
  (`e4fccc0f-...`) authenticates the *pool VM creation* path. The Batch
  account MI is separate and only handles the auto-storage link. Don't
  conflate them; both can coexist.

## When to do this

- Not during a credential rotation (mid-flight risk).
- After the public-push of `aledb` settles.
- Before the next planned storage-key rotation — that's when the cost of
  not doing this would otherwise resurface.

## Cross-references

- [../rotation_runbook.md](../rotation_runbook.md) step 1g — the immediate
  re-sync workaround that this migration eliminates.
- [data_disk_migration.md](data_disk_migration.md) — sibling "structural
  cleanup" task discovered during the same rotation.
- [audit_summary.md](audit_summary.md) — the parent audit; this is
  one of its "structural follow-ups."
