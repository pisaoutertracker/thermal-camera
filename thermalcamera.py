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

    STEP_STYLE = stepper.INTERLEAVE
    STEP_VALUE = 0.9 if STEP_STYLE == stepper.INTERLEAVE else 1.8

    def __init__(self, absolute_position=None):
        # Thermal camera setup
        self._addresses = [
            0x30,
            0x31,
            0x32,
            0x33,
        ]
        self.mlx_dict = {
            f"camera{i}": adafruit_mlx90640.MLX90640(busio.I2C(board.SCL, board.SDA, frequency=int(1e6)), address=addr)
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
                logging.error("No absolute position given and no absolute position file found.")
                self._absolute_position = 0.0
        else:
            self._absolute_position = absolute_position
        # Set up the GPIO pins to read the switch
        GPIO.setmode(GPIO.BCM)
        self.pin = 23
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def address(self, camera):
        """Get the address of a thermal camera.

        Parameters
        ----------
        camera : str
            Name of the camera.

        Returns
        -------
        address : int
            Address of the camera.
        """
        return self._addresses[list(self.mlx_dict.keys()).index(camera)]

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

    def rotate(self, angle, direction="fw"):
        """Rotate the stepper motor by a given angle.

        Parameters
        ----------
        angle : float
            Angle to rotate the stepper motor by.
        """
        if direction not in ["fw", "bw"]:
            logging.error("Direction must be either 'fw' or 'bw'.")
            raise ValueError
        direction = stepper.FORWARD if direction == "fw" else stepper.BACKWARD

        # Round to the closest multiple of the step value
        nsteps = round(angle / self.STEP_VALUE)
        for _ in range(abs(nsteps)):
            self.kit.stepper1.onestep(style=self.STEP_STYLE, direction=direction)
            # Update the absolute position considering the direction of rotation
            if direction == stepper.BACKWARD:
                self.absolute_position = (self.absolute_position - self.STEP_VALUE) % 360  # ? Is this correct?
            else:
                self.absolute_position = (self.absolute_position + self.STEP_VALUE) % 360
            # Check if the switch is pressed
            state = self.get_switch_state()
            if state:
                logging.warning("Sensor found")
            time.sleep(0.01)
        logging.info(f"Stepper motor rotated by {angle} degrees.")

    def go_to(self, position):
        """Go to a given position.

        Parameters
        ----------
        position : float
            Position to go to.
        """
        if position >= self.absolute_position:
            direction = "fw"
        elif position < self.absolute_position:
            direction = "bw"
        self.rotate(abs(position - self.absolute_position), direction)
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

    def calibrate(self, prudence=180, direction="bw"):
        """Calibrate the stepper motor.

        Parameters
        ----------
        prudence : float
            Maximum angle to rotate the stepper motor.
        direction : str
            Direction to rotate the stepper motor.
        """
        if direction not in ["fw", "bw"]:
            logging.error("Direction must be either 'fw' or 'bw'.")
            raise ValueError
        direction = stepper.FORWARD if direction == "fw" else stepper.BACKWARD
        update_pos_func = lambda x: (
            (self.absolute_position + x) % 360 if direction == stepper.FORWARD else (self.absolute_position - x) % 360
        )
        logging.info("Starting calibration.")
        total_steps = round(prudence / self.STEP_VALUE)
        steps = 0
        while True:
            if self.get_switch_state():
                self.absolute_position = 0
                logging.info("Sensor found: absolute position set to 0 degrees.")
                break
            else:
                if steps >= total_steps:
                    logging.warning("Sensor not found within the prudence angle.")
                    break
                else:
                    self.kit.stepper1.onestep(direction=direction, style=self.STEP_STYLE)
                    self.absolute_position = update_pos_func(self.STEP_VALUE)
                    steps += 1
                    time.sleep(0.01)

    def release(self):
        """Release the stepper motor."""
        self.kit.stepper1.release()
        logging.info("Stepper motor released.")
