import os
import sys
import subprocess
import json
from main import get_darkModePalette, load_stylesheet
from hf_check import choose_best_site

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGroupBox, QCheckBox, QButtonGroup, QComboBox, QMessageBox, QPushButton
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtCore import Qt, QThread, Signal


def get_system():
    if sys.platform == 'win32':
        aria2c_path = os.path.join(os.path.dirname(__file__), '..', '..', 'aria2', 'aria2-1.37.0-win-64bit-build1', 'aria2c.exe')
        return 'windows', aria2c_path
    elif sys.platform == 'darwin':
        return 'mac', None
    elif sys.platform == 'linux':
        aria2c_path = os.path.join(os.path.dirname(__file__), '..', '..', 'aria2', 'aria2-1.37.0-aarch64-linux-android-build1', 'aria2c')
        return 'linux', aria2c_path
    else:
        return None, None
    
class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.system, self.aria2c_path = get_system()
        self.msst_model_data = self.load_json('./data/msst_model_map.json')
        self.vr_model_data = self.load_json('./data/vr_model_map.json')
        self.setup_ui()

    def load_json(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data    
        
    def setup_ui(self):
        self.resize(400, 600)
        self.setWindowTitle("ComfyMSS Model Downloader")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.title = QLabel("ComfyMSS Model Downloader")
        self.title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title)
        group_box = QGroupBox()
        group_layout = QVBoxLayout()
        group_box.setLayout(group_layout)

        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)

        # 创建 multi_stem_models 复选框和组合框
        multi_stem_checkbox = QCheckBox("multi_stem_models")
        group_layout.addWidget(multi_stem_checkbox)
        self.button_group.addButton(multi_stem_checkbox)
        self.multi_stem_combobox = QComboBox()
        self.multi_stem_combobox.setEnabled(False)  # 初始禁用
        group_layout.addWidget(self.multi_stem_combobox)

        # 创建 single_stem_models 复选框和组合框
        single_stem_checkbox = QCheckBox("single_stem_models")
        group_layout.addWidget(single_stem_checkbox)
        self.button_group.addButton(single_stem_checkbox)
        self.single_stem_combobox = QComboBox()
        self.single_stem_combobox.setEnabled(False)  # 初始禁用
        group_layout.addWidget(self.single_stem_combobox)

        # 创建 vocal_models 复选框和组合框
        vocal_model_checkbox = QCheckBox("vocal_models")
        group_layout.addWidget(vocal_model_checkbox)
        self.button_group.addButton(vocal_model_checkbox)
        self.vocal_model_combobox = QComboBox()
        self.vocal_model_combobox.setEnabled(False)  # 初始禁用
        group_layout.addWidget(self.vocal_model_combobox)

        # 创建VR_Models 复选框和组合框
        vr_model_checkbox = QCheckBox("VR_Models")
        group_layout.addWidget(vr_model_checkbox)
        self.button_group.addButton(vr_model_checkbox)
        self.vr_model_combobox = QComboBox()
        self.vr_model_combobox.setEnabled(False)
        group_layout.addWidget(self.vr_model_combobox)

        for combo_box in [self.multi_stem_combobox, self.single_stem_combobox, self.vocal_model_combobox, self.vr_model_combobox]:
            combo_box.setFixedHeight(40)

        # 连接复选框的 stateChanged 信号到槽函数
        multi_stem_checkbox.stateChanged.connect(self.refresh_state)
        single_stem_checkbox.stateChanged.connect(self.refresh_state)
        vocal_model_checkbox.stateChanged.connect(self.refresh_state)
        vr_model_checkbox.stateChanged.connect(self.refresh_state)

        self.layout.addWidget(group_box)

        download_button = QPushButton("Download")
        download_button.clicked.connect(self.download_model)
        self.layout.addWidget(download_button)

    def refresh_state(self):
        if self.button_group.checkedButton() is None:
            return
        selected_checkbox = self.button_group.checkedButton()
        if selected_checkbox.text() == "multi_stem_models":
            for model in self.msst_model_data['multi_stem_models']:
                self.multi_stem_combobox.addItem(model['name'])
            self.multi_stem_combobox.setEnabled(True)
            self.single_stem_combobox.clear()
            self.single_stem_combobox.setEnabled(False)
            self.vocal_model_combobox.clear()
            self.vocal_model_combobox.setEnabled(False)
            self.vr_model_combobox.clear()
            self.vr_model_combobox.setEnabled(False)

        elif selected_checkbox.text() == "single_stem_models":
            for model in self.msst_model_data['single_stem_models']:
                self.single_stem_combobox.addItem(model['name'])
            self.single_stem_combobox.setEnabled(True)
            self.multi_stem_combobox.clear()
            self.multi_stem_combobox.setEnabled(False)
            self.vocal_model_combobox.clear()
            self.vocal_model_combobox.setEnabled(False)
            self.vr_model_combobox.clear()
            self.vr_model_combobox.setEnabled(False)

        elif selected_checkbox.text() == "vocal_models":
            for model in self.msst_model_data['vocal_models']:
                self.vocal_model_combobox.addItem(model['name'])
            self.vocal_model_combobox.setEnabled(True)
            self.multi_stem_combobox.clear()
            self.multi_stem_combobox.setEnabled(False)
            self.single_stem_combobox.clear()
            self.single_stem_combobox.setEnabled(False)
            self.vr_model_combobox.clear()
            self.vr_model_combobox.setEnabled(False)

        elif selected_checkbox.text() == "VR_Models":
            for model in self.vr_model_data:
                self.vr_model_combobox.addItem(model)
            self.vr_model_combobox.setEnabled(True)
            self.multi_stem_combobox.clear()
            self.multi_stem_combobox.setEnabled(False)
            self.single_stem_combobox.clear()
            self.single_stem_combobox.setEnabled(False)
            self.vocal_model_combobox.clear()
            self.vocal_model_combobox.setEnabled(False)
        
    def download_model(self):
        if self.button_group.checkedButton() is None:
            return
        self.selected_checkbox = self.button_group.checkedButton()
        self.check_thread = check_hf_thread()
        self.check_thread.finished.connect(self.on_check_thread_finished)
        self.check_thread.start()

        for combobox in [self.multi_stem_combobox, self.single_stem_combobox, self.vocal_model_combobox]:
            self.selected_model = combobox.currentText()
            if self.selected_model:
                break

    def on_check_thread_finished(self):
        self.best_site, self.response_time, self.download_site = self.check_thread.get_result()
        if not self.download_site:
            QMessageBox.critical(self, "Error", "No available download site")
            return
        self.url = self.download_site + '/'.join(['', 'model', self.selected_checkbox.text(), self.selected_model])
        print(self.url)

class check_hf_thread(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        best_site, response_time, download_site = choose_best_site()
        if isinstance(best_site, str) and "Error" in best_site:
            print(best_site)
        else:
            print(f"Best site: {best_site} with response time: {response_time:.4f} seconds, URL: {download_site}")
            self.best_site = best_site
            self.response_time = response_time  
            self.download_site = download_site

    def get_result(self):
        return self.best_site, self.response_time, self.download_site        


if __name__ == "__main__":
    app = QApplication([])
    os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
    download_page = DownloadPage()
    download_page.show()
    sys.exit(app.exec())
