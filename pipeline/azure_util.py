
import datetime
import io
import os
import sys
import time

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas
)
from azure.batch import BatchServiceClient
from azure.batch.batch_auth import SharedKeyCredentials
import azure.batch.models as batchmodels
from azure.core.exceptions import ResourceExistsError

import config

DEFAULT_ENCODING = "utf-8"

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


if __name__ == '__main__':
    for blob in get_input_directories():
        print(blob)

