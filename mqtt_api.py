import time
import struct
import json
import base64
import logging
import threading
import paho.mqtt.client as mqtt
import numpy as np

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
        self.monitoring = False
        self.streaming = False
        self.run_thread = None
        self.monitor_thread = None
        self.stream_thread = None
        self.client = None

        # Temporary code for creating a dataset for stitching
        self.stitching_data = {}

    def publish_state(self, client):
        try:
            if self.thermal_camera is not None:
                state = {
                    "running": int(self.running),
                    "position": self.thermal_camera.absolute_position,
                    "switch_state": self.thermal_camera.get_switch_state(),
                    "streaming": int(self.streaming),
                }
                client.publish(self.TOPIC_STATE, json.dumps(state), retain=True)
        except Exception as e:
            logging.error(f"Error when publishing the state: {e}")

    def connect_mqtt(self, broker, brokerport):

        def on_connect(client, userdata, flags, rc):
            logging.info(f"Connected with result code {rc}")
            client.subscribe(self.TOPIC_CMD)
            client.subscribe(self.TOPIC_STATE)

        def on_message(client, userdata, msg):
            if msg.topic.startswith(self.TOPIC_CMD.replace("#", "")):
                try:
                    command = msg.topic.split("/")[-1]
                    payload = json.loads(msg.payload)
                    logging.info(f"Received command {command} with payload {payload}")
                    self.command_handlers[command](client, payload)
                except Exception as e:
                    logging.error(f"Error when executing command {command}: {e}")
            elif msg.topic.startswith(self.TOPIC_STATE):
                pass

        def on_disconnect(client, userdata, rc):
            if self.thermal_camera is not None:
                self.thermal_camera.export_absolute_position()
            logging.info(f"Disconnected with result code {rc}")

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "thermalcam")
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        client.connect(broker, brokerport)
        return client

    def extract_params(self, payload, param_specs):
        result = {}
        for param, spec in param_specs.items():
            param_type = spec.get("type", str)
            param_default = spec.get("default", None)
            param_optional = spec.get("optional", False)
            try:
                param_value = payload[param]
            except KeyError:
                if param_optional:
                    param_value = param_default
                else:
                    logger.error(f"Missing required parameter {param}")
            if param_value is None:
                result[param] = None
                continue
            try:
                result[param] = param_type(param_value)
            except Exception:
                logging.error(f"Error when converting {param} to {param_type}, using default value {param_default}")
                result[param] = param_default
        return result

    def rotate(self, client, payload):
        spec = {
            "angle": {"type": float},
            "direction": {"type": str, "default": "fw", "optional": True},
        }
        params = self.extract_params(payload, spec)
        self.thermal_camera.rotate(**params)

    def go_to(self, client, payload):
        spec = {
            "position": {"type": float},
        }
        params = self.extract_params(payload, spec)
        # self.stop_monitor_stream_threads()
        self.thermal_camera.go_to(**params)
        # self.start_monitor_stream_threads()

    def calibrate(self, client, payload):
        spec = {
            "prudence": {"type": float, "default": 90, "optional": True},
            "direction": {"type": str, "default": "bw", "optional": True},
        }
        params = self.extract_params(payload, spec)
        self.thermal_camera.calibrate(**params)

    def get_switch_state(self, client, payload):
        self.thermal_camera.get_switch_state()

    def set_absolute_position(self, client, payload):
        spec = {
            "value": {"type": float},
        }
        params = self.extract_params(payload, spec)
        self.thermal_camera.absolute_position = params["value"]

    def export_absolute_position(self, client, payload):
        self.thermal_camera.export_absolute_position()

    def import_absolute_position(self, client, payload):
        self.thermal_camera.import_absolute_position()

    def get_frame(self, client, payload):
        spec = {
            "camera": {"type": str},
        }
        params = self.extract_params(payload, spec)
        camera = params["camera"]

        enc_image = base64.b64encode(self.thermal_camera.get_frame_as_bytes(camera)).decode("utf-8")
        result = {
            "image": enc_image,
            "position": self.thermal_camera.absolute_position,
        }

        # Temporary code for creating a dataset for stitching
        position = result["position"]
        image = base64.b64decode(result["image"])
        image = [struct.unpack("f", image[i : i + 4])[0] for i in range(0, len(image), 4)]
        image = np.flip(np.rot90(np.array(image).reshape(24, 32)), axis=0).tolist()
        if position not in self.stitching_data:
            self.stitching_data[position] = {}
        if camera not in self.stitching_data[position]:
            self.stitching_data[position][camera] = []
        self.stitching_data[position][camera].append(image)

        min_temp = float(np.min(image))
        max_temp = float(np.max(image))
        low_temp = float(np.percentile(image,0.05))
        high_temp = float(np.percentile(image,0.95))
        result["min_temperature"] = min_temp
        result["max_temperature"] = max_temp
        result["percentile05_temperature"] = low_temp
        result["percentile95_temperature"] = high_temp

        client.publish(f"{self.TOPIC_ROOT}/{camera}", json.dumps(result))

    def get_frames(self, client, payload):
        for camera in self.thermal_camera.mlx_dict:
            self.get_frame(client, {"camera": camera})

    def init(self, client, payload):
        spec = {
            "absolute_position": {"type": float, "default": None, "optional": True},
        }
        params = self.extract_params(payload, spec)
        self.thermal_camera = ThermalCamera(**params)

    def release(self, client, payload):
        self.thermal_camera.release()

    def _run(self, client, payload):
        spec = {
            "offset": {"type": float, "default": 0, "optional": True},
            "step": {"type": float, "default": 5, "optional": True},
            "wait": {"type": float, "default": 0.1, "optional": True},
            "direction": {"type": str, "default": "fw", "optional": True},
            "continuous": {"type": bool, "default": True, "optional": True},
        }
        params = self.extract_params(payload, spec)
        offset = params["offset"]
        step = params["step"]
        wait = params["wait"]
        direction = params["direction"]
        continuous = params["continuous"]
        print(offset)
        self.thermal_camera.go_to(offset)
        while True:
            if self.running is False:
                logging.info("Stopping the run loop")
                # Temporary code for creating a dataset for stitching
                if self.stitching_data is not None:
                    with open("stitching_data.json", "w") as f:
                        json.dump(self.stitching_data, f)
                break
            print("Pos ", self.thermal_camera.absolute_position)
            if self.thermal_camera.absolute_position > 360 and direction == "fw" :
                direction = "bw"
            if self.thermal_camera.absolute_position < 0 and direction == "bw" :
                direction = "fw"
#           if ( ((380 - self.thermal_camera.absolute_position) < 20) or (
 #              (-20 - self.thermal_camera.absolute_position) > -20
#           ):  # ! Partially verified
#           print("cond1 ", 380 - self.thermal_camera.absolute_position) 
#           print("cond2 ", -20 - self.thermal_camera.absolute_position) 
#               if continuous is False:
#                   logging.info("Stopping the run loop")
#                   self.running = False
#                   break
#               logging.info("Switch state reached, inverting direction")
#               direction = "fw" if direction == "bw" else "bw"
            print("current direction ", direction)
            self.thermal_camera.rotate(step, direction=direction)
            self.get_frames(client, payload)
            time.sleep(wait)

    def run(self, client, payload):
        try:
            if self.running:
                self.stop(client, payload)
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

    def _monitor_state_loop(self, client):
        logging.info("Start monitoring state")
        while self.monitoring:
            self.publish_state(client)
            time.sleep(1)

    def monitor_state(self, client):
        self.monitoring = True
        logging.info("Start monitoring state of the system in a separate thread")
        self.monitor_thread = threading.Thread(target=self._monitor_state_loop, args=(client,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _send_images_loop(self, client):
        while self.streaming:
            try:
                if self.running:
                    continue
                else:
                    self.get_frames(client, {})
            except Exception:
                pass

    def send_images(self, client):
        self.streaming = True
        logging.info("Start images streaming loop in a separate thread")
        self.stream_thread = threading.Thread(target=self._send_images_loop, args=(client,))
        self.stream_thread.daemon = True
        self.stream_thread.start()

    def stop_threads(self):
        self.monitoring = False
        self.streaming = False
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=5.0)
        if self.run_thread and self.run_thread.is_alive():
            self.run_thread.join(timeout=5.0)
        logging.info("Threads stopped")

    def stop_monitor_stream_threads(self):
        self.monitoring = False
        self.streaming = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=5.0)
        logging.info("Monitoring and streaming threads stopped")

    def start_monitor_stream_threads(self):
        self.send_images(self.client)
        self.monitor_state(self.client)


if __name__ == "__main__":
    import sys
    import signal
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", type=str, default="192.168.0.45", help="MQTT broker address")
    parser.add_argument("--brokerport", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--loglevel", "-log", type=str, default="WARNING", help="Logging level")
    args = parser.parse_args()

    logging.getLogger().setLevel(args.loglevel)

    api = ThermalCameraAPI()
    client = api.connect_mqtt(args.broker, args.brokerport)

    def signal_handler(sig, frame):
        api.stop_threads()
        client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        client.loop_start()
        api.monitor_state(client)
        api.send_images(client)
        while True:
            time.sleep(0.1)
    except Exception as e:
        logging.error(f"Error in the main loop: {e}")
    finally:
        api.stop_threads()
        client.disconnect()
