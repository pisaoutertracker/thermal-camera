"""Unit tests for the ThermalCamera class."""
import unittest
from unittest.mock import MagicMock
import numpy as np
from thermalcamera import ThermalCamera


class TestThermalCamera(unittest.TestCase):
    def setUp(self):
        self.camera = ThermalCamera(absolute_position=0)

    def test_initial_absolute_position(self):
        self.assertEqual(self.camera.absolute_position, 0)

    def test_rotate_method(self):
        self.camera.kit = MagicMock()
        self.camera.rotate(90)
        self.assertEqual(self.camera.absolute_position, 90)

    def test_go_to_method(self):
        self.camera.go_to(180)
        self.assertEqual(self.camera.absolute_position, 180)

    def test_export_import_absolute_position(self):
        initial_position = self.camera.absolute_position
        self.camera.export_absolute_position()
        self.camera.absolute_position = 0  # Resetting absolute position
        self.camera.import_absolute_position()
        self.assertEqual(self.camera.absolute_position, initial_position)

    def test_get_frame(self):
        frame = self.camera.get_frame(camera="camera-0")
        self.assertIsInstance(frame, type(np.array([])))
        self.assertEqual(len(frame), 24 * 32)

    def test_get_frame_as_bytes(self):
        frame_bytes = self.camera.get_frame_as_bytes(camera="camera-0")
        self.assertIsInstance(frame_bytes, bytearray)
        # Calculate expected length based on the length of the frame (floats * 4 bytes)
        expected_length = 24 * 32 * 4
        self.assertEqual(len(frame_bytes), expected_length)

    def test_get_frame_as_image(self):
        frame_image = self.camera.get_frame_as_image(camera="camera-0")
        self.assertIsInstance(frame_image, type(np.array([])))
        self.assertEqual(frame_image.shape, (24, 32))

    def test_get_switch_state(self):
        switch_state = self.camera.get_switch_state()
        self.assertIsInstance(switch_state, bool)


if __name__ == "__main__":
    unittest.main()
