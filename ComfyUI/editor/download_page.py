import os
import sys
import subprocess
from main import get_darkModePalette, load_stylesheet

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QFontDatabase, QFont


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
        self.setup_ui()
        
    def setup_ui(self):
        self.resize(400, 600)
        self.setWindowTitle("ComfyMSS Model Downloader")
        
if __name__ == "__main__":
    app = QApplication([])
    download_page = DownloadPage()
    download_page.show()
    sys.exit(app.exec())