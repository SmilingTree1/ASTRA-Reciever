import sys, os, time, random, threading
from queue import Queue
from receiver import LoraReceiver
from MapDisplay import  LiveMapDisplay, LiveKmlRoute
from PlotDisplay import TwoSubplotCanvas

import folium
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QSplitter, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl,Qt

# Queue for safely passing data from thread to the main plotter

data_queue = Queue()
map_queue = Queue()
start_time = time.time()

# Starting coordinatespip 
glo_lat, glo_lon = 47.6162, -122.03557
#34.65690, -86.67186  # Huntsville, A

mapfile = "FF.html"

# ======================================================
# Main window with Folium + plots
# ======================================================

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.mapDisplay = LiveMapDisplay()
        

        self.setWindowTitle("Live Tracking")
        # Splitter so user can resize map / plots
        splitter = QSplitter(Qt.Horizontal)

        # --- Two-subplot Matplotlib widget ---
        self.plots = TwoSubplotCanvas(data_queue, map_queue)
        splitter.addWidget(self.plots)

        # --- Folium map widget ---
        self.web = QWebEngineView()
        splitter.addWidget(self.web)

        # Initial map display
        self.mapDisplay.update(glo_lat, glo_lon)
        path = os.path.abspath(mapfile)
        self.web.setUrl(QUrl.fromLocalFile(path))

        splitter.setSizes([800, 600])

        controls_layout = QHBoxLayout()
        self.play_pause_button = QPushButton("Pause")
        self.play_pause_button.setToolTip("Pause/Resume live plot updates")
        self.play_pause_button.clicked.connect(self.toggle_plot)
        controls_layout.addWidget(self.play_pause_button)

        layout = QHBoxLayout()
        layout.addLayout(controls_layout)
        layout.addWidget(splitter)

                # remove all margins and spacing so graph uses maximum space
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)

        # make splitter take the remaining space
        layout.setStretch(0, 0)  # controls row
        layout.setStretch(1, 1)  # splitter expands
        
        self.setLayout(layout)

        # Timers
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.plots.update_plot)
        self.plot_timer.start(2000)

        self.map_timer = QTimer()
        self.map_timer.timeout.connect(self.map_update)
        self.map_timer.start(5000)

    def toggle_plot(self):
        """Toggle the plot timer (play/pause)."""
        if self.plot_timer.isActive():
            self.plot_timer.stop()
            self.play_pause_button.setText("Play")
        else:
            self.plot_timer.start(1000)
            self.play_pause_button.setText("Pause")

    def map_update(self):
        while not map_queue.empty():
            lat, lon = map_queue.get()
            self.mapDisplay.update(lat, lon)
            path = os.path.abspath(mapfile)
            self.web.setUrl(QUrl.fromLocalFile(path))


# Application entry point

LoraReceiverInstance = LoraReceiver(data_queue)
receiverThread = threading.Thread(target=LoraReceiverInstance.receive_data, daemon=True)
receiverThread.start()
app = QApplication(sys.argv)
w = MainWindow()
w.showMaximized()
sys.exit(app.exec_())