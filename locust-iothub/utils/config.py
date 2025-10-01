PARAMS_SOURCE = "keyvault"   # keyvault|config

# ----------------------------------------------------------------------------------------
# --- LOCUST PARAMETERS ------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
KEY_VAULT_NAME = "<keyvaultname>"
MANAGED_IDENTITY_CLIENT_ID = "<clientid>"
STORAGE_QUEUE_NAME = "devices"
MAX_DEVICE_IDS = 7000
# --- Secret names in Key Vault ---
IOTHUB_CONNECTION_STRING_SECRET_NAME = "iothub-connection-string"
IOTHUB_HOSTNAME_SECRET_NAME = "iothub-hostname"
IOTHUB_PROXYNAME_SECRET_NAME = "iothub-proxy"
PROXY_CERTIFICATE_SECRET_NAME = "certificate-name"
STORAGE_CONNECTION_STRING_SECRET_NAME = "storage-connection-string"
# --- Secret values (bad approach) ---
IOTHUB_CONNECTION_STRING_SECRET_VALUE = ""
IOTHUB_HOSTNAME_SECRET_VALUE = ""
IOTHUB_PROXYNAME_SECRET_VALUE = ""
#PROXY_CERTIFICATE_SECRET_VALUE = "certificate.pem"
PROXY_CERTIFICATE_SECRET_VALUE = ""
STORAGE_CONNECTION_STRING_SECRET_VALUE = ""

# ----------------------------------------------------------------------------------------
# --- CONSUMER PARAMETERS ----------------------------------------------------------------
# ----------------------------------------------------------------------------------------
EVENTHUB_CONSUMER_GROUP = "dev-forlani"
# --- Secret names in Key Vault ---
EVENTHUB_CONNECTION_STRING_SECRET_NAME = "iothub-builtin-endpoint-connection-string"
EVENTHUB_NAME_SECRET_NAME = "iothub-builtin-endpoint-name"
# --- Secret values (bad approach) ---
EVENTHUB_CONNECTION_STRING_SECRET_VALUE = ""
EVENTHUB_NAME_SECRET_VALUE = ""