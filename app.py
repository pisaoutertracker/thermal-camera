import os
import time
from flask import Flask, jsonify, request
from flask_restful import Resource, Api

import paho.mqtt.client as mqtt

from thermalcamera import ThermalCamera

# MQTT
broker = "192.168.0.45"
brokerport = 1883
# Flask
app = Flask(__name__)
api = Api(app)
# Global ThermalCamera object
thermal_camera = ThermalCamera(absolute_position=0)


# REST API endpoints
class ImportPosition(Resource):
    def post(self):
        thermal_camera.import_absolute_position()
        return {"status": "success"}, 200


class GetFrameAtRelativeAngle(Resource):
    def get(self):
        args = request.get_json()
        thermal_camera.rotate(args["angle"])
        return thermal_camera.get_frame_as_bytes(), 200


class GetFrameAtAbsoluteAngle(Resource):
    def get(self):
        args = request.get_json()
        thermal_camera.go_to(args["position"])
        return thermal_camera.get_frame_as_bytes(), 200


class Calibrate(Resource):
    def post(self):
        thermal_camera.calibrate()
        return {"status": "success"}, 200


class StartMonitoring(Resource):
    def get(self):
        while True:
            print("Starting monitoring...")
            mqqttclient = mqtt.Client("thermalcam")
            mqqttclient.connect(broker, brokerport)
            mqqttclient.publish(
                "/thermalcamera/camera2/image", thermal_camera.get_frame_as_bytes()
            )
            print("Done.")
            time.sleep(10)


app.add_resource(ImportPosition, "/import-position")
app.add_resource(GetFrameAtRelativeAngle, "/get-frame-relative")
app.add_resource(GetFrameAtAbsoluteAngle, "/get-frame-absolute")
app.add_resource(Calibrate, "/calibrate")
app.add_resource(StartMonitoring, "/start-monitoring")

if __name__ == "__main__":
    app.run(debug=True)
