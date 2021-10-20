# Raspberry PI 4 Model B with DHT11 Temperature/Humidity Sensor as IoT Edge Docker Module

## Setup and configure DHT11 Temperature sensor as Azure IoT Edge Module as Docker container

## Prerequistie

- Raspberry PI 4 Model B board
- Bread board
- Heat Sink with Fan
- DHT11 sensors (cost me $5 for 2 of them)
- Temperature - https://www.amazon.com/HiLetgo-Temperature-Humidity-Digital-3-3V-5V/dp/B01DKC2GQ0/ref=as_li_ss_tl?dchild=1&keywords=dht11&qid=1594447478&sr=8-4&linkCode=ll1&tag=circbasi-20&linkId=e3ae1b1c08241b2ac69056fcd38f0363


## Raspberry PI installation

## Steps

- Take the bread board and lay it in flat surface
- Get some extra wires
- Connect the 3 prong DHT11 into bread board
- Connect the first wire to Ground which is first pin in Raspberry PI
- Connect the 3 prong to 5 PIN in rasperry pi for 5v output
- Connect the middle wire to Pin 7 in rasperry pi which is GPIO PIN 4
- Mine also has extra fan so i am connecting that also to cool raspberrypi
- Check the below pictures

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspdht11-1.jpg "Logo Title Text 1")

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspdht11-2.jpg "Logo Title Text 1")

- Follow the instruction to create a project using visual code
- https://docs.microsoft.com/en-us/azure/iot-edge/tutorial-python-module?view=iotedge-2020-11

```
Note: Make sure the environment is set to ARM other wise it won't work
```

- Create a container registery
- Setup Admin access
- Note the username and password

- Make sure the docker file is changed
- Note i am using balenalib/raspberry-pi-debian, since that worked. The default one had issues

```
## FROM arm32v7/python:3.7-slim-buster
FROM balenalib/raspberry-pi-debian

WORKDIR /app
RUN echo 'asd'

RUN apt-get update && apt-get -y install gcc
RUN apt-get update -y && apt-get install -y python3-dev build-essential

##RUN apt-get update && apt-get install -y python-rpi.gpio python3-rpi.gpio
RUN apt-get update && apt-get install -y python3-rpi.gpio
RUN apt-get install -y python3-pip

RUN pip3 install --upgrade pip wheel setuptools

COPY requirements.txt ./
RUN apt-get install -y libgpiod2

RUN pip3 install -r requirements.txt

COPY . .

USER root:root

CMD [ "python3", "-u", "./main.py" ]
```

- Here is the requirements.txt file

```
azure-iot-device~=2.7.0
board
adafruit-circuitpython-dht
```

- IN this module we are collecting hardware based sensor details
- Container needs privileage access to get the sensor hardware reading
- Here is the deployment.template.json module section look liks

```
        "modules": {
          "PythonModule": {
            "version": "1.0",
            "type": "docker",
            "status": "running",
            "restartPolicy": "always",
            "settings": {
              "image": "${MODULES.PythonModule}",
              "createOptions": {
                "User": "root:root",
                "HostConfig": {
                  "Privileged": true,
                  "IpcMode": "host"
                 }
              }
            }
          }
        }
```

- Now the route configuraiton

```
    "$edgeHub": {
      "properties.desired": {
        "schemaVersion": "1.1",
        "routes": {
          "PythonModuleToIoTHub": "FROM /messages/modules/PythonModule/outputs/* INTO $upstream",
          "sensorToPythonModule": "FROM /messages/modules/pythonmodule/outputs/* INTO BrokeredEndpoint(\"/modules/PythonModule/inputs/input1\")"
        },
        "storeAndForwardConfiguration": {
          "timeToLiveSecs": 7200
        }
      }
    },
```

- Now to the main
- create a python file called main.py

```
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import asyncio
from six.moves import input
import threading
import json
import board
import datetime
from datetime import datetime as dt
import traceback
import adafruit_dht
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message


async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Hub Client for Python" )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()
        # testing code

        # global counters
        TEMPERATURE_THRESHOLD = 25
        TWIN_CALLBACKS = 0
        RECEIVED_MESSAGES = 0

        # connect the client.
        await module_client.connect()
        #dhtDevice = adafruit_dht.DHT11(board.D4)
        dhtDevice = adafruit_dht.DHT11(4)

        # define behavior for receiving an input message on input1
        async def input1_listener(module_client):
            global RECEIVED_MESSAGES
            global TEMPERATURE_THRESHOLD
            while True:
                try:
                    input_message = await module_client.receive_message_on_input("input1")  # blocking call
                    print("the data in the message received on input1 was ")
                    print(input_message.data)
                    print("custom properties are")
                    print(input_message.custom_properties)
                    print("forwarding mesage to output1")
                    await module_client.send_message_to_output(input_message, "output1")
                except Exception as ex:
                    print ( "Unexpected error in input1_listener: %s" % ex )

        async def senddata(module_client):
            global TWIN_CALLBACKS
            global TEMPERATURE_THRESHOLD
            while True:
                try:
                    temperature_c = dhtDevice.temperature
                    temperature_f = temperature_c * (9 / 5) + 32
                    humidity = dhtDevice.humidity
                    #print(
                    #    "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                    #        temperature_f, temperature_c, humidity
                    #    )
                    #)

                    now = dt.now()
                    dt_string = now.strftime("%m/%d/%Y %H:%M:%S.%f")
                    dictionary = {'deviceid':'tempdev', 'timecreated':dt_string, 'temperature':temperature_f,'humidity':humidity}
                    jsonString = json.dumps(dictionary, indent=4)
                    print(" Message - ", jsonString)
                    #await module_client.send_message(jsonString)
                    messagestring = Message(bytearray(jsonString, "UTF-8"))
                    await module_client.send_message_to_output(messagestring, "output2")
                    time.sleep(5.0)

                except:
                    # printing stack trace
                    traceback.print_exception(*sys.exc_info())

                #except Exception as ex:
                #    print ( "Unexpected error in senddata: %s" % ex )

        # define behavior for halting the application
        def stdin_listener():
            while True:
                try:
                    selection = input("Press Q to quit\n")
                    if selection == "Q" or selection == "q":
                        print("Quitting...")
                        break
                except:
                    time.sleep(10)
        
 

        # Schedule task for C2D Listener
        # listeners = asyncio.gather(input1_listener(module_client))
        # listeners = asyncio.gather(input1_listener(module_client), twin_patch_listener(module_client), senddata(module_client))
        listeners = asyncio.gather(input1_listener(module_client),senddata(module_client))

        print ( "The sample is now waiting for messages. ")

        # Run the stdin listener in the event loop
        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        # Wait for user to indicate they are done listening for messages
        await user_finished

        # Cancel listening
        listeners.cancel()

        # Finally, disconnect
        dhtDevice.exit()
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

    # If using Python 3.7 or above, you can use following code instead:
    # asyncio.run(main())
```

- Now right click the deployment file and Generate IoT Edge Deployment manifest
- Will create arm32 json deployment file
- Right click Build and Push IoT Edge Solution
- This will take some time to create the image and upload
- Store the container username and password in .env file
- Now connect to IoT hub in Visual Studio
- Select the IoT edge device
- Click Create deployment for single device
- Go to Config file and select deployment.arm32v7.json
- Wait for deployment to complete
- If something is not updating with docker image please delete the module in IoT hub in portal
- Then apply the deployment in visual studio by right click the IoT edge device and choose Create Deployment for Single Device
- Wait for few mins
- SSH to Raspberry pi and type


```
sudo iotedge list
```

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspdht11-6.jpg "Logo Title Text 1")

- Now see the docker logs

```
sudo dockler logs -f PythonModule
```

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspdht11-7.jpg "Logo Title Text 1")

- Validate the data is available in cloud
- I use Stream analytics to read and write as parquet for further processing

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspdht11-8.jpg "Logo Title Text 1")

- Here are some clean up commands for docker and iot Edge

```
sudo docker system prune -a

sudo docker system prune

sudo docker image prune

sudo docker pull acrname.azurecr.io/pythonmodule:0.0.1-arm32v7

docker login -u ACRusername -p acrpassword acrname.azurecr.io
```