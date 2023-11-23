"""Thermal camera system basic operations."""
import time
import struct
import board
import busio

import numpy as np

import adafruit_mlx90640
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit

import RPi.GPIO as GPIO


class ThermalCamera:
    """Class for the Thermal Camera system."""

    def __init__(self, absolute_position=None):
        # Thermal camera setup
        self.mlx = adafruit_mlx90640.MLX90640(
            busio.I2C(board.SCL, board.SDA, frequency=int(1e6))
        )
        self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
        # Stepper motor setup
        self.kit = MotorKit(i2c=board.I2C())
        # Absolute position of the stepper motor in degrees
        if absolute_position is None:
            print("No absolute position given, using last position.")
            self._absolute_position = self.import_absolute_position()
        else:
            self._absolute_position = absolute_position

    @property
    def absolute_position(self):
        """Get the absolute position of the stepper motor."""
        return self._absolute_position

    @absolute_position.setter
    def absolute_position(self, value):
        """Set the absolute position of the stepper motor."""
        if value < 0 or value > 360:
            raise ValueError("Absolute position must be between 0 and 360 degrees.")
        self._absolute_position = value

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
        self.absolute_position = (self.absolute_position + angle) % 360
        print("Done.")

    def go_to(self, position, *args, **kwargs):
        """Go to a given position."""
        print(f"Going to position {position}...")
        self.rotate(position - self.absolute_position, *args, **kwargs)
        print("Done.")

    def export_absolute_position(self):
        """Export the absolute position of the stepper motor."""
        with open("absolute_position.csv", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{self.absolute_position}\n")
        print("Exported absolute position.")

    def import_absolute_position(self):
        """Import the absolute position of the stepper motor."""
        with open("absolute_position.csv", "r") as f:
            lines = f.readlines()
        self.absolute_position = float(lines[-1].split(",")[1])
        print("Imported absolute position.")

    def _calibrate(self):  # ! Still under development
        """Calibrate the stepper motor."""
        print("Calibrating stepper motor...")
        # Set up the GPIO pins
        GPIO.setmode(GPIO.BCM)
        pin = 18  # ! Update with the correct pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Calibrate the stepper motor
        while True:
            state = GPIO.input(pin)
            if state == GPIO.HIGH:
                self.absolute_position = 0
                print("Sensor found: absolute position set to 0 degrees.")
                GPIO.cleanup()
                break
            else:
                self.kit.stepper1.onestep()
                time.sleep(0.01)
