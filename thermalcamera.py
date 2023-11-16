import time
import struct
import board
import busio

import numpy as np

import adafruit_mlx90640
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit


class ThermalCamera:
    """Class for the Thermal Camera system."""

    def __init__(self, absolute_position):
        # Thermal camera setup
        self.mlx = adafruit_mlx90640.MLX90640(
            busio.I2C(board.SCL, board.SDA, frequency=int(1e6))
        )
        self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
        # Stepper motor setup
        self.kit = MotorKit(i2c=board.I2C())
        self._absolute_position = (
            absolute_position  # Absolute position of the stepper motor in degrees
        )

    def get_frame(self):
        """Get a frame from the thermal camera."""
        buffer = np.zeros((24 * 32,))
        self.mlx.getFrame(buffer)
        return buffer

    def get_frame_as_bytes(self):
        """Get a frame from the thermal camera as bytes."""
        buffer = self.get_frame()
        return bytearray(struct.pack("f" * len(buffer), *buffer))

    def get_frame_as_image(self):
        """Get a frame from the thermal camera as an image."""
        buffer = self.get_frame()
        return np.reshape(buffer, (24, 32))

    def rotate(self, angle, *args, **kwargs):
        """Rotate the stepper motor by a given angle."""
        print(f"Rotating stepper motor by {angle} degrees...")
        for i in range(int(angle / 1.8)):
            self.kit.stepper1.onestep(*args, **kwargs)
            time.sleep(0.01)
        self._absolute_position += angle
        print("Done.")

    @property
    def absolute_position(self):
        """Get the absolute position of the stepper motor."""
        return self._absolute_position

    @absolute_position.setter
    def absolute_position(self, value):
        """Set the absolute position of the stepper motor."""
        self._absolute_position = value

    def _export_absolute_position(self):
        """Export the absolute position of the stepper motor."""
        with open("absolute_position.txt", "w") as f:
            f.write(str(self.absolute_position))
