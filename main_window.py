import sys
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a button
        self.button = QPushButton("Perform API Action", self)
        self.button.clicked.connect(self.call_api)
        self.setCentralWidget(self.button)

    def call_api(self):
        # Example: Sending a GET request to your Flask API endpoint
        url = "http://0.0.0.0:5004/start-monitoring"
        response = requests.get(url)

        if response.status_code == 200:
            print("API request successful")
            # Handle the API response data as needed
        else:
            print("API request failed")


def run_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_gui()
