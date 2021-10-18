# Raspberry PI 4 Model B with DHT11 Temperature/Humidity Sensor

## Setup and configure DHT11 Temperature sensor

## Prerequistie

- Raspberry PI 4 Model B board
- Bread board
- Heat Sink with Fan
- DHT11 sensors (cost me $5 for 2 of them)
- Temperature - https://www.amazon.com/HiLetgo-Temperature-Humidity-Digital-3-3V-5V/dp/B01DKC2GQ0/ref=as_li_ss_tl?dchild=1&keywords=dht11&qid=1594447478&sr=8-4&linkCode=ll1&tag=circbasi-20&linkId=e3ae1b1c08241b2ac69056fcd38f0363


## Raspberry PI installation

- install ada fruit libraries

```
pip3 install adafruit-circuitpython-dht
```

- Install libgpio 

```
sudo apt-get install libgpiod2
```

- Above is the newly updated libraries
- Follow this article - https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup

- Check this article for hardware setup - https://www.thegeekpub.com/236867/using-the-dht11-temperature-sensor-with-the-raspberry-pi/
- DHT has 3 prongs
- Middle is the data output. Mine says out
- First and last are the power and groud corresponding.

## Setup

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

- Once connected now it's time to turn raspberry on

## Raspberry PI 4 Coding

- install ada fruit libraries

```
pip3 install adafruit-circuitpython-dht
```

- Install libgpio 

```
sudo apt-get install libgpiod2
```

- Now time to create a code
- Remember we connected the data pin to 7th pin in the raspberry pi board
- Which is GPIO Pin 4
- We are going to write python code
- Now create a Azure IoT hub resource
- Create a iot device and get the connection string
- Make sure all the libraries are available
- Also use python3


```
# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import time
import board
import adafruit_dht
import json
from datetime import datetime

import os
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient


async def main():
    # Fetch the connection string from an enviornment variable
    conn_str = "HostName=iothubname.azure-devices.net;DeviceId=deviceid;SharedAccessKey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    dhtDevice = adafruit_dht.DHT11(board.D4)

    # Create instance of the device client using the connection string
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    # Connect the device client.
    await device_client.connect()
    while True:
       try:
           # Print the values to the serial port
           temperature_c = dhtDevice.temperature
           temperature_f = temperature_c * (9 / 5) + 32
           humidity = dhtDevice.humidity
           print(
               "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                   temperature_f, temperature_c, humidity
               )
           )

           now = datetime.now()
           dt_string = now.strftime("%m/%d/%Y %H:%M:%S.%f")
           dictionary = {'deviceid':'tempdev', 'timecreated':dt_string, 'temperature':temperature_f,'humidity':humidity}
           jsonString = json.dumps(dictionary, indent=4)
           print(" Message - ", jsonString)
           await device_client.send_message(jsonString)
           time.sleep(5.0)


       except RuntimeError as error:
           # Errors happen fairly often, DHT's are hard to read, just keep going
           print(error.args[0])
           time.sleep(5.0)
           continue
       except Exception as error:
           dhtDevice.exit()
           device_client.shutdown()
           raise error

    time.sleep(5.0)


    # Finally, shut down the client
    await device_client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

    # If using Python 3.6 or below, use the following code instead of asyncio.run(main()):
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.close()
```

- save the file as temptest.py
- now run the python file

```
python3 temptest.py
```

- output should be

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspdht11-3.jpg "Logo Title Text 1")

- Now go to Azure cloud portal
- Let configure stream analytics to read and write as parquet for further processing
- Configure input as IoT hub
- Configure output as ADLS gen2 storage which is also used by Synapse analytics spark
- Create the query as 

```
SELECT
    temperature AS temperature,
    humidity as humidity,
    deviceid as deviceserial,
    timecreated as sensortime,
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

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspdht11-4.jpg "Logo Title Text 1")

- Start the stream analytics and let it run
- Now go to Synapse Analytics workspace
- here is where we are going to do data engineering and modelling
- Create a notebook
- Read the parquet data

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspdht11-5.jpg "Logo Title Text 1")