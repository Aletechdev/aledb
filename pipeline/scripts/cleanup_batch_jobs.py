"""
Delete orphaned Azure Batch jobs whose pools no longer exist.
Run inside the aledb-web container:
    sudo docker exec aledb-web python3 pipeline/scripts/cleanup_batch_jobs.py [--dry-run]

Output data in Azure Storage is NOT affected by deleting jobs.
"""
import sys
from azure.batch import BatchServiceClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials
import pipeline.config as config

dry_run = '--dry-run' in sys.argv

credentials = ServicePrincipalCredentials(
    client_id=config.CLIENT_ID,
    secret=config.SECRET,
    tenant=config.TENANT_ID,
    resource=config.RESOURCE
)
batch_client = BatchServiceClient(credentials, batch_url=config.BATCH_ACCOUNT_URL)

active_pools = {p.id for p in batch_client.pool.list()}
jobs = list(batch_client.job.list())
keep = []
delete = []

for j in jobs:
    if j.pool_info.pool_id in active_pools:
        keep.append(j)
    else:
        delete.append(j)

print(f'Active pools: {active_pools}')
print(f'Total jobs: {len(jobs)}')
print(f'\nWould KEEP ({len(keep)}):')
for j in keep:
    print(f'  {j.id} (state: {j.state.value}, pool: {j.pool_info.pool_id})')

print(f'\nWould DELETE ({len(delete)}):')
for j in delete:
    print(f'  {j.id} (state: {j.state.value}, pool: {j.pool_info.pool_id} - no longer exists)')

if dry_run:
    print('\n[DRY RUN] No jobs deleted.')
else:
    confirm = input(f'\nDelete {len(delete)} orphaned jobs? (yes/no): ')
    if confirm == 'yes':
        for j in delete:
            print(f'Deleting: {j.id}')
            batch_client.job.delete(j.id)
        print(f'\nDeleted {len(delete)} jobs.')
    else:
        print('Aborted.')
