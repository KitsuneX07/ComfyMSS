import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFontDatabase, QFont, QPalette, QColor
from PySide6.QtCore import Qt

from editor import ComfyUIEditor

def load_stylesheet(path):
    with open(path, 'r') as f:
        return f.read()
    

def get_darkModePalette(app=None) :
    
    darkPalette = app.palette()
    darkPalette.setColor( QPalette.Window, QColor( 53, 53, 53 ) )
    darkPalette.setColor( QPalette.WindowText, Qt.white )
    darkPalette.setColor( QPalette.Disabled, QPalette.WindowText, QColor( 127, 127, 127 ) )
    darkPalette.setColor( QPalette.Base, QColor( 42, 42, 42 ) )
    darkPalette.setColor( QPalette.AlternateBase, QColor( 66, 66, 66 ) )
    darkPalette.setColor( QPalette.ToolTipBase, QColor( 53, 53, 53 ) )
    darkPalette.setColor( QPalette.ToolTipText, Qt.white )
    darkPalette.setColor( QPalette.Text, Qt.white )
    darkPalette.setColor( QPalette.Disabled, QPalette.Text, QColor( 127, 127, 127 ) )
    darkPalette.setColor( QPalette.Dark, QColor( 35, 35, 35 ) )
    darkPalette.setColor( QPalette.Shadow, QColor( 20, 20, 20 ) )
    darkPalette.setColor( QPalette.Button, QColor( 53, 53, 53 ) )
    darkPalette.setColor( QPalette.ButtonText, Qt.white )
    darkPalette.setColor( QPalette.Disabled, QPalette.ButtonText, QColor( 127, 127, 127 ) )
    darkPalette.setColor( QPalette.BrightText, Qt.red )
    darkPalette.setColor( QPalette.Link, QColor( 42, 130, 218 ) )
    darkPalette.setColor( QPalette.Highlight, QColor( 42, 130, 218 ) )
    darkPalette.setColor( QPalette.Disabled, QPalette.Highlight, QColor( 80, 80, 80 ) )
    darkPalette.setColor( QPalette.HighlightedText, Qt.white )
    darkPalette.setColor( QPalette.Disabled, QPalette.HighlightedText, QColor( 127, 127, 127 ), )
    
    return darkPalette

    
if __name__ == "__main__":
    app = QApplication(sys.argv + ['-platform', 'windows:darkmode=2'])
    app.setStyle('Fusion')
    os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
    app.setStyleSheet(load_stylesheet('ComfyUI/style/main.qss'))
    font_id = QFontDatabase.addApplicationFont("ComfyUI/style/ubuntu-font-family-0.83/Ubuntu-R.ttf")
    app.setPalette(get_darkModePalette(app))
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    app.setFont(QFont(font_family, 15))
    editor = ComfyUIEditor()
    sys.exit(app.exec())