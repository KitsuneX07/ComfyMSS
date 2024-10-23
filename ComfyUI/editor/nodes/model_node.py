import sys
import os
import yaml
import json
from ml_collections import ConfigDict
from omegaconf import OmegaConf

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QBrush, QFont
from PySide6.QtWidgets import QGraphicsProxyWidget, QCheckBox, QLabel, QHBoxLayout, QGraphicsDropShadowEffect, \
    QGraphicsTextItem, QGraphicsItem, QGroupBox, QApplication

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from ComfyUI.editor.config import EditorConfig, NodeConfig
from ComfyUI.editor.node_port import InputPort, OutputPort, ParamPort, BoolPort, NodePort
from ComfyUI.editor.node import Node
from ComfyUI.editor.nodes.data_flow_node import OutputNode, InputNode

os.chdir(os.path.join(os.getcwd(), '../../'))

TEMP_PATH = "tmpdir"
PYTHON = "D:/Anaconda/envs/msst/python.exe"

import logging
import subprocess


class ModelNode(Node):

    def __init__(self, model_class = None, model_name = None, model_type = None, input_ports = None, param_ports = None,
                 output_ports = None, bool_ports = None, scene = None, parent = None, upstream_node = None,
                 downstream_nodes = None):
        super().__init__(parent)
        self._model_class = model_class
        self._model_name = model_name
        self._model_type = model_type
        self._scene = scene
        self.input_ports = input_ports or []
        self.param_ports = param_ports or []
        self.output_ports = output_ports or []
        self.bool_ports = bool_ports or []
        self.upstream_node = upstream_node
        self.downstream_nodes = downstream_nodes or []
        self._node_width = self.node_width_min
        self._node_height = self.node_height_min
        self._shadow = QGraphicsDropShadowEffect()
        self._shadow.setOffset(0, 0)
        self._shadow.setBlurRadius(20)
        self._shadow_color = QColor('#aaeeee00')
        self.setFlags(
            QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        super().init_node_color()
        self.init_title()
        self.update_ports()
        self.setup_output_format_selector()
        self.store_dirs = {}
        self.input_path = None

    def init_title(self):
        current_font = QApplication.font()
        new_font = QFont(current_font.family(), 16)
        self._title_font = new_font
        self._title_color = Qt.white
        self._title_font_size = 16
        self._title_line1, self._title_line2 = QGraphicsTextItem(self), QGraphicsTextItem(self)
        self._title_line1.setPlainText(self._model_class)
        self._friendly_name = self._model_name[:30] + '...' if len(self._model_name) > 30 else self._model_name

        self._title_line2.setPlainText(self._friendly_name)
        self._title_line2.setFont(QFont(current_font.family(), 12))
        self._title_line2.setToolTip(self._model_name)
        # for title_line in [self._title_line1, self._title_line2]:
        #     title_line.setFont(self._title_font)
        #     title_line.setDefaultTextColor(self._title_color)

        self._title_line1.setDefaultTextColor(self._title_color)
        self._title_line2.setDefaultTextColor(self._title_color)

        self._title_line1.setPos(self.title_padding, self.title_padding)
        self._title_line2.setPos(self.title_padding, self.title_padding * 3 + self._title_font_size)
        title_width = self._title_font_size * len(self._model_name) + 2 * self.title_padding
        # print(self._node_width, title_width)
        # self._node_width = max(self._node_width, title_width)
        self.title_height = 6 * self.title_padding + 2 * self._title_font_size

    def update_ports(self):
        self.init_ports()
        for port_list in [self.input_ports, self.param_ports, self.bool_ports, self.output_ports]:
            for i, port in enumerate(port_list):
                self.add_port(port, index = i)

    def add_port(self, port: NodePort, index = 0):
        self._node_width = max(self._node_width, port._port_width + self.port_padding * 3)
        self._node_height = self.title_height + (
                max(len(self.input_ports), len(self.output_ports)) + len(self.param_ports) + len(
            self.bool_ports)) * (self.port_padding + port._port_icon_size) + self.port_padding
        port.add_to_parent_node(self, self._scene)

        y_offset = self.title_height + index * (self.port_padding + port._port_icon_size) + self.port_padding
        if port.port_type == NodePort.PORT_TYPE_INPUT:
            port.setPos(self.port_padding, y_offset)
        elif port.port_type == NodePort.PORT_TYPE_OUTPUT:
            port.setPos(self._node_width - port._port_width - self.port_padding, y_offset)
        elif port.port_type == NodePort.PORT_TYPE_PARAM:
            port.setPos(self.port_padding, y_offset + max(len(self.input_ports), len(self.output_ports)) * (
                    self.port_padding + port._port_icon_size))
        elif port.port_type == NodePort.PORT_TYPE_BOOL:
            port.setPos(self.port_padding,
                        y_offset + (len(self.param_ports) + max(len(self.input_ports), len(self.output_ports))) * (
                                self.port_padding + ParamPort()._port_icon_size))
   

    def setup_output_format_selector(self):
        # Create a group box for output format selection
        self.output_format_group = QGroupBox()

        # Set font size to be -6 of other components
        font = self.output_format_group.font()
        font.setPointSize(EditorConfig.editor_node_title_font_size - 6)
        self.output_format_group.setAttribute(Qt.WA_TranslucentBackground)
        self.output_format_group.setStyleSheet("QGroupBox { border: 0; }")
        # Initialize checkboxes
        self.wav_checkbox = QCheckBox("wav")
        self.flac_checkbox = QCheckBox("flac")
        self.mp3_checkbox = QCheckBox("mp3")

        # Apply the same font modifications to each checkbox
        for checkbox in [self.wav_checkbox, self.flac_checkbox, self.mp3_checkbox]:
            checkbox.setAutoExclusive(True)
            checkbox.setStyleSheet("QCheckBox { color: white; }")
            checkbox.setFont(font)


        # Set default selection
        self.wav_checkbox.setChecked(True)

        # Layout for checkboxes
        layout = QHBoxLayout()
        label = QLabel("Output Format:")
        label.setStyleSheet("QLabel { color: white; }")
        label.setFont(font)
        layout.addWidget(label)
        layout.addWidget(self.wav_checkbox)
        layout.addWidget(self.flac_checkbox)
        layout.addWidget(self.mp3_checkbox)

        self.output_format_group.setLayout(layout)

        proxy = QGraphicsProxyWidget(self)
        
        proxy.setWidget(self.output_format_group)
        proxy.setPos(0, self._node_height)

        self._node_height += self.output_format_group.sizeHint().height() + self.port_padding

    def get_selected_format(self):
        if self.wav_checkbox.isChecked():
            return "wav"
        elif self.flac_checkbox.isChecked():
            return "flac"
        elif self.mp3_checkbox.isChecked():
            return "mp3"
        return "wav"  # In case none is selected
    
    def update_output_format(self, format):
        if format == "wav":
            self.wav_checkbox.setChecked(True)
        elif format == "flac":
            self.flac_checkbox.setChecked(True)
        elif format == "mp3":
            self.mp3_checkbox.setChecked(True)


class MSSTModelNode(ModelNode):
    def __init__(self, model_class = None, model_name = None, model_type = None, input_ports = None, param_ports = None,
                 output_ports = None, bool_ports = None, scene = None, parent = None, upstream_node = None,
                 downstream_nodes = None):
        super().__init__(model_class, model_name, model_type, input_ports, param_ports, output_ports, bool_ports, scene,
                         parent, upstream_node, downstream_nodes)

    def init_ports(self):
        with open("data/msst_model_map.json", 'r') as f:
            model_map = json.load(f)
        for _ in model_map[self._model_class]:
            if _['name'] == self._model_name:
                self._config_path = _['config_path']
                self._model_type = _['model_type']

        with open(self._config_path) as f:
            if self._model_type == 'htdemucs':
                self._config = OmegaConf.load(self._config_path)
            else:
                self._config = ConfigDict(yaml.load(f, Loader = yaml.FullLoader))

        self.input_ports = [InputPort("Input")]
        for instrument in self._config.training.instruments:
            self.output_ports.append(OutputPort(instrument))
        for param in self._config.inference:
            if param != "normalize":
                self.param_ports.append(ParamPort(port_label = param, default_value = self._config.inference[param]))
        self.bool_ports = [BoolPort(port_label = "Use CPU", default_value = False)]
        if "normalize" in self._config.inference:
            self.bool_ports.append(
                BoolPort(port_label = "Normalize", default_value = self._config.inference["normalize"]))
        self.bool_ports.append(BoolPort(port_label = "Use TTA", default_value = False))

        # print('input_ports:', self.input_ports)
        # print('output_ports:', self.output_ports)
        # print('param_ports:', self.param_ports)
        # print('bool_ports:', self.bool_ports)

    def update_params(self):
        logging.info(f"Running MSST model node {self._model_name}...")
        logging.info("Updating parameters...")
        for param_port in self.param_ports:
            self._config.inference[param_port.port_label] = int(param_port.port_value)

        for bool_port in self.bool_ports:
            if bool_port.port_label == "Normalize":
                self._config.inference['normalize'] = bool_port.port_value
            elif bool_port.port_label == "Use TTA":
                use_tta = bool_port.port_value

        # 保存更新后的配置到文件
        with open(self._config_path, 'w') as f:
            if self._model_type == 'htdemucs':
                OmegaConf.save(self._config, f)
            else:
                yaml.dump(self._config.to_dict(), f)

        logging.info("Parameters written back to config file successfully, start inferencing...")

        self.generate_output_path()
        logging.info(f"store_dirs: {self.store_dirs}")
        logging.info(f"input_path: {self.input_path}")

        self.params = {
            "input_path": self.input_path,
            "model_type": self._model_type,
            "config_path": self._config_path,
            "model_path": os.path.join("pretrain", self._model_class, self._model_name),
            "output_format": self.get_selected_format(),
            "store_dirs": self.store_dirs,
            "use_tta": use_tta,
        }

        # msst_separate = ComfyMSST(
        #     model_type=self._model_type,
        #     config_path=self._config_path,
        #     device='auto',
        #     device_ids=[0],
        #     model_path=os.path.join("./pretrain", self._model_class, self._model_name),
        #     output_format=self.get_selected_format(),
        #     store_dirs=self.store_dirs,
        #     use_tta=use_tta,
        #     debug=True
        # )

        # msst_separate.process_folder(input_folder=self.input_path)
        # logging.info("Inference completed successfully.")
        # msst_separate.del_cache()

    def generate_output_path(self) -> None:
        for output_port in self.output_ports:
            if output_port.is_connected():
                for connected_port in output_port.connected_ports:
                    self.store_dirs[output_port.port_label] = []
                    parent_node = connected_port.parent_node
                    if parent_node.__class__.__name__ == "OutputNode":
                        parent_node.update_params()
                        self.store_dirs[output_port.port_label].append(parent_node.output_path)
                    else:
                        path = os.path.join(TEMP_PATH, f"model_node_{parent_node.index}", output_port.port_label)
                        self.store_dirs[output_port.port_label].append(path)
                        if parent_node.input_path == None or parent_node.input_path == path:
                            parent_node.input_path = path
                        else:
                            raise ValueError("One model node should only have one input path.")

    def save(self) -> dict:
        data = {}
        data['pos'] = [self.scenePos().x(), self.scenePos().y()]
        data['model_class'] = self._model_class
        data['model_name'] = self._model_name
        data['model_type'] = self._model_type
        data["index"] = self.index
        data["params"] = {}
        for port in self.param_ports:
            data["params"][port.port_label] = port.port_value
        data["bools"] = {}
        for port in self.bool_ports:
            data["bools"][port.port_label] = port.port_value
        data["output_format"] = self.get_selected_format()
        return data

class VRModelNode(ModelNode):
    def __init__(self, model_class=None, model_name=None, input_ports=None, param_ports=None, output_ports=None, bool_ports=None, scene=None, parent=None, upstream_node=None, downstream_nodes=None):
        super().__init__(model_class, model_name, input_ports, param_ports, output_ports, bool_ports, scene, parent, upstream_node, downstream_nodes)

    def init_ports(self):
        with open("data/vr_model_map.json", 'r') as f:
            model_map = json.load(f)

        self.input_ports = [InputPort("Input")]
        self.output_ports.append(OutputPort(model_map[self._model_name]["primary_stem"]))
        self.output_ports.append(OutputPort(model_map[self._model_name]["secondary_stem"]))
        self.param_ports = [
            ParamPort("Batch Size", default_value=4),
            ParamPort("Window Size", default_value=512),
            ParamPort("Aggression", default_value=5),
            ParamPort("Post Process Threshold", default_value=0.2)
        ]
        self.bool_ports = [
            BoolPort("Use CPU", default_value=False),
            BoolPort("Invert Spect", default_value=False),
            BoolPort("Enable Tta", default_value=False),
            BoolPort("High End Process", default_value=False),
            BoolPort("Enable Post Process", default_value=False)
        ]

    def update_params(self):
        try:
            logging.info("Updating parameters...")
            self.generate_output_path()
            logging.info(f"Input path: {self.input_path}")
            logging.info(f"Output path: {self.store_dirs}")

            # 更新配置参数
            self.params = {
                "model_file": f"pretrain/VR_Models/{self._model_name}",
                "input_path": self.input_path,
                "output_folder": self.store_dirs,
                "output_format": self.get_selected_format(),
                "invert_using_spec": self.find_port_value("Invert Spect"),
                "use_cpu": self.find_port_value("Use CPU"),
                "vr_params": {
                    "batch_size": int(self.find_port_value("Batch Size")),
                "window_size": int(self.find_port_value("Window Size")),
                "aggression": int(self.find_port_value("Aggression")),
                "enable_tta": self.find_port_value("Enable Tta"),
                "enable_post_process": self.find_port_value("Enable Post Process"),
                "post_process_threshold": float(self.find_port_value("Post Process Threshold")),
                "high_end_process": self.find_port_value("High End Process"),
                }
            }
            logging.info(f"VR parameters: {self.params}")

            # output_folders = ' '.join(
            #     [f"--output_folder_{label} {' '.join(paths)}" for label, paths in self.store_dirs.items()]
            # )

            # invert_spect = self.find_port_value("Invert Spect")
            # logging.info(f"Invert Spect: {invert_spect}")

            # use_cpu = self.find_port_value("Use CPU")

            # vr_separator = ComfyVR(
            #     model_file=f"pretrain/VR_Models/{self._model_name}",
            #     output_format=self.get_selected_format(),
            #     invert_using_spec=invert_spect,
            #     use_cpu=use_cpu,
            #     vr_params=vr_params,
            #     output_dir=self.store_dirs,
            #     debug=True
            # )

            # vr_separator.process_folder(self.input_path)
            # logging.info("Inference completed successfully.")
            # vr_separator.del_cache()
        except Exception as e:
            logging.error(f"Error during VR model execution: {e}")

    def find_port_value(self, port_label):
        port = next((p for p in self.param_ports + self.bool_ports if p.port_label == port_label), None)
        return port.port_value if port else None

    def generate_output_path(self) -> None:
        for output_port in self.output_ports:
            if output_port.is_connected():
                for connected_port in output_port.connected_ports:
                    self.store_dirs[output_port.port_label] = []
                    parent_node = connected_port.parent_node
                    if parent_node.__class__.__name__ == "OutputNode":
                        parent_node.update_params()
                        self.store_dirs[output_port.port_label].append(parent_node.output_path)
                    else:
                        path = os.path.join(TEMP_PATH, f"model_node_{parent_node.index}", output_port.port_label)
                        self.store_dirs[output_port.port_label].append(path)
                        if parent_node.input_path == None or parent_node.input_path == path:
                            parent_node.input_path = path
                        else:
                            raise ValueError("One model node should only have one input path.")
                        
    def save(self) -> dict:
        data = {}
        data['pos'] = [self.scenePos().x(), self.scenePos().y()]
        data['model_class'] = self._model_class
        data['model_name'] = self._model_name
        data["index"] = self.index
        data["params"] = {}
        for port in self.param_ports:
            data["params"][port.port_label] = port.port_value
        data["bools"] = {}
        for port in self.bool_ports:
            data["bools"][port.port_label] = port.port_value
        data["output_format"] = self.get_selected_format()
        return data