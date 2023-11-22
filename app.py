from flask import Flask, jsonify, request
from flask_restful import Resource, Api

from thermalcamera import ThermalCamera

app = Flask(__name__)
api = Api(app)

thermal_camera = ThermalCamera()
class Initiate(Resource):
    def post(self):
        args = request.get_json()
        thermal_camera.absolute_position = args['absolute_position']
        return {'status': 'success'}, 200
    
class GetFrame(Resource):
    def get(self):
        args = request.get_json()
        thermal_camera.rotate(args['angle'])
        return thermal_camera.get_frame_as_bytes(), 200
    
api.add_resource(Initiate, '/initiate')
api.add_resource(GetFrame, '/get_frame')
    
if __name__ == "__main__":
    app.run(debug=True)
