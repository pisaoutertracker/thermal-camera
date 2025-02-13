"""Thermal camera system basic operations."""

import os
import time
import logging
import struct
import board
import busio
import numpy as np
from matplotlib import pyplot as plt
import adafruit_mlx90640
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit
import RPi.GPIO as GPIO

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class ThermalCamera:
    """Class for the Thermal Camera system.

    Parameters
    ----------
    absolute_position : float
        Absolute position of the stepper motor in degrees.

    Attributes
    ----------
    mlx_dict : dict
        Dictionary containing the thermal cameras.
    kit : adafruit_motorkit.MotorKit
        MotorKit object.
    absolute_position : float
        Absolute position of the stepper motor in degrees.
    pin : int
        GPIO pin to read the switch.
    """

    def __init__(self, absolute_position=None):
        # Thermal camera setup
        # ? Put the addresses in a config file
        self._addresses = [
            0x30,
            0x31,
            0x32,
            0x33,
        ]  # , 0x34, 0x35, 0x36]  # ! Update with the correct addresses
        self.mlx_dict = {
            f"camera-{i}": adafruit_mlx90640.MLX90640(
                busio.I2C(board.SCL, board.SDA, frequency=int(1e6)), address=addr
            )
            for i, addr in enumerate(self._addresses)
        }
        for camera in self.mlx_dict.values():
            camera.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_1_HZ
        # Stepper motor setup
        self.kit = MotorKit(i2c=board.I2C())
        # TODO: pulse width customization
        # Absolute position of the stepper motor in degrees
        # If no absolute position is given, try to import it from a file
        if absolute_position is None:
            if os.path.exists("absolute_position.csv"):
                logging.info("No absolute position given, using last position.")
                self.import_absolute_position()
            else:
                logging.error(
                    "No absolute position given and no absolute position file found."
                )
                raise ValueError
        else:
            self._absolute_position = absolute_position
        # Set up the GPIO pins to read the switch
        GPIO.setmode(GPIO.BCM)
        self.pin = 23
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    @property
    def addresses(self):
        return self._addresses

    @property
    def absolute_position(self):
        """Get the absolute position of the stepper motor."""
        return self._absolute_position

    @absolute_position.setter
    def absolute_position(self, value):
        """Set the absolute position of the stepper motor."""
        if value < 0 or value > 360:
            logging.error("Absolute position must be between 0 and 360 degrees.")
            raise ValueError
        self._absolute_position = value

    def get_frame(self, camera):
        """Get a frame from the thermal camera.

        Parameters
        ----------
        camera : str
            Name of the camera to get the frame from.

        Returns
        -------
        buffer : numpy.ndarray
            Array containing the frame.
        """
        buffer = np.zeros((24 * 32,))
        self.mlx_dict[camera].getFrame(buffer)
        return buffer

    def get_frame_as_bytes(self, camera):
        """Get a frame from the thermal camera as bytes.

        Parameters
        ----------
        camera : str
            Name of the camera to get the frame from.

        Returns
        -------
        buffer : bytearray
            Array containing the frame.
        """
        buffer = self.get_frame(camera=camera)
        return bytearray(struct.pack("f" * len(buffer), *buffer))

    def get_frame_as_image(self, camera):
        """Get a frame from the thermal camera as an image.

        Parameters
        ----------
        camera : str
            Name of the camera to get the frame from.

        Returns
        -------
        buffer : numpy.ndarray
            Array containing the frame.
        """
        buffer = self.get_frame(camera=camera)
        return np.reshape(buffer, (24, 32))

    def show_frame(self, camera):
        """Plot a frame from the thermal camera.

        Parameters
        ----------
        camera : str
            Name of the camera to get the frame from.
        """
        buffer = self.get_frame_as_image(camera=camera)
        plt.figure(figsize=(10, 8))
        plt.imshow(buffer, cmap="hot", interpolation="nearest")
        plt.colorbar()
        plt.show()

    def show_frame_loop(self, camera):
        """Plot a frame from the thermal camera in a loop.

        Parameters
        ----------
        camera : str
            Name of the camera to get the frame from.
        """
        plt.ion()
        fig, ax = plt.subplots(figsize=(10, 8))
        buffer = self.get_frame_as_image(camera=camera)
        therm = ax.imshow(buffer, cmap="hot", interpolation="nearest")
        cbar = fig.colorbar(therm)
        cbar.set_label("Temperature")
        while True:
            buffer = self.get_frame_as_image(camera=camera)
            therm.set_array(buffer)
            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(1)

    def get_switch_state(self):
        """Get the state of the switch.

        Returns
        -------
        state : bool
            State of the switch.
        """
        state = GPIO.input(self.pin)
        if state == GPIO.HIGH:
            return True
        else:
            return False

    def rotate(self, angle, *args, **kwargs):
        """Rotate the stepper motor by a given angle.

        Parameters
        ----------
        angle : float
            Angle to rotate the stepper motor by.
        """
        for _ in range(int(angle / 1.8)):
            self.kit.stepper1.onestep(*args, **kwargs)
            # Update the absolute position considering the direction of rotation
            # ! Microstepping is not considered here
            if "direction" in kwargs and kwargs["direction"] == stepper.BACKWARD:
                self.absolute_position = (
                    self.absolute_position - 1.8
                ) % 360  # ? Is this correct?
            else:
                self.absolute_position = (self.absolute_position + 1.8) % 360
            # Check if the switch is pressed
            state = self.get_switch_state()
            if state and self.absolute_position != 0:
                logging.error("Sensor found but absolute position is not 0 degrees.")
                raise ValueError
            # time.sleep(0.05)
        logging.info(f"Stepper motor rotated by {angle} degrees.")

    def go_to(self, position, *args, **kwargs):
        """Go to a given position.

        Parameters
        ----------
        position : float
            Position to go to.
        """
        self.rotate(position - self.absolute_position, *args, **kwargs)
        logging.info(f"Stepper motor moved to {position} degrees.")

    def export_absolute_position(self):
        """Export the absolute position of the stepper motor."""
        with open("absolute_position.csv", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{self.absolute_position}\n")
        logging.info("Exported absolute position.")

    def import_absolute_position(self):
        """Import the absolute position of the stepper motor."""
        with open("absolute_position.csv", "r") as f:
            lines = f.readlines()
        self.absolute_position = float(lines[-1].split(",")[1])
        logging.info("Imported absolute position.")

    def calibrate(self):  # ! Still under development
        """Calibrate the stepper motor."""
        logging.info("Starting calibration.")
        while True:
            if self.get_switch_state():
                self.absolute_position = 0
                logging.info("Sensor found: absolute position set to 0 degrees.")
                break
            else:
                self.kit.stepper1.onestep(direction=stepper.BACKWARD)
                time.sleep(0.01)
