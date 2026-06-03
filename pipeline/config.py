# -------------------------------------------------------------------------
#
# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
# ----------------------------------------------------------------------------------
# The example companies, organizations, products, domain names,
# e-mail addresses, logos, people, places, and events depicted
# herein are fictitious. No association with any real company,
# organization, product, domain name, email address, logo, person,
# places, or events is intended or should be inferred.
# --------------------------------------------------------------------------

# Global constant variables (Azure Storage account/Batch details)
#
# Required environment variables (set in .docker/one.env for the web container):
#   Credentials (must stay out of source control):
#     AZURE_BATCH_ACCOUNT_KEY    — Azure Batch shared key
#     AZURE_STORAGE_ACCOUNT_KEY  — Azure Storage account key
#     AZURE_CLIENT_SECRET        — service-principal password
#   Tenant-identifying resource references:
#     AZURE_BATCH_ACCOUNT_NAME   — e.g. "ale"
#     AZURE_BATCH_ACCOUNT_URL    — e.g. "https://ale.northeurope.batch.azure.com"
#     AZURE_STORAGE_ACCOUNT_NAME — e.g. "aledata"
#     AZURE_TENANT_ID            — Azure AD tenant GUID
#     AZURE_CLIENT_ID            — service-principal app registration GUID
#     AZURE_VIRTUAL_MACHINE_ID   — full resource path of the Batch node VM image
# Missing any of these will raise KeyError at import — intentional, fail loud.

import os

BATCH_ACCOUNT_NAME = os.environ["AZURE_BATCH_ACCOUNT_NAME"]
BATCH_ACCOUNT_KEY = os.environ["AZURE_BATCH_ACCOUNT_KEY"]
BATCH_ACCOUNT_URL = os.environ["AZURE_BATCH_ACCOUNT_URL"]
STORAGE_ACCOUNT_NAME = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
STORAGE_ACCOUNT_DOMAIN = 'blob.core.windows.net'
STORAGE_ACCOUNT_KEY = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
POOL_ID = 'ALEDBAMPool_'
DEDICATED_POOL_NODE_COUNT_LIMIT = 1000
JOB_ID = 'ALEDBAMPJoB_'
VIRTUAL_MACHINE_ID = os.environ["AZURE_VIRTUAL_MACHINE_ID"]
NODE_AGENT_SKU_ID = "batch.node.ubuntu 24.04"

AMP_IMAGE_CONTAINER_NAME = 'images'
AMP_IMAGE_FILE = f"https://{STORAGE_ACCOUNT_NAME}.{STORAGE_ACCOUNT_DOMAIN}/{AMP_IMAGE_CONTAINER_NAME}/amp.tar"
INPUT_CONTAINER_NAME = "data"
OUTPUT_CONTAINER_NAME = "output"
REFERENCE_CONTAINER_NAME = "reference"

TENANT_ID = os.environ["AZURE_TENANT_ID"]
RESOURCE = "https://batch.core.windows.net/"
CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
SECRET = os.environ["AZURE_CLIENT_SECRET"]

# for actual use. edit as necessary
VM_SIZE_PROGRESSION = [('Dv2', 1), ('Dv2', 2), ('Dv2', 3)]

# more memory and storage progression
EDSV4_SERIES_PROGRESSION = [('Edsv4', 2), ('Edsv4', 4)]

# for gauging the smallest storage size that can run a sample. Not necessarily the cheapest.
# storage gb progression: 50, 75, 100, 150, 200, 300
FINE_PROGRESSION = [('Dv2', 1), ('Edsv4', 2), ('Dv2', 2), ('Edsv4', 4), ('Dv2', 3), ('Edsv4', 8)]
ESTIMATE_FINAL_COST_ADJUSTMENT = 1.3  # depends on the VM but a decent estimate
SERIES_INFO = {'Dv2': {'minimum_cores': 1, 'cost_per_core': 0.0658, 'naming_schema': 'Standard_D{}_v2',
                       'naming_progression': 'linear'},
               'Dv3': {'minimum_cores': 2, 'cost_per_core': 0.0535, 'naming_schema': 'Standard_D{}_v3',
                       'naming_progression': 'cores'},
               'Dv4': {'minimum_cores': 2, 'cost_per_core': 0.063, 'naming_schema': 'Standard_D{}_v4',
                       'naming_progression': 'cores'},
               'Edsv4': {'minimum_cores': 2, 'cost_per_core': 0.08, 'naming_schema': 'Standard_E{}ds_v4',
                         'naming_progression': 'cores'},
               'H': {'minimum_cores': 8, 'cost_per_core': 0.121375, 'naming_schema': 'Standard_H{}',
                     'naming_progression': 'cores'}}
