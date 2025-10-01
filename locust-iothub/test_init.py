import time
import logging
from services.iothub_service import IoTHubService
from services.keyvault_service import KeyVaultService
from services.queue_service import QueueService
from utils import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)


def allocate_devices_in_queue(storage_conn_string: str, queue_name: str, numb_of_devices: int):
    queue_service = QueueService(storage_conn_string, queue_name)

    logging.info("Deleting queue")
    max_retries = 3
    delay = 5
    for attempt in range(1, max_retries + 1):
        try:
            queue_service.delete_queue()
            logging.info("Deleting queue done")
            break
        except Exception as ex:
            logging.error(f"Deleting queue failed ({attempt} of {max_retries}): {ex}")
            if attempt < max_retries:
                logging.info(f"Retry in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Deleting queue failed {max_retries} times.")

    logging.info("Creating queue")
    max_retries = 5
    delay = 15
    for attempt in range(1, max_retries + 1):
        try:
            queue_service.create_queue()
            logging.info("Creating queue done")
            break
        except Exception as ex:
            logging.error(f"Creating queue failed ({attempt} of {max_retries}): {ex}")
            if attempt < max_retries:
                logging.info(f"Retry in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Creating queue failed {max_retries} times.")

    logging.info("Populating queue")
    for i in range(1, numb_of_devices + 1):
        device_id = _dec_to_12_pairs(i)
        queue_service.send_message(device_id)
        if i % 20 == 0:
            logging.info(f"Added {i} device ids")


def deprovision_devices_in_iothub(iothub_conn_string: str, numb_of_devices: int):
    iothub_service = IoTHubService(iothub_conn_string)

    for i in range(1, numb_of_devices + 1):
        device_id = _dec_to_12_pairs(i)
        try:
            logging.info(f"Device {i} of {numb_of_devices} deleted")
            iothub_service.delete_device(device_id)
        except Exception:
            continue


def _dec_to_12_pairs(n: int) -> str:
    """
    Convert a decimal number into exactly 12 pairs (24 hex digits) joined by '-'.
    Pads with leading zeros if needed.

    Parameters
    ----------
    n : int
        Decimal number to convert.

    Returns
    -------
    str
        Hex string in format '00-00-00-00-00-00-00-00-00-00-00-01'
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input must be a non-negative integer")

    # Convert to hex string without '0x', in lowercase
    hex_str = f"{n:024x}"  # 24 cifre esadecimali → 12 coppie

    # Split pairs
    pairs = [hex_str[i:i+2] for i in range(0, 24, 2)]

    return "-".join(pairs)


if __name__ == "__main__":
    logging.info(f"START.")

    params_from_key_vault = config.PARAMS_SOURCE == "keyvault"

    if params_from_key_vault:
        # Read secrets from Key Vault
        kv_service = KeyVaultService(key_vault_name=config.KEY_VAULT_NAME)
        storage_connection_string = kv_service.get_secret(config.STORAGE_CONNECTION_STRING_SECRET_NAME)
        iothub_connection_string = kv_service.get_secret(config.IOTHUB_CONNECTION_STRING_SECRET_NAME)
    else:
        # Read secret from config file
        storage_connection_string = config.STORAGE_CONNECTION_STRING_SECRET_VALUE
        iothub_connection_string = config.IOTHUB_CONNECTION_STRING_SECRET_VALUE

    number_of_devices = config.MAX_DEVICE_IDS

    # Init queue devices
    logging.info(f"Allocating device ids in queue")
    allocate_devices_in_queue(storage_connection_string, config.STORAGE_QUEUE_NAME, number_of_devices)

    # Clean iothub devices
    logging.info(f"Cleaning iothub devices")
    # deprovision_devices_in_iothub(iothub_connection_string, number_of_devices)

    logging.info(f"DONE.")