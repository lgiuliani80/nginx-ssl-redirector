import datetime
import json
import random
import logging
from azure.iot.hub.protocol.models import Twin, TwinProperties
from locust import User, task, between
from services.keyvault_service import KeyVaultService
from services.queue_service import QueueService
from services.iothub_service import IoTHubService
from services.sastoken_service import SasTokenService
from mqtt.mqtt_client import MqttClient
from utils import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)


def acquire_device_id(storage_connection_string: str, queue_name: str):
    """Gets a free device from the Azure Queue"""
    queue_service = QueueService(storage_connection_string, queue_name)
    device_id = queue_service.receive_message().content
    try:
        queue_service.delete_message()
    except Exception:
        pass
    return device_id


def provision_device(iothub_connection_string: str, device_id: str):
    """Provisions a device on the Azure IoT Hub."""
    iothub_service = IoTHubService(iothub_connection_string)
    device_key = iothub_service.provision_device(device_id)

    # Update twin device
    twin_patch = Twin(
        tags={"deviceType": "mydevicetype"},
        properties=TwinProperties(
            desired={
                "env": "",
                "eventhub": {
                    "name": "myeventhub",
                    "namespace": "myeventhubnamespace",
                    "policy": "device"
                },
                "lastConfigurationChanged": datetime.datetime.now().isoformat() + "Z",
                "ring": ""
            }
        )
    )
    iothub_service.update_twin(device_id, twin_patch)

    return device_key


def release_device(storage_connection_string: str, queue_name: str, iothub_connection_string: str, device_id: str):
    """Releases the device by deprovisioning it and adding it to the queue."""
    try:
        # Delete device from iothub
        iothub_service = IoTHubService(iothub_connection_string)
        iothub_service.delete_device(device_id)
        # Release device
        queue_service = QueueService(storage_connection_string, queue_name)
        queue_service.send_message(device_id)
        logging.info(f"🔄 Released device {device_id}")
    except Exception:
        logging.error(f"Error releasing device {device_id}")


# ------------------ Locust IoTDeviceUser ------------------ #
class IoTDeviceUser(User):
    wait_time = between(5, 10)

    def __init__(self, environment):
        super().__init__(environment)
        self.storage_connection_string = None
        self.iothub_connection_string = None
        self.storage_queue_name = None
        self.device_id = None
        self.device_key = None
        self.device_client = None
        self.params_from_key_vault = config.PARAMS_SOURCE == "keyvault"

    def on_start(self):
        """At the start of the test, each worker acquires a unique device."""
        if self.params_from_key_vault:
            # Read secrets from Key Vault
            kv_service = KeyVaultService(config.KEY_VAULT_NAME)
            self.storage_connection_string = kv_service.get_secret(config.STORAGE_CONNECTION_STRING_SECRET_NAME)
            self.iothub_connection_string = kv_service.get_secret(config.IOTHUB_CONNECTION_STRING_SECRET_NAME)
            iothub_hostname = kv_service.get_secret(config.IOTHUB_HOSTNAME_SECRET_NAME)
            iothub_proxy = kv_service.get_secret(config.IOTHUB_PROXYNAME_SECRET_NAME)
            certificate = kv_service.get_certificate_path(config.PROXY_CERTIFICATE_SECRET_NAME)
        else:
            # Read secret from config file
            self.storage_connection_string = config.STORAGE_CONNECTION_STRING_SECRET_VALUE
            self.iothub_connection_string = config.IOTHUB_CONNECTION_STRING_SECRET_VALUE
            iothub_hostname = config.IOTHUB_HOSTNAME_SECRET_VALUE
            iothub_proxy = config.IOTHUB_PROXYNAME_SECRET_VALUE
            certificate = config.PROXY_CERTIFICATE_SECRET_VALUE

        self.storage_queue_name = config.STORAGE_QUEUE_NAME

        # Acquire the first device id available
        self.device_id = acquire_device_id(self.storage_connection_string, self.storage_queue_name)

        # Provision device
        self.device_key = provision_device(self.iothub_connection_string, self.device_id)

        # Generate SAS Token
        sas_token = SasTokenService().generate_sas_token(iothub_hostname, self.device_id, self.device_key)

        # Connect to MQTT Sever
        username = f"{iothub_hostname}/{self.device_id}/?api-version=2021-04-12"
        self.device_client = MqttClient(client_id=self.device_id,
                                        mqtt_server=iothub_proxy,
                                        username=username,
                                        password=sas_token,
                                        ca_certs=certificate)
        self.device_client.connect()

    def on_stop(self):
        """At the end, release the device and close the connection."""
        if getattr(self, "device_client", None):
            try:
                self.device_client.disconnect()
            except Exception:
                pass

        if getattr(self, "device_id", None):
            try:
                release_device(self.storage_connection_string, self.storage_queue_name, self.iothub_connection_string, self.device_id)
            except Exception:
                pass

    @task
    def send_message(self):
        if self.device_client:
            try:
                promoted_properties = ""
                payload = {"Temperature": round(random.uniform(20, 25), 1)}
                if promoted_properties:
                    self.device_client.publish(f"devices/{self.device_id}/messages/events/{promoted_properties}", json.dumps(payload))
                else:
                    self.device_client.publish(f"devices/{self.device_id}/messages/events", json.dumps(payload))
            except Exception as e:
                logging.error(f"Error sending message: {e}")