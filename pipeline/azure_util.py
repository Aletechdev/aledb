import datetime
import io
from io import StringIO
import os
import sys
import time
import csv

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas, BlobProperties
)
from azure.batch import BatchServiceClient
from azure.batch.batch_auth import SharedKeyCredentials
import azure.batch.models as batchmodels
from azure.core.exceptions import ResourceExistsError

import config

DEFAULT_ENCODING = "utf-8"


def get_directory_contents(directory, blob_service_client):
    return blob_service_client.get_container_client(container=config.INPUT_CONTAINER_NAME).list_blobs(
        name_starts_with=directory)


def get_input_directories():
    blob_service_client = BlobServiceClient(
        account_url=f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/",
        credential=config.STORAGE_ACCOUNT_KEY
    )
    return blob_service_client.get_container_client(container=config.INPUT_CONTAINER_NAME).walk_blobs(delimiter='/')


def get_output_directories():
    blob_service_client = BlobServiceClient(
        account_url=f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/",
        credential=config.STORAGE_ACCOUNT_KEY
    )
    return blob_service_client.get_container_client(container=config.INPUT_CONTAINER_NAME).walk_blobs(delimiter='/')


# input blob csv file
def get_pipeline_input_filenames_from_blob(csv_blob: BlobProperties, blob_service_client):
    container = blob_service_client.get_container_client(container=csv_blob.container)
    reader = csv.reader(StringIO(container.download_blob(blob=csv_blob).readall().decode()))
    run_details = {rows[0]: rows[1] for rows in reader}
    read_file_list = run_details['additional read files'].split(",")
    read_file_list.append(run_details['filename'])
    read_file_list.append(run_details['filename2'])
    reference_file_list = run_details['reference file name(s)'].split(",")

    return {'read_files': read_file_list, 'reference_files': reference_file_list}


# input directory spit out dictionary of pipeline inputs from the data folder
def get_pipeline_inputs_from_directory(directory):
    blob_service_client = BlobServiceClient(
        account_url=f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/",
        credential=config.STORAGE_ACCOUNT_KEY
    )
    input_dict = {}

    for blob in get_directory_contents(directory, blob_service_client):
        blob_name = str(blob.name)
        if blob_name.endswith('.csv'):
            input_dict[blob_name] = [batchmodels.ResourceFile(auto_storage_container_name=config.INPUT_CONTAINER_NAME,
                                                              blob_prefix=blob_name)]
            name_dict = get_pipeline_input_filenames_from_blob(blob, blob_service_client)
            for file in name_dict['read_files']:
                input_dict[blob_name].append(
                    batchmodels.ResourceFile(auto_storage_container_name=config.INPUT_CONTAINER_NAME,
                                             blob_prefix=directory + '/' + file))
            for file in name_dict['reference_files']:
                input_dict[blob_name].append(
                    batchmodels.ResourceFile(auto_storage_container_name=config.REFERENCE_CONTAINER_NAME,
                                             blob_prefix=directory + '/' + file))

    return input_dict


def create_pool(
        batch_client: BatchServiceClient,
        pool_id: str,
        vm_size: str,
        vm_count: int):
    pool = batchmodels.PoolAddParameter(
        id=pool_id,
        virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
            image_reference=config.VIRTUAL_MACHINE_ID,
            node_agent_sku_id=config.NODE_AGENT_SKU_ID),
        vm_size=vm_size,
        target_dedicated_nodes=vm_count,
        start_task=batchmodels.StartTask(
            command_line="/bin/bash -c \"time /root/startup.sh\"",
            resource_files=[batchmodels.ResourceFile(auto_storage_container_name=config.AMP_IMAGE_CONTAINER_NAME,
                                                     blob_prefix='amp.tar')],
            wait_for_success=True,
            max_task_retry_count=3,
        )
    )
    try:
        print("Attempting to create pool:", pool.id)
        batch_client.pool.add(pool)
        print("Created pool:", pool.id)
    except batchmodels.BatchErrorException as err:
        if err.error.code != "PoolExists":
            raise
        else:
            print(f"Pool {pool.id!r} already exists")

'''
def submit_job_and_add_task(
        batch_client: BatchServiceClient,
        blob_service_client: BlobServiceClient,
        job_id: str,
        pool_id: str):
    """Submits a job to the Azure Batch service and adds
    a task that runs a python script.

    :param batch_client: The batch client to use.
    :param blob_service_client: The storage block blob client to use.
    :param job_id: The id of the job to create.
    :param pool_id: The id of the pool to use.
    """
    job = batchmodels.JobAddParameter(
        id=job_id,
        pool_info=batchmodels.PoolInformation(pool_id=pool_id))

    batch_client.job.add(job)

    try:
        blob_service_client.create_container(_CONTAINER_NAME)
    except ResourceExistsError:
        pass

    sas_url = common.helpers.upload_blob_and_create_sas(
        blob_service_client,
        _CONTAINER_NAME,
        _SIMPLE_TASK_NAME,
        _SIMPLE_TASK_PATH,
        datetime.datetime.utcnow() + datetime.timedelta(hours=1))

    task = batchmodels.TaskAddParameter(
        id="MyPythonTask",
        command_line="python " + _SIMPLE_TASK_NAME,
        resource_files=[batchmodels.ResourceFile(
            file_path=_SIMPLE_TASK_NAME,
            http_url=sas_url)])

    batch_client.task.add(job_id=job.id, task=task)
'''

def run_pipeline(directory):
    batch_account_key = config.BATCH_ACCOUNT_KEY
    batch_account_name = config.BATCH_ACCOUNT_NAME
    batch_service_url = config.BATCH_ACCOUNT_URL

    credentials = SharedKeyCredentials(
        batch_account_name,
        batch_account_key)

    batch_client = BatchServiceClient(
        credentials,
        batch_url=batch_service_url)

    # Retry 5 times -- default is 3
    #batch_client.config.retry_policy.retries = 5
    create_pool(batch_client=batch_client, pool_id=directory, vm_count=1, vm_size="STANDARD_E2ds_V4")


if __name__ == '__main__':
    run_pipeline('project_D_new_reference')
