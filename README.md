# IoT Hub Redirector

A containerized nginx-based SSL proxy solution for Azure IoT Hub that provides secure certificate management and traffic redirection.

## Overview

This project creates an Azure Container Instance running nginx that acts as an SSL proxy to Azure IoT Hub. It automatically retrieves SSL certificates from Azure Key Vault using managed identity authentication and provides secure traffic forwarding on ports 443 and 8883.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IoT Devices   │──> │  Container       │───>│   Azure IoT     │
│                 │    │  Instance        │    │   Hub           │
│                 │    │  (nginx proxy)   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Azure Key       │
                       │  Vault           │
                       │  (Certificates)  │
                       └──────────────────┘
```

## Features

- 🔐 **Automatic Certificate Management**: Retrieves SSL certificates from Azure Key Vault
- 🌐 **SSL Proxy**: Secure forwarding to Azure IoT Hub on port 8883
- 🔄 **Auto-restart**: Container restarts automatically on failure
- 📊 **Monitoring**: Integrated with Azure Log Analytics
- 🏗️ **Infrastructure as Code**: Automated Azure resource deployment
- 🐳 **Containerized**: Easy deployment and scaling

## Deployment options

### Azure Container Instances

[Azure Container Instances deployment guide](ACI.md).

### Azure Container Apps

[Azure Container Apps deployment guide](ACA.md).

### Azure Service Fabric Cluster

[Azure Service Fabric Cluster deployment guide](/servicefabric/README.md).

## Load Testing by Locust

Performed load testing by simulating multiple IoT devices connecting to a proxy, evaluating system performance and scalability.  
See documentation here [Locust Load Testing](/locust-iothub/README.md).