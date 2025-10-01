import base64
import tempfile
from azure.identity import ManagedIdentityCredential
from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates

class KeyVaultService:

    def __init__(self, key_vault_name: str, managed_identity_client_id: str = None):
        if not managed_identity_client_id:
            credential = AzureCliCredential()
        else:
            credential = ManagedIdentityCredential(client_id=managed_identity_client_id)

        self.client = SecretClient(vault_url=f"https://{key_vault_name}.vault.azure.net/", credential=credential)

    def get_secret(self, name: str) -> str:
        return self.client.get_secret(name).value

    def set_secret(self, name: str, value: str):
        self.client.set_secret(name, value)

    def get_certificate_path(self, name: str) -> str:
        certificate = self.client.get_secret(name)
        cert_bytes = base64.b64decode(certificate.value)

        # Write to a temporary file. If it's a PFX: convert to PEM
        try:
            private_key, cert, additional_certs = load_key_and_certificates(cert_bytes, password=None, backend=default_backend())
            # Salva solo il certificato principale + eventuali CA intermedi in un file temporaneo
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as f:
                f.write(cert.public_bytes(encoding=serialization.Encoding.PEM))
                if additional_certs:
                    for c in additional_certs:
                        f.write(c.public_bytes(encoding=serialization.Encoding.PEM))
                ca_path = f.name
        except ValueError:
            # If it's not PFX, assume it's already PEM
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as f:
                f.write(cert_bytes)
                ca_path = f.name

        return ca_path