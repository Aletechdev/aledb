import gzip
import json
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


def get_shared_directories():
    lsjson_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'muyao@aledb.org', 'rclone', 'lsjson', '--dirs-only',
                  '--drive-shared-with-me', 'ALE:']
    lsjson_out = json.loads(subprocess.check_output(lsjson_cmd).decode("utf-8"))
    return lsjson_out


def get_files_from_directory(dir):
    ls_json_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'muyao@aledb.org', 'rclone', 'lsjson', '--dirs-only',
                   '--drive-shared-with-me', 'ALE:']


def transfer_to_azure(shared_drive_name):
    root_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'muyao@aledb.org']

    create_folder_cmd = ['sudo', 'mkdir', f'/pipeline_inputs/{shared_drive_name}']
    subprocess.run(root_cmd + create_folder_cmd)
    copy_files_cmd = ['rclone', 'copy', '--drive-shared-with-me', f"ALE:{shared_drive_name}", f"/pipeline_inputs/{shared_drive_name}"]
    subprocess.run(root_cmd + copy_files_cmd)


#will use the external rclone command to do so
def transfer_to_azure_mounted(dir):
    #code for the files in a mounted system
    blob_service_client = BlobServiceClient(
        account_url=f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/",
        credential=config.STORAGE_ACCOUNT_KEY
    )

    for path, subdirs, files in os.walk(dir):
        for name in files:
            fullPath = os.path.join(path, name)
            print("FullPath : " + fullPath)
            file = fullPath.replace(dir, '')
            fileName = file[1:len(file)];
            print("File Name :" + fileName)

            print("\nUploading to Azure Storage as blob:\n\t" + fileName)
            blob_service_client.get_container_client(container="data").upload_blob(fileName, open(fullPath, "rb"))
