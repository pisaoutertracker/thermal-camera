import os
import time
from flask import Flask, Response, jsonify, request
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
        return Response(
            thermal_camera.get_frame_as_bytes(), mimetype="application/octet-stream"
        )


class GetFrameAtAbsoluteAngle(Resource):
    def get(self):
        args = request.get_json()
        thermal_camera.go_to(args["position"])
        return Response(
            thermal_camera.get_frame_as_bytes(), mimetype="application/octet-stream"
        )


class Calibrate(Resource):
    def post(self):
        thermal_camera.calibrate()
        return {"status": "success"}, 200


class StartMonitoring(Resource):
    def get(self):
        while True:
            try:
                print("Starting monitoring...")
                mqqttclient = mqtt.Client("thermalcam")
                mqqttclient.connect(broker, brokerport)
                mqqttclient.publish(
                    "/thermalcamera/camera2/image", thermal_camera.get_frame_as_bytes()
                )
                print("Done.")
                time.sleep(10)
            except KeyboardInterrupt:
                return {"status": "success"}, 200


api.add_resource(ImportPosition, "/import-position")
api.add_resource(GetFrameAtRelativeAngle, "/get-frame-relative")
api.add_resource(GetFrameAtAbsoluteAngle, "/get-frame-absolute")
api.add_resource(Calibrate, "/calibrate")
api.add_resource(StartMonitoring, "/start-monitoring")

if __name__ == "__main__":
    app.run(debug=True)
