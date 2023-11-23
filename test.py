"""Unit tests for the ThermalCamera class."""
import unittest
from unittest.mock import MagicMock
from thermalcamera import ThermalCamera


class TestThermalCamera(unittest.TestCase):
    def setUp(self):
        self.camera = ThermalCamera()

    def test_initial_absolute_position(self):
        self.assertEqual(self.camera.absolute_position, 0)

    def test_rotate_method(self):
        # Mock the motor kit and rotate method to avoid physical movement
        self.camera.kit = MagicMock()
        self.camera.rotate(90)
        self.assertEqual(self.camera.absolute_position, 90)

    def test_go_to_method(self):
        # Mock the rotate method to avoid physical movement
        self.camera.rotate = MagicMock()
        self.camera.go_to(180)
        self.assertEqual(self.camera.absolute_position, 180)

    def test_export_import_absolute_position(self):
        initial_position = self.camera.absolute_position
        self.camera.export_absolute_position()
        self.camera.absolute_position = 0  # Resetting absolute position
        self.camera.import_absolute_position()
        self.assertEqual(self.camera.absolute_position, initial_position)


if __name__ == "__main__":
    unittest.main()
