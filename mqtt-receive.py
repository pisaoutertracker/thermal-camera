import struct
import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1 import make_axes_locatable
import paho.mqtt.client as mqtt

MQTT_SERVER = "pccmslab1"
MQTT_PATH = "/thermalcam"

# Initialize a list of float as per your data. Below is a random example
fig, ax = plt.subplots()
im = ax.imshow(np.random.rand(24, 32) * 30 + 10, cmap="plasma")
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(im, cax=cax)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)
    # The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    global im
    # more callbacks, etc
    # Create a file with write byte permission
    print(msg.payload)
    print(len(msg.payload))
    flo_arr = [
        struct.unpack("f", msg.payload[i : i + 4])[0]
        for i in range(0, len(msg.payload), 4)
    ]
    print(max(flo_arr))
    if im == "":
        plt.figure(figsize=(10, 8))
        im = plt.imshow(
            np.array(flo_arr).reshape(24, 32), cmap="hot", interpolation="nearest"
        )
        plt.colorbar()
        #    plt.savefig('img.png', dpi = 300)
        plt.draw()
    else:
        im.set_data(np.array(flo_arr).reshape(24, 32))
        im.set_clim(min(20, min(flo_arr)), max(flo_arr))
        plt.draw()

    # plt.show()


#    img = cv2.imread('img.png')
#    resized_img = cv2.resize(img, (320,240))
#    cv2.imwrite('img.png', resized_img)

# The callback for when the client receives a CONNACK response from the server.


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.loop_forever()
client.loop_start()
plt.show()
