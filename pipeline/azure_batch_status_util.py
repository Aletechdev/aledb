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


def get_active_batches(batch_client: BatchServiceClient):
    batch_account_key = config.BATCH_ACCOUNT_KEY
    batch_account_name = config.BATCH_ACCOUNT_NAME
    batch_service_url = config.BATCH_ACCOUNT_URL
    credentials = ServicePrincipalCredentials(
        client_id=config.CLIENT_ID,
        secret=config.SECRET,
        tenant=config.TENANT_ID,
        resource=config.RESOURCE
    )

    batch_client = BatchServiceClient(
        credentials,
        batch_url=batch_service_url)

    pool_list = batch_client.pool.list()
    return pool_list


def get_task_output(node_id):
    return
