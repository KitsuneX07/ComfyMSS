from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem, QApplication, QLabel, QApplication, QToolBar, QFileDialog, QMessageBox, QTextEdit, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtGui import QFont, QDrag, QAction, QFontDatabase, QIcon
from PySide6.QtCore import Qt, QMimeData, QByteArray, QPoint, QLine, QSize
from view import ComfyUIView
from scene import ComfyUIScene
from monitor import MonitorPage
from download_page import DownloadPage
from nodes.model_node import MSSTModelNode, VRModelNode
from nodes.data_flow_node import InputNode, OutputNode
import json
import os
import shutil
import logging


class ComfyUIEditor(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.node_position_offset = 100
        print(os.getcwd())
        if not os.path.exists('./data'):
            shutil.copytree("data_backup", "data")
        if not os.path.exists('./configs'):
            shutil.copytree("configs_backup", "configs")    
        self.msst_model_data = self.load_json('./data/msst_model_map.json')
        self.vr_model_data = self.load_json('./data/vr_model_map.json')
        self.setup_editor()

    def load_json(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    def setup_editor(self):
        # 设置窗口大小和标题
        self.setGeometry(300, 200, 1440, 1080)

        self.scene = ComfyUIScene()
        self.monitor_page = MonitorPage(refresh_rate=1000)
        self.monitor_page.setFont(QApplication.font())
        self.view = ComfyUIView(self.scene, self)

        current_font = QApplication.font()
        current_font.setPointSize(16)
        self.setFont(current_font)
        print("当前字体:", current_font.family(), "大小:", current_font.pointSize())
        self.setWindowTitle("ComfyMSS Editor")

        # 创建主布局
        self.layout = QVBoxLayout(self)

        # 创建工具栏
        self.add_toolbar()

        # 创建水平Splitter用于树形控件和场景视图
        splitter = QSplitter(Qt.Horizontal, self)
        self.layout.addWidget(splitter)

        self.view.setAcceptDrops(True)
        splitter.addWidget(self.view)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Node list")
        self.tree.setStyleSheet("QHeaderView::section{background-color: #313131; color: white; border: 0px; font-size: 16px; font-family: Consolas;}")
        self.tree.setDragEnabled(True)
        splitter.addWidget(self.tree)

        self.tree.itemDoubleClicked.connect(self.add_selected_model_node)
        self.tree.startDrag = self.start_drag

        current_font = QApplication.font()
        new_font = QFont(current_font.family(), 16)
        self.tree.setFont(new_font)
        self.tree.setStyleSheet("QTreeWidget::item{margin: 1px;}")
        self.populate_tree()

        # 将MonitorPage添加到布局中，并设置固定高度
        self.monitor_page.setFixedHeight(200)
        self.layout.addWidget(self.monitor_page)
        self.download_page = None

        self.showMaximized()

    def populate_tree(self):
        # 填充树形控件
        for category, models in self.msst_model_data.items():
            category_item = QTreeWidgetItem(self.tree)
            category_item.setText(0, category)
            category_item.setData(0, Qt.UserRole, category)  # 设置model_class
            for model in models:
                model_item = QTreeWidgetItem(category_item)
                model_item.setText(0, model["name"])
                model["model_class"] = category  # 添加model_class信息到模型数据
                model_item.setData(0, Qt.UserRole, model)
                model_item.setToolTip(0, model["name"])

        vr_category_item = QTreeWidgetItem(self.tree)
        vr_category_item.setText(0, "vr_models")
        for model_name, model in self.vr_model_data.items():
            model["model_class"] = "vr_models"
            model["name"] = model_name
            model_item = QTreeWidgetItem(vr_category_item)
            model_item.setText(0, model_name)
            model_item.setData(0, Qt.UserRole, model)
            model_item.setToolTip(0, model["name"])

        # 添加输入和输出节点
        io_category_item = QTreeWidgetItem(self.tree)
        io_category_item.setText(0, "I/O")

        input_node_item = QTreeWidgetItem(io_category_item)
        input_node_item.setText(0, "Input Node")
        input_node_item.setData(0, Qt.UserRole, "InputNode")

        output_node_item = QTreeWidgetItem(io_category_item)
        output_node_item.setText(0, "Output Node")
        output_node_item.setData(0, Qt.UserRole, "OutputNode")

    def add_selected_model_node(self, item, column):
        # 处理双击事件
        if item.childCount() > 0:
            return
        model_info = item.data(0, Qt.UserRole)
        print("Add model node:", model_info)
        pos = [100, 100]
        self.view.create_node(model_info, pos)

    def start_drag(self, event):
        item = self.tree.currentItem()
        if not item:
            return
        mime_data = QMimeData()
        model_info = item.data(0, Qt.UserRole)
        mime_data.setData('application/json', QByteArray(json.dumps(model_info).encode('utf-8')))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        result = drag.exec(Qt.MoveAction)
        
    def add_toolbar(self):
        toolbarWidget = QWidget(self)
        layout = QHBoxLayout()
        toolbarWidget.setLayout(layout)

        label = QLabel("Comfy MSS Editor")
        label.setStyleSheet("color: white;")

        toolbar1 = QToolBar()
        toolbar2 = QToolBar()
        toolbar3 = QToolBar()
        for toolbar in [toolbar1, toolbar2, toolbar3]:
            toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2A2A2A;
                border-radius: 10px;
                padding: 5px;
            }
            QToolBar QToolButton {
                border: none;
                padding: 5px;
                margin: 2px;
            }
            QToolBar QToolButton:hover {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 5px;
            }
            QToolBar QToolButton:pressed {
                background-color: rgba(255, 255, 255, 50);
            }
            """)

        open_action = QAction(QIcon("ComfyUI/style/icons/open.svg"), "", self)
        open_action.setToolTip("loading an existing preset")
        open_action.triggered.connect(self.load_file)
        toolbar1.addAction(open_action)

        save_action = QAction(QIcon("ComfyUI/style/icons/save.svg"), "", self)
        save_action.setToolTip("saving the current preset to disk")
        save_action.triggered.connect(self.save_file)
        toolbar1.addAction(save_action)

        run_action = QAction(QIcon("ComfyUI/style/icons/run.svg"), "", self)
        run_action.setToolTip("running the current editor page")
        run_action.triggered.connect(self.view.run)
        toolbar2.addAction(run_action)

        interrupt_action = QAction(QIcon("ComfyUI/style/icons/interrupt.svg"), "", self)
        interrupt_action.setToolTip("interrupting the current running process")
        interrupt_action.triggered.connect(self.view.interrupt_inference)
        toolbar2.addAction(interrupt_action)

        download_action = QAction(QIcon("ComfyUI/style/icons/download.svg"), "", self)
        download_action.setToolTip("downloading models")
        download_action.triggered.connect(self.show_download_page)
        toolbar2.addAction(download_action)

        close_action = QAction(QIcon("ComfyUI/style/icons/exit.svg"), "", self)
        close_action.setToolTip("closing the editor")
        close_action.triggered.connect(self.close)
        toolbar3.addAction(close_action)

        layout.addWidget(label)
        layout.addWidget(toolbar1)
        layout.addWidget(toolbar2)
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(toolbar3)

        self.layout.insertWidget(0, toolbarWidget)
        
    def load_file(self):
        defalut_path = "./presets"
        file_path, _ = QFileDialog.getOpenFileName(self, "打开文件", defalut_path, "Preset Files (*.preset);;All Files (*)")
        if file_path:
            self.view.load(file_path)
            QMessageBox.information(self, "Load", f"Loading preset from {file_path}")

    def save_file(self):
        defalut_path = "./presets"
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", defalut_path, "Preset Files (*.preset);;All Files (*)")
        if file_path:
            self.view.save(file_path)
            QMessageBox.information(self, "Save", f"Saving preset to {file_path}")

    def show_download_page(self):
        if not self.download_page:
            self.download_page = DownloadPage()
            self.download_page.setFont(self.font())
        self.download_page.show()
        
    def closeEvent(self, event):

        if self.download_page is not None and self.download_page.isVisible():
            self.download_page.close()
        super().closeEvent(event)