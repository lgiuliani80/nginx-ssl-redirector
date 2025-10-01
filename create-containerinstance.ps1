#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Creates Azure Container Instance with storage account, managed identity, and required configuration.

.DESCRIPTION
    This script creates the following Azure resources:
    - Storage account optimized for Azure Files
    - User assigned managed identity
    - Container Instance with nginx:latest image and proper configuration

.PARAMETER ResourceGroup
    The name of the Azure resource group where resources will be created.

.PARAMETER StorageAccountName
    The name of the storage account to create.

.PARAMETER UmiName
    The name of the user assigned managed identity to create.

.PARAMETER DnsLabel
    The DNS label for the container instance.

.PARAMETER KeyVaultSecretUrl
    The URL of the Key Vault secret containing the certificate.

.PARAMETER IothubHostname
    The hostname of the IoT Hub.

.PARAMETER LogAnalyticsWorkspace
    The name or resource ID of the Log Analytics workspace for diagnostic settings.

.PARAMETER ContainerInstanceName
    The name of the container instance to create.

.PARAMETER Location
    The Azure region where resources will be created. Defaults to 'East US'.

.EXAMPLE
    .\create-containerinstance.ps1 -ResourceGroup "myRG" -StorageAccountName "mystorageacct" -UmiName "myumi" -DnsLabel "mydns" -KeyVaultSecretUrl "https://mykv.vault.azure.net/secrets/mycert" -IothubHostname "myiothub.azure-devices.net" -LogAnalyticsWorkspace "mylogworkspace" -ContainerInstanceName "mycontainer"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory = $true)]
    [string]$ContainerInstanceName,
    
    [Parameter(Mandatory = $true)]
    [string]$StorageAccountName,
    
    [Parameter(Mandatory = $true)]
    [string]$UmiName,
    
    [Parameter(Mandatory = $true)]
    [string]$LogAnalyticsWorkspaceName,
    
    [Parameter(Mandatory = $true)]
    [string]$LogAnalyticsWorkspaceResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$DnsLabel,
    
    [Parameter(Mandatory = $true)]
    [string]$KeyVaultSecretUrl,
    
    [Parameter(Mandatory = $true)]
    [string]$IothubHostname,
    
    [Parameter(Mandatory = $false)]
    [string]$Location = "ItalyNorth"
)

# Error handling
$ErrorActionPreference = "Stop"

try {
    Write-Host "Starting Azure resource creation..." -ForegroundColor Green
    
    # Check if logged in to Azure
    Write-Host "Checking Azure login status..." -ForegroundColor Yellow
    $account = az account show --query "name" -o tsv 2>$null
    if (-not $account) {
        throw "Not logged in to Azure. Please run 'az login' first."
    }
    Write-Host "Logged in to Azure account: $account" -ForegroundColor Green
    
    # Create Storage Account optimized for Azure Files
    Write-Host "Creating storage account '$StorageAccountName'..." -ForegroundColor Yellow
    az storage account create `
        --name $StorageAccountName `
        --resource-group $ResourceGroup `
        --location $Location `
        --sku Standard_ZRS `
        --kind StorageV2 `
        --enable-large-file-share `
        --allow-shared-key-access true `
        --public-network-access Enabled `
        --access-tier Hot
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create storage account"
    }
    Write-Host "Storage account created successfully" -ForegroundColor Green
    
    # Get storage account key
    Write-Host "Getting storage account key..." -ForegroundColor Yellow
    $storageKey = az storage account keys list `
        --resource-group $ResourceGroup `
        --account-name $StorageAccountName `
        --query "[0].value" -o tsv
    
    if (-not $storageKey) {
        throw "Failed to retrieve storage account key"
    }
    Write-Host "Storage account key retrieved" -ForegroundColor Green
    
    # Create file shares
    Write-Host "Creating file shares..." -ForegroundColor Yellow
    az storage share create `
        --name "scripts" `
        --account-name $StorageAccountName `
        --account-key $storageKey
    
    az storage share create `
        --name "config" `
        --account-name $StorageAccountName `
        --account-key $storageKey
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create file shares"
    }
    Write-Host "File shares created successfully" -ForegroundColor Green
    
    # Upload files to shares
    Write-Host "Uploading files to storage shares..." -ForegroundColor Yellow
    
    # Upload 01-get-certificate.sh to scripts share
    $scriptPath = Join-Path $PSScriptRoot "scripts\01-get-certificate.sh"
    if (Test-Path $scriptPath) {
        az storage file upload `
            --account-name $StorageAccountName `
            --account-key $storageKey `
            --share-name "scripts" `
            --source $scriptPath `
            --path "01-get-certificate.sh"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ 01-get-certificate.sh uploaded to scripts share" -ForegroundColor Green
        } else {
            Write-Warning "Failed to upload 01-get-certificate.sh"
        }
    } else {
        Write-Warning "Script file not found at: $scriptPath"
    }
    
    # Upload nginx.conf.template to config share
    $templatePath = Join-Path $PSScriptRoot "templates\nginx.conf.template"
    if (Test-Path $templatePath) {
        az storage file upload `
            --account-name $StorageAccountName `
            --account-key $storageKey `
            --share-name "config" `
            --source $templatePath `
            --path "nginx.conf.template"

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ nginx.conf.template uploaded to config share" -ForegroundColor Green
        } else {
            Write-Warning "Failed to upload nginx.conf.template"
        }
    } else {
        Write-Warning "Template file not found at: $templatePath"
    }
    
    Write-Host "File uploads completed" -ForegroundColor Green
    
    # Create User Assigned Managed Identity
    Write-Host "Creating user assigned managed identity '$UmiName'..." -ForegroundColor Yellow
    az identity create `
        --name $UmiName `
        --resource-group $ResourceGroup `
        --location $Location
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create user assigned managed identity"
    }
    Write-Host "User assigned managed identity created successfully" -ForegroundColor Green
    
    # Get UMI Client ID
    Write-Host "Getting managed identity client ID..." -ForegroundColor Yellow
    $umiClientId = az identity show `
        --name $UmiName `
        --resource-group $ResourceGroup `
        --query "clientId" -o tsv
    
    if (-not $umiClientId) {
        throw "Failed to retrieve managed identity client ID"
    }
    Write-Host "Managed identity client ID: $umiClientId" -ForegroundColor Green
    
    # Get UMI Resource ID
    $umiResourceId = az identity show `
        --name $UmiName `
        --resource-group $ResourceGroup `
        --query "id" -o tsv

    # Create Log Analytics Workspace
    az monitor log-analytics workspace create `
        --resource-group $ResourceGroup `
        --workspace-name $LogAnalyticsWorkspaceName `
        --location $Location

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create log analytics workspace"
    }
    Write-Host "Log analytics workspace created successfully" -ForegroundColor Green
    
    # Get Log Analytics Workspace ID and Key
    Write-Host "Getting Log Analytics workspace information..." -ForegroundColor Yellow
    $workspaceId = az monitor log-analytics workspace show `
        --workspace-name $LogAnalyticsWorkspaceName `
        --resource-group $LogAnalyticsWorkspaceResourceGroup `
        --query "customerId" -o tsv
    
    $workspaceKey = az monitor log-analytics workspace get-shared-keys `
        --workspace-name $LogAnalyticsWorkspaceName `
        --resource-group $LogAnalyticsWorkspaceResourceGroup `
        --query "primarySharedKey" -o tsv
    
    if (-not $workspaceId -or -not $workspaceKey) {
        throw "Failed to retrieve Log Analytics workspace information"
    }
    Write-Host "Log Analytics workspace information retrieved" -ForegroundColor Green
    
    # Create Container Instance
    Write-Host "Creating container instance '$ContainerInstanceName'..." -ForegroundColor Yellow
    # azure-containerinstance.yaml

    $yaml = @"
apiVersion: 2018-10-01
location: $Location
name: $ContainerInstanceName
type: Microsoft.ContainerInstance/containerGroups
identity:
  type: UserAssigned
  userAssignedIdentities:
    '$($umiResourceId)': {}
properties:
  containers:
    - name: nginx-container
      properties:
        image: nginx:latest
        command:
          - "/bin/bash"
          - "-c"
          - "ulimit -n 65535 && /docker-entrypoint.sh nginx -g 'daemon off;'"
        resources:
          requests:
            cpu: 1.0
            memoryInGb: 1.5
        ports:
          - port: 443
          - port: 8883
        environmentVariables:
          - name: KV_SECRET_URL
            value: $KeyVaultSecretUrl
          - name: NGINX_ENVSUBST_OUTPUT_DIR
            value: /etc/nginx
          - name: IOTHUB_HOSTNAME
            value: $IothubHostname
          - name: UMI_CLIENT_ID
            value: $umiClientId
        volumeMounts:
          - name: scripts-volume
            mountPath: /docker-entrypoint.d/init-scripts
          - name: config-volume
            mountPath: /etc/nginx/templates
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    dnsNameLabel: $DnsLabel
    ports:
    - protocol: tcp
      port: 443
    - protocol: tcp
      port: 8883
  volumes:
    - name: scripts-volume
      azureFile:
        shareName: scripts
        storageAccountName: $StorageAccountName
        storageAccountKey: $storageKey
    - name: config-volume
      azureFile:
        shareName: config
        storageAccountName: $StorageAccountName
        storageAccountKey: $storageKey
  diagnostics:
    logAnalytics:
      workspaceId: $workspaceId
      workspaceKey: $workspaceKey
"@ 
    
    # Write-Host $yaml -ForegroundColor Cyan

    $yamlFile = [System.IO.Path]::GetTempFileName() + ".yaml"
    $yaml | Out-File -FilePath $yamlFile -Encoding UTF8

    try {
        az container create `
            --resource-group $ResourceGroup `
            --file $yamlFile
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create container instance"
        }
    }
    finally {
        Remove-Item -Path $yamlFile -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "Container instance created successfully" -ForegroundColor Green
    
    # Get container instance FQDN and IP address
    $containerFqdn = az container show `
        --resource-group $ResourceGroup `
        --name $ContainerInstanceName `
        --query "ipAddress.fqdn" -o tsv
    
    $containerIp = az container show `
        --resource-group $ResourceGroup `
        --name $ContainerInstanceName `
        --query "ipAddress.ip" -o tsv
    
    Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Resources created:" -ForegroundColor Cyan
    Write-Host "  📦 Storage Account: $StorageAccountName" -ForegroundColor White
    Write-Host "  🔐 Managed Identity: $UmiName (Client ID: $umiClientId)" -ForegroundColor White
    Write-Host "  🐳 Container Instance: $ContainerInstanceName" -ForegroundColor White
    Write-Host "  🌐 FQDN: $containerFqdn" -ForegroundColor White
    Write-Host "  🌍 Public IP: $containerIp" -ForegroundColor White
    Write-Host "  📊 Diagnostics: Connected to Log Analytics workspace '$LogAnalyticsWorkspaceName'" -ForegroundColor White
    
    return @{
        StorageAccountName = $StorageAccountName
        StorageAccountKey = $storageKey
        UmiName = $UmiName
        UmiClientId = $umiClientId
        ContainerInstanceName = $ContainerInstanceName
        ContainerFqdn = $containerFqdn
        ContainerPublicIp = $containerIp
    }
}
catch {
    Write-Error "❌ Deployment failed: $($_.Exception.Message)"
    throw
}
