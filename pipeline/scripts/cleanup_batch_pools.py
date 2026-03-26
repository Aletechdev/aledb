"""
Delete idle Azure Batch pools (0 dedicated nodes).
Run inside the aledb-web container:
    sudo docker exec aledb-web python3 pipeline/scripts/cleanup_batch_pools.py [--dry-run]

Output data in Azure Storage is NOT affected by deleting pools.
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

pools = list(batch_client.pool.list())
keep = []
delete = []

for p in pools:
    if p.current_dedicated_nodes > 0:
        keep.append(p)
    else:
        delete.append(p)

print(f'Total pools: {len(pools)}')
print(f'\nWould KEEP ({len(keep)}):')
for p in keep:
    print(f'  {p.id} ({p.current_dedicated_nodes} VMs active)')

print(f'\nWould DELETE ({len(delete)}):')
for p in delete:
    print(f'  {p.id}')

if dry_run:
    print('\n[DRY RUN] No pools deleted.')
else:
    confirm = input(f'\nDelete {len(delete)} pools? (yes/no): ')
    if confirm == 'yes':
        for p in delete:
            print(f'Deleting: {p.id}')
            batch_client.pool.delete(p.id)
        print(f'\nDeleted {len(delete)} pools.')
    else:
        print('Aborted.')
