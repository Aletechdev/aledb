import re
import io
import datetime
from io import StringIO
import os
import sys
import time
import csv

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_container_sas,
    generate_blob_sas, BlobProperties
)
from azure.batch import BatchServiceClient
from azure.batch.batch_auth import SharedKeyCredentials
import azure.batch.models as batchmodels
from azure.core.exceptions import ResourceExistsError
from msrestazure.azure_active_directory import ServicePrincipalCredentials

import pipeline.config as config

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
                                             blob_prefix=file))

    return input_dict


def create_pool(
        batch_client: BatchServiceClient,
        pool_id: str,
        vm_size: str,
        vm_count: int):
    pool = batchmodels.PoolAddParameter(
        id=pool_id,
        virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
            image_reference=batchmodels.ImageReference(virtual_machine_image_id=config.VIRTUAL_MACHINE_ID),
            node_agent_sku_id=config.NODE_AGENT_SKU_ID),
        vm_size=vm_size,
        enable_auto_scale=True,
        auto_scale_formula='startingNumberOfVMs = {};maxNumberofVMs = {}; pendingTaskSamplePercent = $PendingTasks.GetSamplePercent(180 * TimeInterval_Second);pendingTaskSamples = pendingTaskSamplePercent < 70 ? startingNumberOfVMs : avg($PendingTasks.GetSample(180 *TimeInterval_Second)); $TargetDedicatedNodes=min(maxNumberofVMs, pendingTaskSamples); $NodeDeallocationOption= taskcompletion;'.format(
            vm_count, vm_count),
        auto_scale_evaluation_interval=datetime.timedelta(minutes=5),
        start_task=batchmodels.StartTask(
            command_line="/bin/bash -c \"time /root/startup.sh\"",
            resource_files=[batchmodels.ResourceFile(auto_storage_container_name=config.AMP_IMAGE_CONTAINER_NAME,
                                                     blob_prefix='amp.tar')],
            wait_for_success=True,
            max_task_retry_count=3,
            user_identity=batchmodels.UserIdentity(
                auto_user=batchmodels.AutoUserSpecification(
                    scope=batchmodels.AutoUserScope.pool,
                    elevation_level=batchmodels.ElevationLevel.admin)),

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


def create_job(
        batch_client: BatchServiceClient,
        job_id: str,
        pool_id: str):
    job = batchmodels.JobAddParameter(
        id=job_id,
        pool_info=batchmodels.PoolInformation(pool_id=pool_id))

    batch_client.job.add(job)


def build_sas_url(
        blob_service_client: BlobServiceClient,
        container_name: str,
        sas_token: str
) -> str:
    """Builds a signed URL for a blob

    :param blob_service_client: The blob service client
    :param container_name: The name of the blob container
    :param blob_name: The name of the blob
    :param sas_token: An SAS token
    """
    base_url = str(blob_service_client.url)
    if not base_url.endswith("/"):
        base_url += "/"

    return f"{base_url}{container_name}?{sas_token}"


def run_pipeline(directory, run_name):
    batch_account_key = config.BATCH_ACCOUNT_KEY
    batch_account_name = config.BATCH_ACCOUNT_NAME
    batch_service_url = config.BATCH_ACCOUNT_URL

    blob_service_client = BlobServiceClient(
        account_url=f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/",
        credential=config.STORAGE_ACCOUNT_KEY
    )

    credentials = ServicePrincipalCredentials(
        client_id=config.CLIENT_ID,
        secret=config.SECRET,
        tenant=config.TENANT_ID,
        resource=config.RESOURCE
    )

    batch_client = BatchServiceClient(
        credentials,
        batch_url=batch_service_url)
    samples = get_pipeline_inputs_from_directory(directory=directory).items()
    # get the number of samples to run

    create_pool(batch_client=batch_client, pool_id=run_name, vm_count=len(samples), vm_size="STANDARD_E2ds_V4")

    create_job(batch_client=batch_client, job_id=run_name,
               pool_id=run_name)

    print('Adding {} tasks to job [{}]...'.format(len(samples), run_name))

    tasks = list()

    output_container_sas_url = build_sas_url(
        blob_service_client,
        container_name=config.OUTPUT_CONTAINER_NAME,
        sas_token=generate_container_sas(account_name=blob_service_client.account_name,
                                         account_key=config.STORAGE_ACCOUNT_KEY,
                                         container_name=config.OUTPUT_CONTAINER_NAME,
                                         permission=BlobSasPermissions.from_string('rw'),
                                         expiry=datetime.datetime.utcnow() + datetime.timedelta(
                                             days=7)))

    for csv_key, input_files in samples:
        sample_name = re.sub('[^a-zA-Z0-9\n\\+\.]', '-',
                             csv_key.split("/")[-1].replace(".csv", "").replace("+", "-"))

        output_file_path = '{}/alemutpipe-outputs/{}.tar.gz'.format(directory, sample_name)
        command = "/bin/bash -c \"sudo docker run -v $AZ_BATCH_TASK_WORKING_DIR/{}:/var/data -t --name amp{} " \
                  "aletechdev/amp bash -i -c \\\"source /root/.bashrc && time /amp.sh\\\" && mv " \
                  "$AZ_BATCH_TASK_WORKING_DIR/{}/alemutpipe-outputs/*.tar.gz " \
                  "$AZ_BATCH_TASK_WORKING_DIR/{}/alemutpipe-outputs/{}.tar.gz\"".format(directory, sample_name,
                                                                                        directory,
                                                                                        directory, sample_name)
        tasks.append(batchmodels.TaskAddParameter(
            id=sample_name,
            user_identity=batchmodels.UserIdentity(
                auto_user=batchmodels.AutoUserSpecification(
                    scope=batchmodels.AutoUserScope.pool,
                    elevation_level=batchmodels.ElevationLevel.admin)),
            command_line=command,
            resource_files=input_files,
            output_files=[batchmodels.OutputFile(
                file_pattern=output_file_path,
                destination=batchmodels.OutputFileDestination(
                    container=batchmodels.OutputFileBlobContainerDestination(
                        path='{}/{}.tar.gz'.format(run_name, sample_name),
                        container_url=output_container_sas_url)),
                upload_options=batchmodels.OutputFileUploadOptions(
                    upload_condition=batchmodels.OutputFileUploadCondition.task_completion)),
                batchmodels.OutputFile(
                    file_pattern="../stdout.txt",
                    destination=batchmodels.OutputFileDestination(
                        container=batchmodels.OutputFileBlobContainerDestination(
                            path="{}/{}_out.txt".format(run_name, sample_name),
                            container_url=output_container_sas_url)),
                    upload_options=batchmodels.OutputFileUploadOptions(
                        upload_condition=batchmodels.OutputFileUploadCondition.task_completion)),
            ]
        )
        )

    batch_client.task.add_collection(run_name, tasks)


if __name__ == '__main__':
    run_pipeline('project_D_new_reference', 'testing_aledbamp_6')
