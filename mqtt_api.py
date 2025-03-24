import time
import json
import logging
import threading
import paho.mqtt.client as mqtt

from thermalcamera import ThermalCamera

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ThermalCameraAPI:

    TOPIC_CMD = "/thermalcamera/cmd/#"
    TOPIC_ROOT = "/thermalcamera"
    TOPIC_STATE = "/thermalcamera/state"

    def __init__(self):
        self.thermal_camera = None
        self.command_handlers = {
            "get_frame": self.get_frame,
            "get_switch_state": self.get_switch_state,
            "rotate": self.rotate,
            "go_to": self.go_to,
            "calibrate": self.calibrate,
            "set_absolute_position": self.set_absolute_position,
            "export_absolute_position": self.export_absolute_position,
            "import_absolute_position": self.import_absolute_position,
            "get_frames": self.get_frames,
            "init": self.init,
            "release": self.release,
            "run": self.run,
            "stop": self.stop,
        }
        self.running = False

    def publish_state(self, client):
        try:
            if self.thermal_camera is not None:
                state = {
                    "running": int(self.running),
                    "position": self.thermal_camera.absolute_position,
                    "switch_state": self.thermal_camera.get_switch_state(),
                }
                client.publish(self.TOPIC_POS, json.dumps(state), retain=True)
        except Exception as e:
            logging.error(f"Error when publishing the state: {e}")

    def connect_mqtt(self, broker, brokerport):

        def on_connect(client, userdata, flags, rc):
            client.subscribe(self.TOPIC_CMD)
            client.subscribe(self.TOPIC_STATE)

        def on_message(client, userdata, msg):
            if msg.topic == self.TOPIC_CMD:
                command = msg.topic.split("/")[-1]
                payload = json.loads(msg.payload)
                self.command_handlers[command](client, payload)
            elif msg.topic == self.TOPIC_STATE:
                pass

        def on_disconnect(client, userdata, rc):
            if self.thermal_camera is not None:
                self.thermal_camera.export_absolute_position()
            logging.error(f"Disconnected with result code {rc}")

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "thermalcam")
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        client.connect(broker, brokerport)
        return client

    def rotate(self, client, payload):
        self.thermal_camera.rotate(payload)

    def go_to(self, client, payload):
        self.thermal_camera.go_to(payload)

    def calibrate(self, client, payload):
        self.thermal_camera.calibrate(payload)

    def get_switch_state(self, client, payload):
        self.thermal_camera.get_switch_state()

    def set_absolute_position(self, client, payload):
        value = payload.get("value")
        self.thermal_camera.absolute_position = value

    def export_absolute_position(self, client, payload):
        self.thermal_camera.export_absolute_position()

    def import_absolute_position(self, client, payload):
        self.thermal_camera.import_absolute_position()

    def get_frame(self, client, payload):
        frame = self.thermal_camera.get_frame_as_bytes(payload)
        try:
            camera = payload.get("camera")
            camera_name = camera.replace("-", "")
            address = self.thermal_camera.addresses[self.thermal_camera.mlx_dict.index(camera)]
            client.publish(f"/thermalcamera/{camera_name}/image/{address}", frame)
            client.publish(f"/thermalcamera/{camera_name}/position", self.thermal_camera.absolute_position)
        except ValueError:
            pass

    def get_frames(self, client, payload):
        for camera in self.thermal_camera.mlx_dict:
            self.get_frame(client, {"camera": camera})

    def init(self, client, payload):
        self.thermal_camera = ThermalCamera(payload)

    def release(self, client, payload):
        self.thermal_camera.release()

    def _run(self, client, payload):
        if self.thermal_camera is None:
            absolute_position = payload.get("absolute_position", None)
            self.thermal_camera = ThermalCamera(absolute_position=absolute_position)
        prudence = payload.get("prudence", 180)
        offset = payload.get("offset", 0)
        step = payload.get("step", 5)
        wait = payload.get("wait", 0.1)
        self.thermal_camera.calibrate(prudence=prudence)
        self.thermal_camera.go_to(offset)
        while self.running:
            self.thermal_camera.rotate(step)
            self.get_frames(client, payload)
            time.sleep(wait)

    def run(self, client, payload):
        try:
            if self.running:
                self.stop()
            self.running = True
            self.run_thread = threading.Thread(target=self._run, args=(client, payload))
            self.run_thread.daemon = True
            self.run_thread.start()
        except Exception as e:
            self.running = False
            logging.error(f"Error when running the thermal camera: {e}")

    def stop(self, client, payload):
        if self.running:
            self.running = False
            if self.run_thread and self.run_thread.is_alive():
                self.run_thread.join(timeout=5.0)
            self.thermal_camera.export_absolute_position()

    def monitor_state(self, client):
        client.loop_start()
        while True:
            self.publish_state(client)
            time.sleep(1)

    # NOTE: This should be keep separate from the rest of the API
    # (existing mqtt_send and receive scripts)
    def send_images(self, client):
        client.loop_start()
        while True:
            for camera in self.thermal_camera.mlx_dict:
                try:
                    b_array = self.thermal_camera.get_frame_as_bytes(camera)
                    camera_name = camera.replace("-", "")
                    address = self.thermal_camera.addresses[self.thermal_camera.mlx_dict.index(camera)]
                    client.publish(f"/thermalcamera/{camera_name}/image/{address}", b_array)
                    time.sleep(0.1)
                except ValueError:
                    continue


broker = "192.168.0.45"
brokerport = 1883


if __name__ == "__main__":
    api = ThermalCameraAPI()
    client = api.connect_mqtt(broker, brokerport)
    api.monitor_state(client)
