import asyncio
import logging
from utils import config
from azure.eventhub.aio import EventHubConsumerClient
from services.keyvault_service import KeyVaultService

logging.basicConfig(level=logging.INFO)

# Monitoring device list
TARGET_DEVICE_IDS = [
    "00-00-00-00-00-00-00-00-00-00-00-01",
    "00-00-00-00-00-00-00-00-00-00-00-02",
    "00-00-00-00-00-00-00-00-00-00-00-03",
    "00-00-00-00-00-00-00-00-00-00-00-04",
    "00-00-00-00-00-00-00-00-00-00-00-05",
    "31-ff-d6-05-50-4d-37-34-15-72-20-43"
]


async def on_event(partition_context, event):
    body = event.body_as_str()
    system_props = event.system_properties

    device_id = event.system_properties[b"iothub-connection-device-id"].decode()

    if device_id in TARGET_DEVICE_IDS:
        logging.info(
            f"📥 Device {device_id} | "
            f"Seq: {event.sequence_number} | "
            f"Offset: {event.offset} | "
            f"Enqueued: {system_props.get('x-opt-enqueued-time')} | "
            f"Body: {body}"
        )

    # checkpoint
    await partition_context.update_checkpoint(event)


async def main(params_from_key_vault: bool):
    if params_from_key_vault:
        # Read secrets from Key Vault
        kv_service = KeyVaultService(config.KEY_VAULT_NAME)
        eventhub_connection_string = kv_service.get_secret(config.EVENTHUB_CONNECTION_STRING_SECRET_NAME)
        eventhub_name = kv_service.get_secret(config.EVENTHUB_NAME_SECRET_NAME)
    else:
        # Read secret from config file
        eventhub_connection_string = config.EVENTHUB_CONNECTION_STRING_SECRET_VALUE
        eventhub_name = config.EVENTHUB_NAME_SECRET_VALUE

    eventhub_consumer_group = config.EVENTHUB_CONSUMER_GROUP

    client = EventHubConsumerClient.from_connection_string(
        conn_str=eventhub_connection_string,
        consumer_group=eventhub_consumer_group,
        eventhub_name=eventhub_name,
    )

    async with client:
        await client.receive(
            on_event=on_event,
            starting_position="@latest",
        )


if __name__ == "__main__":
    params_from_key_vault = config.PARAMS_SOURCE == "keyvault"
    asyncio.run(main(params_from_key_vault))