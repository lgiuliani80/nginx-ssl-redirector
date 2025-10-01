import time
import urllib.parse
import hmac
import base64
import hashlib


class SasTokenService:

    @staticmethod
    def generate_sas_token(iothub_hostname: str, device_id: str, device_key: str, expiry_hours: int = 24):
        resource_uri = f"{iothub_hostname}/devices/{device_id}"
        ttl = int(time.time()) + expiry_hours * 60 * 60
        to_sign = f"{urllib.parse.quote_plus(resource_uri)}\n{ttl}"
        signature = base64.b64encode(
            hmac.new(base64.b64decode(device_key), to_sign.encode("utf-8"), hashlib.sha256).digest()
        ).decode("utf-8")
        token = (
            f"SharedAccessSignature sr={urllib.parse.quote_plus(resource_uri)}"
            f"&sig={urllib.parse.quote_plus(signature)}&se={ttl}"
        )
        return token
