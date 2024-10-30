from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Slot, QTimer, Qt
from circular_progress import CircularProgress
import pynvml
import platform
from torch import cuda, backends

class MonitorWidget(QWidget):
    valueChanged = Signal(int)

    def __init__(self, label_text="Usage"):
        super().__init__()
        self.circular_progress = CircularProgress(value=0)
        self.circular_progress.setFixedSize(120, 120)

        self.label = QLabel(label_text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.circular_progress)
        layout.addWidget(self.label)

        self.valueChanged.connect(self.circular_progress.set_value)

    def set_label_text(self, text):
        self.label.setText(text)

    @Slot()
    def update_value(self, new_value):
        self.valueChanged.emit(new_value)


class MonitorPage(QWidget):
    def __init__(self, refresh_rate=1000):
        super().__init__()
        self.layout = QHBoxLayout(self)

        self.gpu_monitor = MonitorWidget(label_text="GPU Usage")
        self.vram_monitor = MonitorWidget(label_text="VRAM Usage")
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.message_box = self.setup_message_box()

        self.layout.addWidget(self.gpu_monitor)
        self.layout.addWidget(self.vram_monitor)
        self.layout.addWidget(self.message_box)
        self.layout.addItem(spacer)

        try:
            pynvml.nvmlInit()  # Initialize NVML
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Assuming single GPU

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_values)
            self.timer.start(refresh_rate)
        except pynvml.NVMLError as error:
            print(f"NVML error: {error}")
            pass

    @Slot()
    def update_values(self):
        try:
            # GPU utilization
            gpu_utilization = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            self.gpu_monitor.update_value(gpu_utilization.gpu)

            # Memory utilization
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            total_memory = memory_info.total
            used_memory = memory_info.used

            # VRAM usage
            vram_usage = int((used_memory / total_memory) * 100)
            self.vram_monitor.update_value(vram_usage)

        except pynvml.NVMLError as error:
            print(f"NVML error: {error}")

    def setup_message_box(self):
        os_name = platform.system()
        os_version = platform.version()
        machine = platform.machine()
        cpu = platform.processor()
        self.gpu = "No available GPU detected"
        if cuda.is_available():
            self.gpu = backends.cuda.get_device_name(0)
        elif backends.mps.is_available():
            self.gpu = "MPS"
        
        message_box = QWidget()
        message_box.setStyleSheet("font-size: 15px; color: white;")
        message_box_layout = QVBoxLayout(message_box)
        message_box_layout.addWidget(QLabel(f"OS: {os_name} {os_version}"))
        message_box_layout.addWidget(QLabel(f"Machine: {machine}"))
        message_box_layout.addWidget(QLabel(f"CPU: {cpu}"))
        message_box_layout.addWidget(QLabel(f"GPU: {self.gpu}"))

        return message_box


if __name__ == '__main__':
    app = QApplication([])

    window = MonitorPage(refresh_rate=1000)
    window.show()

    app.exec()