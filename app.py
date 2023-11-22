from flask import Flask, jsonify, request
from flask_restful import Resource, Api

from thermalcamera import ThermalCamera

app = Flask(__name__)
api = Api(app)

class Initiate(Resource):
    def post(self):
        args = request.get_json()
        thermal_camera = ThermalCamera(**args)
        thermal_camera.initiate()
        return jsonify({'status': 'success'}), 200
    
api.add_resource(Initiate, '/initiate')
    
if __name__ == "__main__":
    app.run(debug=True)
