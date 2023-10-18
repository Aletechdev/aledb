import gzip
import shutil

import subprocess
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


# the lazy/existing way to run it all for now. does not work cus i dont have azcopy set up in the containter
def run_upload_script(directory):
    subprocess.Popen(['sh', './upload.sh'], cwd='/app/pipeline/transfer')


def get_output_directory_names():
    blob_service_client = BlobServiceClient(
        account_url=f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/",
        credential=config.STORAGE_ACCOUNT_KEY
    )
    available_folders = blob_service_client.get_container_client(container=config.OUTPUT_CONTAINER_NAME).walk_blobs(
        delimiter='/')
    output_directory_names = []
    for folder in available_folders:
        output_directory_names.append(folder.name.replace('/', ''))

    return output_directory_names


def get_out_directory_contents(directory, blob_service_client):
    return blob_service_client.get_container_client(container=config.OUTPUT_CONTAINER_NAME).list_blobs(
        name_starts_with=directory)


def download_blobs_from_folder(directory):
    blob_service_client = BlobServiceClient(
        account_url=f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/",
        credential=config.STORAGE_ACCOUNT_KEY
    )
    # step one download all blobs to a folder
    transfer_loc = '/app/pipeline/transfer/'
    os.makedirs(transfer_loc + directory)
    for blob in get_out_directory_contents(directory, blob_service_client):
        print("debugging" + blob.name)
        with open(file=os.path.join(transfer_loc, blob.name), mode="wb") as file:
            file.write(
                blob_service_client.get_container_client(container=blob.container).download_blob(blob=blob).readall())


def upload_batch_job(directory):
    download_blobs_from_folder(directory)

    with gzip.open('file.txt.gz', 'rb') as f_in:
        with open('file.txt', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
