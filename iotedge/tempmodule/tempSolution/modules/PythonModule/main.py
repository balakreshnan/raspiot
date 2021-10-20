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