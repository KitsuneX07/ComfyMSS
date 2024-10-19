from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem, QApplication, QLabel, QApplication, QToolBar, QFileDialog, QMessageBox
from PySide6.QtGui import QFont, QDrag, QAction
from PySide6.QtCore import Qt, QMimeData, QByteArray, QPoint, QLine
from view import ComfyUIView
from scene import ComfyUIScene
from nodes.model_node import MSSTModelNode, VRModelNode
from nodes.data_flow_node import InputNode, OutputNode
import json
import os
import shutil


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
        self.view = ComfyUIView(self.scene, self)
        
        current_font = QApplication.font()
        current_font.setPointSize(16)
        self.setFont(current_font)
        print("当前字体:", current_font.family(), "大小:", current_font.pointSize())
        self.setWindowTitle("ComfyMSS Editor")

        # 创建主布局
        self.layout = QVBoxLayout(self)
        self.add_toolbar()
        # 创建Splitter，用于调整树形控件和场景视图的宽度
        splitter = QSplitter(Qt.Horizontal, self)
        self.layout.addWidget(splitter)

        # 创建场景和视图，并添加到Splitter中
        
        self.view.setAcceptDrops(True)  # 启用接受拖放
        # 创建工具栏
        

        splitter.addWidget(self.view)

        # 创建树形控件
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Node list")
        self.tree.setStyleSheet("QHeaderView::section{background-color: #313131; color: white; border: 0px; font-size: 16px; font-family: Consolas;}")
        self.tree.setDragEnabled(True)  # 启用拖放
        splitter.addWidget(self.tree)

        self.tree.itemDoubleClicked.connect(self.add_selected_model_node)  # 双击添加
        self.tree.startDrag = self.start_drag  # 重写startDrag方法

        # 设置字体
        current_font = QApplication.font()
        new_font = QFont(current_font.family(), 16)
        self.tree.setFont(new_font)        
        self.tree.setStyleSheet("QTreeWidget::item{margin: 1px;}")
        self.populate_tree()
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

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        toolbar.addAction(close_action)
        
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


