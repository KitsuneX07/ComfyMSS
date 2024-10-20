from PySide6.QtWidgets import QGraphicsView, QMenu
from PySide6.QtGui import QPainter, QMouseEvent, QKeyEvent, QDragEnterEvent, QDragMoveEvent, QFont
from PySide6.QtCore import Qt, QEvent, QPointF
from edge import NodeEdge, DraggingEdge
from node import Node
from node_port import NodePort, InputPort, OutputPort
from nodes.model_node import MSSTModelNode, VRModelNode, ModelNode
from nodes.data_flow_node import InputNode, OutputNode
from thread import InferenceThread
import json
import os
import shutil
import logging
TEMP_PATH = "tmpdir"


class ComfyUIView(QGraphicsView):
    def __init__(self, scene, log_window, parent=None):
        super().__init__(parent)
        self._scene = scene
        self.log_window = log_window
        self.edges = []
        self.nodes = []
        self.input_node = None
        self.setScene(self._scene)
        self._scene.set_view(self)

        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.TextAntialiasing |
                            QPainter.SmoothPixmapTransform |
                            QPainter.LosslessImageRendering)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        # Hide scrollbars
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # scale
        self._zoom_clamp = [0.2, 2]
        self._zoom_factor = 1.05
        self._view_scale = 1.0
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # Scale relative to mouse position
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Disable drag mode
        self._drag_mode = False
        # Draggable edges
        self._drag_edge = None
        self._drag_edge_mode = False

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat('application/json'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat('application/json'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat('application/json'):
            item_data = event.mimeData().data('application/json')
            model_info = json.loads(item_data.data().decode('utf-8'))
            pos = self.mapToScene(event.pos()).toPoint()
            self.create_node(model_info, [pos.x(), pos.y()])
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton:
            self.middle_button_pressed(event)
        elif event.button() == Qt.LeftButton:
            self.left_button_pressed(event)
        elif event.button() == Qt.RightButton:
            self.right_button_pressed(event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton:
            self.middle_button_released(event)
        elif event.button() == Qt.LeftButton:
            self.left_button_released(event)
        elif event.button() == Qt.RightButton:
            self.right_button_released(event)
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton:
            self.reset_scale()
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            zoom_factor = self._zoom_factor
        else:
            zoom_factor = 1 / self._zoom_factor
        self._view_scale *= zoom_factor
        if self._view_scale < self._zoom_clamp[0] or self._view_scale > self._zoom_clamp[1]:
            zoom_factor = 1.0
            self._view_scale = self._last_scale
        self._last_scale = self._view_scale
        self.scale(zoom_factor, zoom_factor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_edge_mode:
            self._drag_edge.update_position(self.mapToScene(event.pos()))
        else:
            super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Delete:
            self.remove_selected_items()
        else:
            return super().keyPressEvent(event)

    def middle_button_pressed(self, event):
        if self.itemAt(event.pos()) is not None:
            return
        else:
            release_event = QMouseEvent(QEvent.MouseButtonRelease, event.pos(), Qt.LeftButton, Qt.NoButton, event.modifiers())
            super().mouseReleaseEvent(release_event)

            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._drag_mode = True
            click_event = QMouseEvent(QEvent.MouseButtonPress, event.pos(), Qt.LeftButton, Qt.NoButton, event.modifiers())
            super().mousePressEvent(click_event)

    def middle_button_released(self, event):
        release_event = QMouseEvent(QEvent.MouseButtonRelease, event.pos(), Qt.LeftButton, Qt.NoButton, event.modifiers())
        super().mouseReleaseEvent(release_event)

        self.setDragMode(QGraphicsView.RubberBandDrag)
        self._drag_mode = False

    def left_button_pressed(self, event: QMouseEvent):
        mouse_pos = event.pos()
        item = self.itemAt(mouse_pos)
        # print('Item:', item.__class__.__name__)
        if item.__class__.__name__ == 'OutputPort' or item.__class__.__name__ == 'InputPort':
            print('Dragging edge')
            self._drag_edge_mode = True
            self.create_dragging_edge(item)
        else:
            super().mousePressEvent(event)

    def create_dragging_edge(self, port: NodePort):
        port_pos = port.get_port_pos()
        if port.port_type == NodePort.PORT_TYPE_INPUT or port.port_type == NodePort.PORT_TYPE_OUTPUT:
            drag_from_source = True
        else:
            drag_from_source = False
        if self._drag_edge is None:
            self._drag_edge = DraggingEdge(port_pos,
                                           port_pos,
                                           edge_color=port._port_color,
                                           drag_from_source=drag_from_source,
                                           scene=self._scene)

            self._drag_edge.set_first_port(port)
            self._scene.addItem(self._drag_edge)

    def left_button_released(self, event: QMouseEvent):
        if self._drag_edge_mode:
            self._drag_edge_mode = False
            item = self.itemAt(event.pos())
            if item.__class__.__name__ == 'OutputPort' or item.__class__.__name__ == 'InputPort':
                self._drag_edge.set_second_port(item)
                edge = self._drag_edge.create_node_edge()
                if edge is not None:
                    self.edges.append(edge)
            self._scene.removeItem(self._drag_edge)
            self._drag_edge = None

        super().mouseReleaseEvent(event)

    def right_button_pressed(self, event):
        if self._scene.selectedItems():
            return
        
        super().mousePressEvent(event)

    def right_button_released(self, event):
        super().mouseReleaseEvent(event)

    def set_menu_widget(self, widget):
        self._menu_widget = widget

    def reset_scale(self):
        self.resetTransform()
        self._view_scale = 1.0

    def add_node(self, node, pos = [0, 0], index = None):
        self._scene.addItem(node)
        node.setPos(pos[0], pos[1])
        node.set_scene(self._scene)
        if index is not None:
            node.index = index
        else:
            node.index = len(self.nodes)
        self.nodes.append(node)

    def create_node(self, model_info, pos):

        if isinstance(model_info, str):
            if model_info == "InputNode":
                if self.input_node is not None:
                    raise Exception("Input node already exists")
                else:
                    new_node = InputNode()
                    self.input_node = new_node     
            elif model_info == "OutputNode":
                new_node = OutputNode()
        else:
            model_class = model_info.get("model_class")
            if model_class == "vr_models":
                model_name = model_info.get("name")
                new_node = VRModelNode(model_class = model_class, model_name = model_name)
            else:
                model_type = model_info.get("model_type")
                model_name = model_info.get("name")
                new_node = MSSTModelNode(model_class = model_class, model_name = model_name, model_type = model_type)

        self.add_node(new_node, pos = pos, index = None)

    def remove_selected_items(self):
        selected_items = self._scene.selectedItems()
        for item in selected_items:
            if item in self.edges:
                self.edges.remove(item)
                item._source_port.remove_edge()
                item._des_port.remove_edge()
                item.update()
            elif item in self.nodes:
                if item == self.input_node:
                    self.input_node = None
                item.remove_edge()
                self.nodes.remove(item)
                item.update()
            self._scene.removeItem(item)
            
    def clear_editor(self):
        for item in self._scene.items():
            self._scene.removeItem(item)
        self.edges = []
        self.nodes = []
        self.input_node = None
        
    def debug(self):
        for i in range(10):
            self.run()
            shutil.rmtree('output', ignore_errors=True)


    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        context_menu.addAction("delete selected items", self.remove_selected_items)
        context_menu.addAction("reset scale", self.reset_scale)
        context_menu.addAction("clear editor", self.clear_editor)
        context_menu.addAction("run", self.run)
        context_menu.addAction("save", self.save)
        context_menu.addAction("debug", self.debug)

        context_menu.exec(event.globalPos())

    def run(self):

        self.inference_thread = None

        shutil.rmtree(TEMP_PATH, ignore_errors=True)

        if self.inference_thread is not None and self.inference_thread.isRunning():
            logging.error('Previous thread is still running.')
            return
        
        self.inference_thread = InferenceThread(self.input_node)
        self.inference_thread.log_signal.connect(self.add_log)

        # 启动线程
        self.inference_thread.start()

    def add_log(self, message):
        self.log_window.append(message)
        self.log_window.ensureCursorVisible()    
            
    def save(self, file_path:str) -> None:
        data = {}
        data['nodes'] = {}
        for node in self.nodes:
            data['nodes'][node.index] = node.save()
        data['edges'] = {}
        edge_index = 0
        for edge in self.edges:
            data['edges'][edge_index] = edge.save()
            edge_index += 1
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            print(f'Saved to {os.path.abspath("./presets/1.preset")}')

    def load(self, file_path: str) -> None:
        self.clear_editor()
        with open(file_path, 'r') as f:
            data = json.load(f)
            nodes = data.get('nodes')
            edges = data.get('edges')
            for index, node_data in nodes.items():
                model_class = node_data.get('model_class')
                if model_class == 'InputNode':
                    node = InputNode(input_path = node_data.get('input_path'))
                    self.input_node = node
                elif model_class == 'OutputNode':
                    node = OutputNode(output_path = node_data.get('output_path'))
                elif model_class == 'vr_models':
                    node = VRModelNode(
                        model_class = node_data.get('model_class'),
                        model_name = node_data.get('model_name')
                        )
                    for param in node_data.get('params'):
                        for param_port in node.param_ports:
                            if param_port.port_label == param:
                                param_port.line_edit.setText(str(node_data.get('params').get(param)))
                                break
                    
                    for bool in node_data.get('bools'):
                        for bool_port in node.bool_ports:
                            if bool_port.port_label == bool:
                                value = node_data.get('bools').get(bool)
                                if value:
                                    bool_port.checkbox.setChecked(True)
                                break

                    output_format = node_data.get('output_format')
                    node.update_output_format(output_format)

                else:
                    node = MSSTModelNode(
                        model_class = node_data.get('model_class'),
                        model_name = node_data.get('model_name'),
                        model_type = node_data.get('model_type')
                        )
                    for param in node_data.get('params'):
                        for param_port in node.param_ports:
                            if param_port.port_label == param:
                                param_port.line_edit.setText(str(node_data.get('params').get(param)))
                                break
                    
                    for bool in node_data.get('bools'):
                        for bool_port in node.bool_ports:
                            if bool_port.port_label == bool:
                                value = node_data.get('bools').get(bool)
                                if value:
                                    bool_port.checkbox.setChecked(True)
                                break

                    output_format = node_data.get('output_format')
                    node.update_output_format(output_format)

                self.add_node(node, pos = node_data.get('pos'), index = index)

            for index, edge_data in edges.items():
                source_node_index, source_port_label = edge_data.get('source_port')
                des_node_index, des_port_label = edge_data.get('des_port')
                for port in self.nodes[int(source_node_index)].output_ports:
                    if port.port_label == source_port_label:
                        source_port = port
                        break

                for port in self.nodes[int(des_node_index)].input_ports:
                    if port.port_label == des_port_label:
                        des_port = port
                        break
                
                edge = NodeEdge(source_port, des_port, self._scene)
                self.edges.append(edge)