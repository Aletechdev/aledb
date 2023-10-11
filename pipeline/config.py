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

# import "config.py" in "batch_amp.py"

# Update the Batch and Storage account credential strings below with the values
# unique to your accounts. These are used when constructing connection strings
# for the Batch and Storage client objects.

BATCH_ACCOUNT_NAME = 'ale'
BATCH_ACCOUNT_KEY = 'jLEiVFyapGeUOZS33cO58nntQPsk5LYZ/PMAjgZzyZXqaf9fdEuGgYImrKuQ7AdAqmjnih7Y/Hbnu5AdiOYJsw=='
BATCH_ACCOUNT_URL = 'https://ale.northeurope.batch.azure.com'
STORAGE_ACCOUNT_NAME = 'aledata'
STORAGE_ACCOUNT_DOMAIN = 'blob.core.windows.net'
STORAGE_ACCOUNT_KEY = 'peP/fMYaBPMd3U5Bq1n+Xam2QjlKKPOOf1gb8na2h86EsyDYIthSYTRUJtDKBRbTeFx+qyq1Q5RXUWE2a5hB7A=='
POOL_ID = 'ALEDBAMPool_'
DEDICATED_POOL_NODE_COUNT_LIMIT = 1000
JOB_ID = 'ALEDBAMPJoB_'
VIRTUAL_MACHINE_ID = "/subscriptions/aee8556f-d2fd-4efd-a6bd-f341a90fa76e/resourceGroups/rg-ALEdb/providers/Microsoft.Compute/galleries/ensembleamp/images/eAMP/versions/2.5.6"
NODE_AGENT_SKU_ID = "batch.node.ubuntu 18.04"

AMP_IMAGE_FILE = "https://aledata.blob.core.windows.net/images/amp.tar"
AMP_IMAGE_CONTAINER_NAME = 'images'
INPUT_CONTAINER_NAME = "data"
OUTPUT_CONTAINER_NAME = "output"
REFERENCE_CONTAINER_NAME = "reference"


TENANT_ID = "f251f123-c9ce-448e-9277-34bb285911d9"
RESOURCE = "https://batch.core.windows.net/"
CLIENT_ID = "e4fccc0f-8557-4534-82cd-bffe18ff2de9"
SECRET = "-~.wq0P4YRSCQwq7-IW1X5W3Ns3xMp9IGX"

# for actual use. edit as necessary
VM_SIZE_PROGRESSION = [('Dv2', 1), ('Dv2', 2), ('Dv2', 3)]

# more memory and storage progression
EDSV4_SERIES_PROGRESSION = [('Edsv4', 2), ('Edsv4', 4)]

# for gauging the smallest storage size that can run a sample. Not necessarily the cheapest.
# storage gb progression: 50, 75, 100, 150, 200, 300
FINE_PROGRESSION = [('Dv2', 1), ('Edsv4', 2), ('Dv2', 2), ('Edsv4', 4), ('Dv2', 3), ('Edsv4', 8)]
ESTIMATE_FINAL_COST_ADJUSTMENT = 1.3  # depends on the VM but a decent estimate
SERIES_INFO = {'Dv2':   {'minimum_cores': 1, 'cost_per_core': 0.0658, 'naming_schema': 'Standard_D{}_v2', 'naming_progression': 'linear'},
               'Dv3':   {'minimum_cores': 2, 'cost_per_core': 0.0535, 'naming_schema': 'Standard_D{}_v3', 'naming_progression': 'cores'},
               'Dv4':   {'minimum_cores': 2, 'cost_per_core': 0.063, 'naming_schema': 'Standard_D{}_v4', 'naming_progression': 'cores'},
               'Edsv4': {'minimum_cores': 2, 'cost_per_core': 0.08, 'naming_schema': 'Standard_E{}ds_v4', 'naming_progression': 'cores'},
               'H':     {'minimum_cores': 8, 'cost_per_core': 0.121375, 'naming_schema': 'Standard_H{}', 'naming_progression': 'cores'}}
