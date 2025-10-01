# Locust Load Testing

Performed load testing by simulating multiple IoT devices connecting to a proxy, evaluating system performance and scalability.


## Requirements installation
```
pip install -r requirements
```
---------------

## Test Init

Initialization of the device IDs available for the Locust test.

Steps:
1. Read parameters from Key Vault or from the config file (using the PARAMS_SOURCE parameter in config.py).
2. Allocate the device IDs in an Azure Storage Queue.
3. Deprovision old devices from IoT Hub (optional).

Run :
```
python .\test_init.py
```

---------------

## Locustfile

Simulation of an IoT device connecting to an MQTT proxy or directly to IoT Hub and publishing messages.

Steps:
1. Read parameters from Key Vault or from the config file (using the PARAMS_SOURCE parameter in config.py).
2. Acquire a device ID from the Azure Storage Queue.
3. Provision the device on IoT Hub.
4. Generate the SAS token to connect to IoT Hub.
5. Connect to the MQTT Proxy or IoT Hub.
6. Periodically publish messages.

Run single processor:
```
locust -f .\locustfile.py
```

Run multiple processors using all VM cores:
```
.\Run-locust-multi-processors.ps1 
```

---------------

## Consumer

Instance that consumes messages from a generic Event Hub (including IoT Hub built-in endpoint).
Optionally, messages can be filtered for a specific group of devices.

Steps:
1. Read parameters from Key Vault or from the config file (using the PARAMS_SOURCE parameter in config.py).
2. Create Event Hub consumer.
3. Start receiving messages.

Run:
```
python .\consumer.py
```