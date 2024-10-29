import sys
import os
os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
import json
import webbrowser
from huggingface_hub import hf_hub_url
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QProgressBar, QComboBox, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt, QFile, QSize
from PySide6.QtGui import QIcon
from thread import DownloadThread


class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download Manager")
        self.setFixedWidth(400)

        self.setStyleSheet("""
            QWidget {
                color: white;
                background-color: #333;  /* 设置整体背景色为深色 */
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLabel {
                font-size: 14px;
                color: white;
            }
            QComboBox {
                color: white;
                background-color: #444;
                border: 1px solid #555;   
                border-radius: 5px;
                font-size: 13px; 
            }
        """)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.msst_model_data = self.load_json('./data/msst_model_map.json')
        self.vr_model_data = self.load_json('./data/vr_model_map.json')

        self.title = QLabel("Model Download Center")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.auto_download_label = QLabel("Auto Download")
        self.auto_download_label.setAlignment(Qt.AlignCenter)
        self.auto_download_label.setStyleSheet("font-size: 15px;")

        self.model_type_combobox = QComboBox()
        self.model_type_combobox.addItem("multi_stem_models")
        self.model_type_combobox.addItem("single_stem_models")
        self.model_type_combobox.addItem("vocal_models")
        self.model_type_combobox.addItem("VR_Models")
        self.model_type_combobox.setCurrentIndex(-1)

        self.model_combobox = QComboBox()

        self.model_type_combobox.currentIndexChanged.connect(self.on_model_type_changed)
            
        self.auto_download_button = QPushButton(QIcon("ComfyUI/style/icons/download.svg"), "Auto Download")
        self.auto_download_button.setStyleSheet("font-size: 15px;")
        self.auto_download_button.setIconSize(QSize(20, 20))
        self.auto_download_button.setFixedWidth(150)
        self.auto_download_button.clicked.connect(self.on_auto_download)

        self.manual_download_button = QPushButton("Try Manual Download")
        self.manual_download_button.setStyleSheet("font-size: 15px;")
        self.manual_download_button.setIconSize(QSize(20, 20))
        self.manual_download_button.setFixedWidth(200)
        self.manual_download_button.clicked.connect(self.on_manual_download)


        self.layout.addWidget(self.title)
        self.layout.addWidget(self.auto_download_label)
        self.layout.addWidget(self.model_type_combobox)
        self.layout.addWidget(self.model_combobox)
        button_layout1 = QHBoxLayout()
        button_layout1.addStretch()
        button_layout1.addWidget(self.auto_download_button)
        button_layout1.addStretch()
        self.layout.addLayout(button_layout1)
        button_layout2 = QHBoxLayout()
        button_layout2.addStretch()
        button_layout2.addWidget(self.manual_download_button)
        button_layout2.addStretch()
        self.layout.addLayout(button_layout2)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.speed_label = QLabel("Download Speed: 0 KB/s")
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setStyleSheet("font-size: 15px;")

        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.speed_label)

    def load_json(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    def on_model_type_changed(self):
        self.model_combobox.clear()
        model_type = self.model_type_combobox.currentText()
        if model_type == "VR_Models":
            for model in self.vr_model_data:
                self.model_combobox.addItem(model)
        else:
            for model in self.msst_model_data[model_type]:
                self.model_combobox.addItem(model["name"])

    def on_manual_download(self):
        website = "https://r1kc63iz15l.feishu.cn/wiki/YrBkwwstBiRop8kDflZcVNHbnmc"
        webbrowser.open(website)

    def on_manual_download(self):
        website = "https://r1kc63iz15l.feishu.cn/wiki/YrBkwwstBiRop8kDflZcVNHbnmc"
        webbrowser.open(website)

    def on_auto_download(self):
        model_type = self.model_type_combobox.currentText()
        model_name = self.model_combobox.currentText()
        if model_type and model_name:
            self.download_thread = DownloadThread(model_type, model_name)
            self.download_thread.log_signal.connect(self.display_log)
            self.download_thread.progress_signal.connect(self.update_progress)
            self.download_thread.speed_signal.connect(self.update_speed)
            self.download_thread.finished.connect(self.download_finished)
            self.download_thread.start()
        else:
            self.display_log("请选择模型类型和模型名称！")

    def download_finished(self):
        self.display_log("Download completed!")
        self.progress_bar.setValue(100)
        self.download_thread.quit()
        message_box = QMessageBox()
        message_box.setText("Download completed!")

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def update_speed(self, speed):
        self.speed_label.setText(f"Download Speed: {speed:.2f} MB/s")

    def display_log(self, message):
        print(message)  # 可以根据需要将日志显示在 UI 的某个标签或文本框中

if __name__ == "__main__":
    app = QApplication(sys.argv)
    os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
    window = DownloadPage()
    window.show()
    sys.exit(app.exec())
