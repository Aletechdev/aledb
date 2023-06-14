from __future__ import print_function
import datetime
import re
import csv
import os
import sys
import time
from pipeline import config

from collections import OrderedDict

try:
    input = raw_input
except NameError:
    pass

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas
)
from azure.batch import BatchServiceClient
from azure.batch.batch_auth import SharedKeyCredentials
import azure.batch.models as batchmodels
from azure.core.exceptions import ResourceExistsError

from pipeline import node_control

DEFAULT_ENCODING = "utf-8"

sys.path.append('.')
sys.path.append('..')

# Update the Batch and Storage account credential strings in config.py with values
# unique to your accounts. These are used when constructing connection strings
# for the Batch and Storage client objects.


def query_yes_no(question: str, default: str = "yes") -> str:
    """
    Prompts the user for yes/no input, displaying the specified question text.

    :param str question: The text of the prompt for input.
    :param str default: The default if the user hits <ENTER>. Acceptable values
    are 'yes', 'no', and None.
    :return: 'yes' or 'no'
    """
    valid = {'y': 'yes', 'n': 'no'}
    if default is None:
        prompt = ' [y/n] '
    elif default == 'yes':
        prompt = ' [Y/n] '
    elif default == 'no':
        prompt = ' [y/N] '
    else:
        raise ValueError(f"Invalid default answer: '{default}'")

    choice = default

    while 1:
        user_input = input(question + prompt).lower()
        if not user_input:
            break
        try:
            choice = valid[user_input[0]]
            break
        except (KeyError, IndexError):
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

    return choice


def print_batch_exception(batch_exception: batchmodels.BatchErrorException):
    """
    Prints the contents of the specified Batch exception.

    :param batch_exception:
    """
    print('-------------------------------------------')
    print('Exception encountered:')
    if batch_exception.error and \
            batch_exception.error.message and \
            batch_exception.error.message.value:
        print(batch_exception.error.message.value)
        if batch_exception.error.values:
            print()
            for mesg in batch_exception.error.values:
                print(f'{mesg.key}:\t{mesg.value}')
    print('-------------------------------------------')


def check_pool_control_status(batch_service_client):
    for pool in batch_service_client.pool.list():
        if pool.allocation_state == 'steady':
            nodes = node_control.get_list_of_active_nodes(batch_service_client, pool.id)
            if len(nodes) == 0:
                print("Warning: Active pools detected. Pool control may be offline. Please")


def get_sample_files(csv_path):
    with open(csv_path, encoding="utf8") as metadata_file:
        csv_reader = csv.reader(metadata_file)
        all_file_list = [csv_path]
        for row in csv_reader:
            if row[0] == "filename":
                all_file_list.append(row[1])
            elif row[0] == "filename2":
                if row[1] != "":
                    all_file_list.append(row[1])
            elif row[0] == "additional read files":
                if row[1] != "":
                    all_file_list += (row[1].split(","))
            elif row[0] == 'reference file name(s)':
                if row[1] != "":
                    all_file_list += (row[1].split(","))

        res = list(OrderedDict.fromkeys(all_file_list))
        return res


def get_inputs(block_blob_client, container_name, file_path, file_names):
    """
    Uploads a local file to an Azure Blob storage container.

    :param block_blob_client: A blob service client.
    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str container_name: The name of the Azure Blob storage container.
    :param str file_names: The name of the files
    :rtype: `azure.batch.models.ResourceFile`
    :return: A ResourceFile initialized with a SAS URL appropriate for Batch
    tasks.
    """
    inputs = []
    # Obtain the SAS token for the container.
    sas_token = get_container_sas_token(block_blob_client,
                                        container_name, azureblob.BlobPermissions.READ)
    for file_name in file_names:
        if file_path is not '':
            blob_name = file_path + '/' + os.path.basename(file_name)
        else:
            blob_name = os.path.basename(file_name)

        sas_url = block_blob_client.make_blob_url(container_name,
                                                  blob_name,
                                                  sas_token=sas_token).replace(' ', '%20')
        inputs.append(batchmodels.ResourceFile(file_path=blob_name, http_url=sas_url))
    return [file_names[0], inputs]


def get_container_sas_token(block_blob_client,
                            container_name, blob_permissions):
    """
    Obtains a shared access signature granting the specified permissions to the
    container.

    :param block_blob_client: A blob service client.
    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str container_name: The name of the Azure Blob storage container.
    :param BlobPermissions blob_permissions:
    :rtype: str
    :return: A SAS token granting the specified permissions to the container.
    """
    # Obtain the SAS token for the container, setting the expiry time and
    # permissions. In this case, no start time is specified, so the shared
    # access signature becomes valid immediately. Expiration is in 2 hours.
    container_sas_token = \
        block_blob_client.generate_container_shared_access_signature(
            container_name,
            permission=blob_permissions,
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=169))

    return container_sas_token


def get_container_sas_url(block_blob_client,
                          container_name, blob_permissions):
    """
    Obtains a shared access signature URL that provides write access to the
    ouput container to which the tasks will upload their output.

    :param block_blob_client: A blob service client.
    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str container_name: The name of the Azure Blob storage container.
    :param BlobPermissions blob_permissions:
    :rtype: str
    :return: A SAS URL granting the specified permissions to the container.
    """
    # Obtain the SAS token for the container.
    sas_token = get_container_sas_token(block_blob_client,
                                        container_name, azureblob.BlobPermissions.WRITE)

    # Construct SAS URL for the container
    container_sas_url = "https://{}.blob.core.windows.net/{}?{}".format(
        config._STORAGE_ACCOUNT_NAME, container_name, sas_token)

    return container_sas_url


def create_pool(batch_service_client, pool_id, num_dedicated_nodes, blob_client, vm_size):
    """
    Creates a pool of compute nodes with the specified OS settings.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str pool_id: An ID for the new pool.
    :param str publisher: Marketplace image publisher
    :param str offer: Marketplace image offer
    :param str sku: Marketplace image sky
    """
    print('Creating pool [{}]...'.format(pool_id))

    # Create a new pool of Linux compute nodes using an Azure Virtual Machines
    # Marketplace image. For more information about creating pools of Linux
    # nodes, see:
    # https://azure.microsoft.com/documentation/articles/batch-linux-nodes/

    # The start task installs ffmpeg on each node from an available repository, using
    # an administrator user identity.

    input_container_name = 'images'

    new_pool = batch.models.PoolAddParameter(
        id=pool_id,
        virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
            image_reference=batchmodels.ImageReference(
                virtual_machine_image_id=config._VIRTUAL_MACHINE_ID
            ),
            node_agent_sku_id=config._NODE_AGENT_SKU_ID),
        vm_size=vm_size,
        enable_auto_scale=False,
        # commenting out to allow for deletion of unusable nodes. auto_scale_formula='startingNumberOfVMs = {};
        # maxNumberofVMs = {}; pendingTaskSamplePercent = $PendingTasks.GetSamplePercent(180 * TimeInterval_Second);
        # pendingTaskSamples = pendingTaskSamplePercent < 70 ? startingNumberOfVMs : avg($PendingTasks.GetSample(180 *
        # TimeInterval_Second)); $TargetDedicatedNodes=min(maxNumberofVMs, pendingTaskSamples); $NodeDeallocationOption
        # = taskcompletion;'.format(num_dedicated_nodes, num_dedicated_nodes),
        target_dedicated_nodes=num_dedicated_nodes,
        # target_low_priority_nodes=config._LOW_PRIORITY_POOL_NODE_COUNT,
        start_task=batchmodels.StartTask(
            command_line="/bin/bash -c \"time /root/startup.sh\"",
            resource_files=get_inputs(blob_client, input_container_name, '', ['amp.tar'])[1],
            wait_for_success=True,
            max_task_retry_count=3,
            user_identity=batchmodels.UserIdentity(
                auto_user=batchmodels.AutoUserSpecification(
                    scope=batchmodels.AutoUserScope.pool,
                    elevation_level=batchmodels.ElevationLevel.admin)),
        )
    )

    batch_service_client.pool.add(new_pool)


def create_job(batch_service_client, job_id, pool_id):
    """
    Creates a job with the specified ID, associated with the specified pool.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID for the job.
    :param str pool_id: The ID for the pool.
    """
    print('Creating job [{}]...'.format(job_id))

    job = batch.models.JobAddParameter(
        id=job_id,
        pool_info=batch.models.PoolInformation(pool_id=pool_id))

    batch_service_client.job.add(job)


def add_tasks(batch_service_client, job_id, input_files_collection, output_container_sas_url, input_path, output_path):
    """
    Adds a task for each input file in the collection to the specified job.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID of the job to which to add the tasks.
    :param list input_files: A collection of input files. One task will be
     created for each input file.
    :param output_container_sas_token: A SAS token granting write access to
    the specified Azure Blob storage container.
    """

    print('Adding {} tasks to job [{}]...'.format(len(input_files_collection), job_id))

    tasks = list()

    for idx, input_files in enumerate(input_files_collection):
        sample_name = re.sub('[^a-zA-Z0-9\n\\+\.]', '-', input_files[0].split("/")[-1].replace(".csv", "").replace("+", "-"))
        input_files = input_files[1]

        output_file_path = '{}/alemutpipe-outputs/{}.tar.gz'.format(input_path, idx)
        command = "/bin/bash -c \"sudo docker run -v $AZ_BATCH_TASK_WORKING_DIR/{}:/var/data -t --name amp{} " \
                  "aletechdev/amp bash -i -c \\\"source /root/.bashrc && time /amp.sh\\\" && mv " \
                  "$AZ_BATCH_TASK_WORKING_DIR/{}/alemutpipe-outputs/*.tar.gz " \
                  "$AZ_BATCH_TASK_WORKING_DIR/{}/alemutpipe-outputs/{}.tar.gz\"".format(input_path, idx, input_path, input_path, idx)

        tasks.append(batch.models.TaskAddParameter(
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
                              path='{}/{}.tar.gz'.format(output_path, sample_name),
                              container_url=output_container_sas_url)),
                upload_options=batchmodels.OutputFileUploadOptions(
                    upload_condition=batchmodels.OutputFileUploadCondition.task_completion)),
                batchmodels.OutputFile(
                    file_pattern="../stdout.txt",
                    destination=batchmodels.OutputFileDestination(
                        container=batchmodels.OutputFileBlobContainerDestination(
                            path="{}/{}_out.txt".format(output_path, sample_name),
                            container_url=output_container_sas_url)),
                    upload_options=batchmodels.OutputFileUploadOptions(
                        upload_condition=batchmodels.OutputFileUploadCondition.task_completion)),
            ]
        )
        )

    batch_service_client.task.add_collection(job_id, tasks)


if __name__ == '__main__':
    try:
        directory_name = sys.argv[1]
        print(directory_name)
    except:
        print('Error: Usage python batch_amp.py <PATH_TO_METADATA>')
        raise
    start_time = datetime.datetime.now().replace(microsecond=0)
    print('Sample start: {}'.format(start_time))
    print()

    # Create the blob client, for use in obtaining references to
    # blob storage containers and uploading files to containers.

    blob_client = azureblob.BlockBlobService(
        account_name=config._STORAGE_ACCOUNT_NAME,
        account_key=config._STORAGE_ACCOUNT_KEY)

    # Use the blob client to create the containers in Azure Storage if they
    # don't yet exist.

    input_container_name = 'data'
    output_container_name = 'output'

    input_path = input("Enter the path to your data within the " + input_container_name + " container: ").strip("/")
    print("input path set to " + input_path)
    output_path = input("Enter the desired output path within the " + output_container_name + " container: ").strip("/")

    # Create a list of all csv files in the InputFiles directory.
    input_csv_paths = []

    for folder, subs, files in os.walk(directory_name):
        for filename in files:
            if filename.endswith(".csv"):
                input_csv_paths.append(os.path.abspath(
                    os.path.join(folder, filename)))

    # Upload the input files. This is the collection of files that are to be processed by the tasks.
    input_files = [
        get_inputs(blob_client, input_container_name, input_path, get_sample_files(file_path))
        for file_path in input_csv_paths
        ]

    # Obtain a shared access signature URL that provides write access to the output
    # container to which the tasks will upload their output.

    output_container_sas_url = get_container_sas_url(
        blob_client,
        output_container_name,
        azureblob.BlobPermissions.WRITE)

    # Create a Batch service client. We'll now be interacting with the Batch
    # service in addition to Storage
    credentials = ServicePrincipalCredentials(
        client_id=config.CLIENT_ID,
        secret=config.SECRET,
        tenant=config.TENANT_ID,
        resource=config.RESOURCE
    )

    batch_client = batch.BatchServiceClient(
        credentials,
        batch_url=config._BATCH_ACCOUNT_URL)

    try:
        try:
            # Create the pool that will contain the compute nodes that will execute the
            # tasks.

            print('Generating nodes for ' + str(len(input_csv_paths)) + ' samples')
            num_samples = len(input_csv_paths)
            if num_samples < int(config._DEDICATED_POOL_NODE_COUNT_LIMIT):
                num_nodes = num_samples
            else:
                num_nodes = int(input("Number of nodes to initiate: "))

            current_vm_progression = config.EDSV4_SERIES_PROGRESSION
            for vm_size in current_vm_progression:
                vm_series_info = config.SERIES_INFO[vm_size[0]]
                if vm_series_info['naming_progression'] is 'linear':
                    num_cores = 2**(vm_size[1]-1)
                else:
                    num_cores = vm_size[1]
                vm_size_name = vm_series_info['naming_schema'].format(vm_size[1])

                print('Creating a {} pool with {} nodes, at a listed cost of ${} per node hour or '
                      'a combined listed cost of ${} per hour.\n'
                      'Real prices will be around 10-30% higher depending on the VM selected.'
                      .format(vm_size_name, num_nodes, vm_series_info['cost_per_core']*num_cores, vm_series_info['cost_per_core']*num_cores*num_nodes))
                if query_yes_no('Continue?') == 'no':
                    break
                pool_id = config._POOL_ID + output_path.replace(' ', '_') + '_' + vm_size_name
                job_id = config._JOB_ID + output_path.replace(' ', '_')

                create_pool(batch_client, pool_id, num_nodes, blob_client, vm_size_name)
                if vm_size == current_vm_progression[0]:
                    # Create the job that will run the tasks.
                    create_job(batch_client, job_id, pool_id)
                    # Add the tasks to the job. Pass the input files and a SAS URL
                    # to the storage container for output files.
                    add_tasks(batch_client, job_id,
                              input_files, output_container_sas_url, input_path, output_path)
                else:
                    print('Disabling active job')
                    batch_client.job.disable(job_id, 'requeue')
                    time.sleep(10)
                    print('Updating pool to %s' % (pool_id))
                    batch_client.job.update(job_id, job_update_parameter=batchmodels.JobUpdateParameter(
                        pool_info=batch.models.PoolInformation(pool_id=pool_id)))
                    print('Re-enabling active job')
                    batch_client.job.enable(job_id)
                # Pause execution until tasks reach Completed state.
                pool_start_time = datetime.datetime.now().replace(microsecond=0)
                print('{} start: {}'.format(pool_id, start_time))
                incomplete_tasks = node_control.wait_for_tasks_to_complete(batch_client,
                                           job_id, pool_id,
                                           datetime.timedelta(minutes=1440))
                print("Pool ended with output {}".format(incomplete_tasks))
                pool_end_time = datetime.datetime.now().replace(microsecond=0)
                print('{} end: {}'.format(pool_id, pool_end_time))
                print('Pool elapsed time: {}'.format(pool_end_time - pool_start_time))
                if incomplete_tasks:
                    num_nodes = len(incomplete_tasks)
                    print("The following {} tasks are still incomplete:".format)
                    for incomplete_task in incomplete_tasks:
                        print(incomplete_task.id)

                else:
                    break

                # end loop here
        except KeyboardInterrupt:
            print("Pipeline stopped")
            if query_yes_no('Delete job?') == 'yes':
                batch_client.job.delete(job_id)

            if query_yes_no('Delete pool?') == 'yes':
                batch_client.pool.delete(pool_id)
            raise

        print("  Success! All tasks reached the 'Completed' state within the "
              "specified timeout period.")

    except Exception as err:
        batch_client.pool.delete(pool_id)
        print_batch_exception(err)
        if query_yes_no('Delete job?') == 'yes':
            batch_client.job.delete(job_id)

    # Delete input container in storage
    print('Deleting container [{}]...'.format(input_container_name))
    #blob_client.delete_container(input_container_name)

    # Print out some timing info
    end_time = datetime.datetime.now().replace(microsecond=0)
    print()
    print('Run end: {}'.format(end_time))
    print('Total Elapsed time: {}'.format(end_time - start_time))
    print()

    # Clean up Batch resources (if the user so chooses).
    try:
        if query_yes_no('Delete job?') == 'yes':
            batch_client.job.delete(job_id)
    except:
        print("Job deletion failed")

