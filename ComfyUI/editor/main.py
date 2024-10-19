import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont

from editor import ComfyUIEditor

def load_stylesheet(path):
    with open(path, 'r') as f:
        return f.read()

if __name__ == "__main__":
    app = QApplication([])
    os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
    app.setStyleSheet(load_stylesheet('ComfyUI/style/main.qss'))
    font_id = QFontDatabase.addApplicationFont("ComfyUI/style/ubuntu-font-family-0.83/Ubuntu-R.ttf")
    if font_id == -1:
        print("字体加载失败")
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    app.setFont(QFont(font_family, 15))
    editor = ComfyUIEditor()
    sys.exit(app.exec())