import struct
import numpy as np
# import cv2
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1 import make_axes_locatable
import paho.mqtt.client as mqtt

MQTT_SERVER = "192.168.0.45"
MQTT_PATH = "/thermalcamera/+/image/#"

# e.g. /thermalcamera/camera0/image, /thermalcamera/camera1/image, etc.

fig, axs = plt.subplots(2, 2, figsize=(10, 8))
initial_image = np.random.rand(32, 24) * 30 + 10
images = [axs[i, j].imshow(initial_image, cmap="plasma") for i in range(2) for j in range(2)]
im_dict = {f"camera{i}": images[i] for i in range(4)}
cbar = [make_axes_locatable(axs[i, j]).append_axes("right", size="5%", pad=0.05) for i in range(2) for j in range(2)]
cbar = [fig.colorbar(images[i], cax=cbar[i]) for i in range(4)]
titles = [axs[i, j].set_title(f"Camera {i*2+j}") for i in range(2) for j in range(2)]



# # Initialize a list of float as per your data. Below is a random example
# fig, ax = plt.subplots()
# im = ax.imshow(np.random.rand(24, 32) * 30 + 10, cmap="plasma")
# divider = make_axes_locatable(ax)
# cax = divider.append_axes("right", size="5%", pad=0.05)
# plt.colorbar(im, cax=cax)


def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_PATH)


def on_message(client, userdata, msg):
    # get the camera name
    camera_name = msg.topic.split("/")[2]
    # get the image data
    flo_arr = [
        struct.unpack("f", msg.payload[i : i + 4])[0]
        for i in range(0, len(msg.payload), 4)
    ]
    # update the image
    im_dict[camera_name].set_data(np.flip(np.rot90(np.array(flo_arr).reshape(24, 32)), axis=0))
    im_dict[camera_name].set_clim(min(20, min(flo_arr)), max(flo_arr))
    # update the colorbar
#    cbar[int(camera_name[-1])].update_bruteforce(im_dict[camera_name])
    # update the title
    # titles[int(camera_name[-1])].set_text(f"Camera {camera_name[-1]}")
    plt.draw()


# def on_message(client, userdata, msg):
#     global im
#     # more callbacks, etc
#     # Create a file with write byte permission
#     print(msg.payload)
#     print(len(msg.payload))
#     flo_arr = [
#         struct.unpack("f", msg.payload[i : i + 4])[0]
#         for i in range(0, len(msg.payload), 4)
#     ]
#     print(max(flo_arr))
#     if im == "":
#         plt.figure(figsize=(10, 8))
#         im = plt.imshow(
#             np.array(flo_arr).reshape(24, 32), cmap="hot", interpolation="nearest"
#         )
#         plt.colorbar()
#         #    plt.savefig('img.png', dpi = 300)
#         plt.draw()
#     else:
#         im.set_data(np.array(flo_arr).reshape(24, 32))
#         im.set_clim(min(20, min(flo_arr)), max(flo_arr))
#         plt.draw()

#     # plt.show()


# #    img = cv2.imread('img.png')
# #    resized_img = cv2.resize(img, (320,240))
# #    cv2.imwrite('img.png', resized_img)

# # The callback for when the client receives a CONNACK response from the server.


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
