param(
    [Parameter(Mandatory=$true)][string]$IotHubHostname,
    [Parameter(Mandatory=$false)][string]$KeyVaultSecretUrl
)

$pwd_slashes = $pwd -replace '\\', '/'
$token_result = az account get-access-token --resource https://vault.azure.net | ConvertFrom-Json
$token = $token_result.accessToken
docker run -d --rm `
  --mount "type=bind,source=$pwd_slashes/scripts,target=/docker-entrypoint.d/init-scripts" `
  --mount "type=bind,source=$pwd_slashes/templates,target=/etc/nginx/templates" `
  -e TOKEN=$token `
  -e KV_SECRET_URL=$KeyVaultSecretUrl `
  -e NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx `
  -e IOTHUB_HOSTNAME=$IotHubHostname `
  -p 8883:8883 `
  -p 4080:80 `
  -p 4443:443 `
  nginx:latest

  # Add the following line if you want to mount local certificates
  #--mount "type=bind,source=$pwd_slashes/secrets,target=/certs" `
