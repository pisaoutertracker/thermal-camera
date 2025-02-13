import time
import struct
import numpy as np
import matplotlib.pyplot as plt
import board
import busio
import adafruit_mlx90640

import paho.mqtt.client as mqtt

from thermalcamera import ThermalCamera

# MQTT
broker = "192.168.0.45"
brokerport = 1883

thermal_camera = ThermalCamera()

while True:
    for i, camera in enumerate(thermal_camera.mlx_dict):
        try:
            b_array = thermal_camera.get_frame_as_bytes(camera)
            mqqttclient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,"thermalcam")
            mqqttclient.connect(broker, brokerport)
            camera_name = camera.replace("-", "")
            address = thermal_camera.addresses[i]
            ret = mqqttclient.publish(f"/thermalcamera/{camera_name}/image/{address}", b_array)
            # print(f"/thermalcamera/{camera_name}/image/{address}")
            # print(ret)
            # print("Done")
            time.sleep(0.1)
        except ValueError:
            continue
