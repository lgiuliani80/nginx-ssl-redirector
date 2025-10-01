import paho.mqtt.client as mqtt
import ssl

class MqttClient:
    def __init__(self, client_id: str, mqtt_server: str, username: str, password: str, ca_certs: str):
        self.client_id = client_id
        self.mqtt_server = mqtt_server
        self.username = username
        self.password = password
        self.ca_certs = ca_certs
        self.connected = False

        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        self.client.username_pw_set(username=username, password=password)

        if self.ca_certs:
            self.client.tls_set(ca_certs=ca_certs, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
        else:
            self.client.tls_set(cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        # self.client.on_publish = self._on_publish

    def connect(self):
        self.client.connect(self.mqtt_server, 8883)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def is_connected(self):
        return self.connected

    def publish(self, topic: str, payload: str):
        if self.connected:
            self.client.publish(topic, payload, qos=1)

    # Callbacks
    def _on_connect(self, client, userdata, flags, rc):
        self.connected = (rc == 0)
        if rc == 0:
            print(f"[{self.client_id}] ➡️ Connected, rc={rc}")
        else:
            print(f"[{self.client_id}] ❌ Connection failed, rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"[{self.client_id}] 🔌 Disconnected rc={rc}")

    def _on_publish(self, client, userdata, mid):
        print(f"[{self.client_id}] 📤 Message {mid} published")
