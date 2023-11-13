import time
import struct
import numpy as np
import matplotlib.pyplot as plt
import board
import busio
import adafruit_mlx90640
import paho.mqtt.client as mqtt

# Thermal camera
i2c = busio.I2C(board.SCL, board.SDA, frequency=int(1e6))
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
buffer = np.zeros((24 * 32,))

# MQTT
broker = "192.168.0.45"
brokerport = 1883

while True:
    try:
        print("Getting values...")
        mlx.getFrame(buffer)
        ba = bytearray(struct.pack("f" * len(buffer), *buffer))
        mqqttclient = mqtt.Client("thermalcam")
        mqqttclient.connect(broker, brokerport)
        ret = mqqttclient.publish("/thermalcamera/camera2/image", ba)
        print(ret)
        print("Done")
        time.sleep(10)
    except ValueError:
        continue
