"""
Stop a specific Azure Batch run by deleting its job and pool.
Run inside the aledb-web container:
    sudo docker exec aledb-web python3 pipeline/scripts/stop_batch_run.py <run_name>

Example:
    sudo docker exec aledb-web python3 pipeline/scripts/stop_batch_run.py SWRhodo_debug
"""
import sys
from azure.batch import BatchServiceClient
from azure.batch.models import BatchErrorException
from msrestazure.azure_active_directory import ServicePrincipalCredentials
import pipeline.config as config

if len(sys.argv) < 2:
    print('Usage: python3 pipeline/scripts/stop_batch_run.py <run_name>')
    sys.exit(1)

run_name = sys.argv[1]

credentials = ServicePrincipalCredentials(
    client_id=config.CLIENT_ID,
    secret=config.SECRET,
    tenant=config.TENANT_ID,
    resource=config.RESOURCE
)
batch_client = BatchServiceClient(credentials, batch_url=config.BATCH_ACCOUNT_URL)

# Dry-run: show what will be affected
print(f'Looking up run: {run_name}\n')

found_pool = None
found_job = None

try:
    pool = batch_client.pool.get(run_name)
    found_pool = pool
    print(f'Pool: {pool.id}')
    print(f'  State: {pool.state}')
    print(f'  VMs: {pool.current_dedicated_nodes}/{pool.target_dedicated_nodes}')
except BatchErrorException:
    print(f'Pool: {run_name} - not found')

try:
    job = batch_client.job.get(run_name)
    found_job = job
    tasks = list(batch_client.task.list(run_name))
    running = sum(1 for t in tasks if t.state.value == 'running')
    completed = sum(1 for t in tasks if t.state.value == 'completed')
    print(f'Job: {job.id}')
    print(f'  State: {job.state.value}')
    print(f'  Tasks: {len(tasks)} total, {running} running, {completed} completed')
except BatchErrorException:
    print(f'Job: {run_name} - not found')

if not found_pool and not found_job:
    print(f'\nNothing found for "{run_name}".')
    sys.exit(0)

print()
confirm = input('Delete this job and pool? (yes/no): ')
if confirm == 'yes':
    if found_job:
        print(f'Deleting job: {run_name}')
        batch_client.job.delete(run_name)
    if found_pool:
        print(f'Deleting pool: {run_name}')
        batch_client.pool.delete(run_name)
    print('Done.')
else:
    print('Aborted.')
