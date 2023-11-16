from flask import Flask, jsonify

from thermalcamera import ThermalCamera

app = Flask(__name__)

thermal_camera = ThermalCamera(0)


@app.route("/frame")
def some_wrap(func):
    def wrapper(*args, **kwargs):
        return jsonify(func(*args, **kwargs))

    return wrapper


if __name__ == "__main__":
    app.run(debug=True)
