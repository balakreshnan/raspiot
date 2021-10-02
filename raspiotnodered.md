# Raspberry PI NodeRed as Azure IoT Edge

## Use Node-Red as IoT Edge Modules

## Steps

- Go to - https://github.com/iotblackbelt/noderededgemodule
- Follow the instruction for createing a new IoT Edge with Node Red
- For Raspberry pi 32 i use armv7
- Module name as: nodered
- i used iotblackbelt/noderededgemodule:1.0.2-arm32v7

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered4.jpg "Logo Title Text 1")

- For container option

```
{
  "User": "root:root",
  "HostConfig": {
    "Privileged": true,
    "Binds": [
      "/node-red:/data"
    ],
    "PortBindings": {
      "1880/tcp": [
        {
          "HostPort": "1880"
        }
      ]
    }
  }
}
```

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered5.jpg "Logo Title Text 1")

- Route

```
"routeToHub": "FROM /messages/modules/nodered/outputs/* INTO $upstream",
"tempToRed": "FROM /messages/modules/SimulatedTemperatureSensor/* INTO BrokeredEndpoint("/modules/nodered/inputs/input1")"
```

- Now click Create and wait for few min

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered3.jpg "Logo Title Text 1")

- Go to Raspberry pi
- do 

```
sudo iotedge list
```

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered8.jpg "Logo Title Text 1")

- There should be 4 modules

- Now you should see nodered module
- Now in the above Repo there is a example folder
- https://github.com/iotblackbelt/noderededgemodule/tree/master/node-red-contrib-azure-iot-edge-module/examples
- Save the example.json to local folder as example-1.json
- Open the raspberry pi nodered ui - http://ip:1880
- Click import and select the example-1.json

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered2.jpg "Logo Title Text 1")

- Should open 2 flows
- Click Deploy

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered1.jpg "Logo Title Text 1")

- Check the logs

```
sudo docker logs nodered
```

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered6.jpg "Logo Title Text 1")

- As far as data is flowing to iot
- Process the data using stream analytics and store to storage
- Stream analytics query

```
SELECT
    machine.temperature AS MachTemp,
    machine.pressure as pressure,
    ambient.temperature as AmbTemp,
    ambient.humidity as humidity,
    timeCreated,
    EventProcessedUtcTime,
    PartitionId,
    EventEnqueuedUtcTime,
    IoTHub.ConnectionDeviceId as DeviceId,
    IoTHub.EnqueuedTime as DeviceEnqueuedTime
INTO
    output
FROM
    input
```

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered7.jpg "Logo Title Text 1")

- Also check the NodeRed UI dashboard by http://ip:1880/ui

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/nodered9.jpg "Logo Title Text 1")