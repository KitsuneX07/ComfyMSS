from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem, QApplication, QLabel, QApplication, QToolBar, QFileDialog, QMessageBox, QTextEdit, QDockWidget
from PySide6.QtGui import QFont, QDrag, QAction, QFontDatabase
from PySide6.QtCore import Qt, QMimeData, QByteArray, QPoint, QLine
from view import ComfyUIView
from scene import ComfyUIScene
from nodes.model_node import MSSTModelNode, VRModelNode
from nodes.data_flow_node import InputNode, OutputNode
import json
import os
import shutil
import logging


class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)
        self.text_edit.ensureCursorVisible()


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
        self.log_window = QTextEdit(self)
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("color: white;")  # 设置字体为白色
        self.log_window.setFont(QFont('Courier New', 10))  # 设置等宽字体
        self.view = ComfyUIView(self.scene, self.log_window, self)

        current_font = QApplication.font()
        current_font.setPointSize(16)
        self.setFont(current_font)
        print("当前字体:", current_font.family(), "大小:", current_font.pointSize())
        self.setWindowTitle("ComfyMSS Editor")

        # 创建主布局
        self.layout = QVBoxLayout(self)

        # 创建工具栏
        self.add_toolbar()

        # 创建垂直Splitter用于主体内容和日志窗口
        vertical_splitter = QSplitter(Qt.Vertical, self)
        self.layout.addWidget(vertical_splitter)

        # 创建水平Splitter用于树形控件和场景视图
        splitter = QSplitter(Qt.Horizontal, self)
        vertical_splitter.addWidget(splitter)  # 添加到垂直Splitter

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

        # 将日志窗口添加到垂直Splitter


        log_handler = QTextEditLogger(self.log_window)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)

        vertical_splitter.addWidget(self.log_window)  # 添加日志窗口

        self.show()

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

        vr_category_item = QTreeWidgetItem(self.tree)
        vr_category_item.setText(0, "vr_models")
        for model_name, model in self.vr_model_data.items():
            model["model_class"] = "vr_models"
            model["name"] = model_name
            model_item = QTreeWidgetItem(vr_category_item)
            model_item.setText(0, model_name)
            model_item.setData(0, Qt.UserRole, model)

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
        toolbar = QToolBar()
        self.layout.addWidget(toolbar)
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.load_file)
        toolbar.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        run_action = QAction("Run", self)
        run_action.triggered.connect(self.view.run)
        toolbar.addAction(run_action)

        close_action = QAction("Exit", self)
        close_action.triggered.connect(self.close)
        toolbar.addAction(close_action)

        toggle_log_action = QAction("Toggle Log", self)
        toggle_log_action.triggered.connect(self.toggle_log_window)
        toolbar.addAction(toggle_log_action)
        
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

    def toggle_log_window(self):
        # 切换日志窗口的可见性
        if self.log_window.isVisible():
            self.log_window.hide()
        else:
            self.log_window.show()
        
