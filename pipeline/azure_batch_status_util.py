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


def get_active_batches():
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


def get_pool(pool_name):
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

    pool = batch_client.pool.get(pool_name)
    return pool


def get_job(job_name):
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

    job = batch_client.job.get(job_name)
    return job


def get_task_list(job_name):
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
    tasks = batch_client.task.list(job_id=job_name)
    return tasks


def get_log_file(job, task):
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
    current_task = batch_client.task.get(job_id=job,task_id=task)
    if current_task.state.value == "running":
        batch_client.file.get_from_task(job_id=job, task_id=task, file_path="../stdout.txt")

    if "upload" in current_task.state.value:
        batch_client.file.get_from_task(job_id=job, task_id=task, file_path="../stdout.txt")
