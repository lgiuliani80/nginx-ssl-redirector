from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import Twin

class IoTHubService:
    def __init__(self, connection_string: str):
        self.registry_manager = IoTHubRegistryManager(connection_string)

    def provision_device(self, device_id: str):
        try:
            device = self.registry_manager.create_device_with_sas(
                device_id=device_id,
                primary_key="",
                secondary_key="",
                status="enabled"
            )
        except Exception:
            device = self.registry_manager.get_device(device_id)
        device_key = device.authentication.symmetric_key.primary_key
        return device_key

    def delete_device(self, device_id: str):
        self.registry_manager.delete_device(device_id)

    def get_twin(self, device_id: str):
        return self.registry_manager.get_twin(device_id)

    def update_twin(self, device_id: str, twin_patch: Twin):
        self.registry_manager.update_twin(device_id, twin_patch, twin_patch.etag)