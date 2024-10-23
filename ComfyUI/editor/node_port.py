import sys

sys.path.append('.')

from PySide6.QtWidgets import QGraphicsItem, QLineEdit, QGraphicsProxyWidget, QCheckBox, QApplication
from PySide6.QtGui import QColor, QPen, QBrush, QPainter, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRectF, QPointF
from config import EditorConfig, NodeConfig


class NodePort(QGraphicsItem):
    PORT_TYPE_INPUT = 1001
    PORT_TYPE_OUTPUT = 1002
    PORT_TYPE_PARAM = 1003
    PORT_TYPE_BOOL = 1004

    def __init__(self, port_label = '', port_color = '#ffffff', port_type = PORT_TYPE_INPUT, parent = None,
                 edges = None):
        super().__init__(parent)
        self.port_pos = None
        self.parent_node = None
        self._scene = None
        self.port_label = port_label  # 端口标签
        self._port_color = port_color  # 端口颜色
        self.port_type = port_type  # 端口类型：输入、输出、参数、布尔类型

        # 初始化画笔和画刷
        self._pen_default = QPen(QColor(self._port_color))
        self._pen_default.setWidthF(1.5)
        self._brush_default = QBrush(QColor(self._port_color))
        
        current_font = QApplication.font()
        new_font = QFont(current_font.family(), 14)
        self._port_font = new_font
        self._font_metrics = QFontMetrics(self._port_font)
        self._port_icon_size = NodeConfig.port_icon_size  # 端口图标大小
        self._port_label_size = self._font_metrics.horizontalAdvance(self.port_label)  # 端口标签宽度
        self._port_width = self._port_icon_size + self._port_label_size  # 端口宽度

        self.port_value = None  # 端口值
        self.has_value_set = False  # 是否设置了值

        self.edges = [] if edges is None else edges
        self.connected_ports: list[NodePort] = [] if edges is None else edges

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._port_width, self._port_icon_size)

    def add_to_parent_node(self, parent_node, scene):
        self.setParentItem(parent_node)
        self.parent_node = parent_node
        self._scene = scene

        if self.port_type == NodePort.PORT_TYPE_INPUT:
            self.setPos(0, 0)
        elif self.port_type == NodePort.PORT_TYPE_OUTPUT:
            self.setPos(parent_node.boundingRect().width() - self._port_width, 0)

    def get_port_pos(self):
        self.port_pos = self.scenePos()
        if self.port_type == NodePort.PORT_TYPE_INPUT:
            return QPointF(self.port_pos.x() + 0.5 * self._port_icon_size,
                           self.port_pos.y() + 0.5 * self._port_icon_size)
        elif self.port_type == NodePort.PORT_TYPE_OUTPUT:
            return QPointF(self.port_pos.x() + 0.5 * self._port_icon_size + self._port_label_size + 5,
                           self.port_pos.y() + 0.5 * self._port_icon_size)

    def add_edge(self, edge, connected_port):
        if self.port_type == NodePort.PORT_TYPE_INPUT:
            self.edges.append(edge)
            self.connected_ports.append(connected_port)
        else:
            self.edges.append(edge)
            self.connected_ports.append(connected_port)
            self.parent_node.downstream_nodes.append(connected_port.parent_node)
            self.parent_node.downstream_edges.append(edge)

    def remove_edge(self):
        if self.port_type == NodePort.PORT_TYPE_INPUT:
            if len(self.connected_ports):
                self.connected_ports[0].parent_node.downstream_nodes.remove(self.parent_node)
        for edge in self.edges:
            print('Removing edge:', edge)
            self.parent_node._scene.removeItem(edge)
            edge._des_port.edges.remove(edge)
            edge._source_port.edges.remove(edge)
            edge._des_port.update()
            edge._source_port.update()
            self.update()

    def is_connected(self):
        return len(self.edges) > 0

    def set_port_value(self, value):
        self.port_value = value
        self.has_value_set = True


class InputPort(NodePort):

    def __init__(self, port_label = ''):
        super().__init__(port_label = port_label, port_type = NodePort.PORT_TYPE_INPUT)

    def paint(self, painter: QPainter, option, widget) -> None:
        square = QRectF(0, 0, self._port_icon_size, self._port_icon_size)
        painter.setPen(self._pen_default)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(square)

        if self.is_connected():
            small_square = QRectF(
                self._port_icon_size / 4,
                self._port_icon_size / 4,
                self._port_icon_size / 2,
                self._port_icon_size / 2
            )
            painter.setBrush(self._brush_default)
            painter.drawRect(small_square)

        painter.setFont(self._port_font)
        painter.drawText(QRectF(self._port_icon_size + 5, 0, self._port_label_size, self._port_icon_size),
                         Qt.AlignLeft | Qt.AlignVCenter, self.port_label)


class OutputPort(NodePort):

    def __init__(self, port_label = ''):
        super().__init__(port_label = port_label, port_type = NodePort.PORT_TYPE_OUTPUT)

    def paint(self, painter: QPainter, option, widget) -> None:
        painter.setPen(self._pen_default)
        painter.setFont(self._port_font)
        painter.drawText(QRectF(0, 0, self._port_label_size, self._port_icon_size),
                         Qt.AlignRight | Qt.AlignVCenter, self.port_label)

        square = QRectF(self._port_label_size + 5, 0, self._port_icon_size, self._port_icon_size)
        painter.setPen(self._pen_default)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(square)

        if self.is_connected():
            small_square = QRectF(
                self._port_label_size + self._port_icon_size / 4 + 5,
                self._port_icon_size / 4,
                self._port_icon_size / 2,
                self._port_icon_size / 2
            )
            painter.setBrush(self._brush_default)
            painter.drawRect(small_square)


class ParamPort(NodePort):

    def __init__(self, port_label = '', port_color = '#ffffff', default_value = '', parent = None):
        super().__init__(port_label = port_label, port_color = port_color, port_type = NodePort.PORT_TYPE_PARAM,
                         parent = parent)

        self._default_value = default_value
        self.port_value = self._default_value
        self.has_value_set = True
        self.line_edit = QLineEdit(self.port_label)
        self.line_edit.setText(str(self._default_value))
        self.line_edit.setMaximumHeight(self._port_icon_size - 3)

        self._proxy_widget = QGraphicsProxyWidget(self)
        self._proxy_widget.setWidget(self.line_edit)

        self._port_label_size = self._font_metrics.horizontalAdvance(self.port_label)
        self._port_textbox_width = 100
        self._port_width = self._port_label_size + self._port_textbox_width
        self.line_edit.textChanged.connect(self.update_value)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._port_width, self._port_icon_size)

    def paint(self, painter: QPainter, option, widget) -> None:
        painter.setPen(self._pen_default)
        painter.setFont(self._port_font)
        painter.drawText(QRectF(0, 0, self._port_label_size, self._port_icon_size),
                         Qt.AlignLeft | Qt.AlignVCenter, self.port_label)

        self._proxy_widget.setGeometry(
            QRectF(self._port_label_size + 5, 2, self._port_textbox_width, self._port_icon_size))

    def update_value(self):
        self.port_value = self.line_edit.text()
        self.has_value_set = True
    


class BoolPort(NodePort):
    def __init__(self, port_label='', port_color='#ffffff', default_value=False, parent=None):
        super().__init__(port_label=port_label, port_color=port_color, port_type=NodePort.PORT_TYPE_BOOL, parent=parent)

        self._default_value = default_value

        # 创建复选框并设置默认值
        self.checkbox = QCheckBox(self.port_label)
        self.checkbox.setChecked(self._default_value)
        self.checkbox.setAttribute(Qt.WA_TranslucentBackground)

        # 使用 QGraphicsProxyWidget 集成复选框到图形项中
        self._proxy_widget = QGraphicsProxyWidget(self)
        self._proxy_widget.setWidget(self.checkbox)

        # 计算标签和复选框大小
        # self._port_label_size = self._font_metrics.horizontalAdvance(self.port_label)
        self._port_checkbox_width = 16

        # 计算总宽度
        self._port_width = self._port_label_size + self._port_checkbox_width
        self.checkbox.stateChanged.connect(self.update_value)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._port_width, self._port_icon_size)

    def paint(self, painter: QPainter, option, widget) -> None:
        painter.setPen(self._pen_default)
        painter.setFont(self._port_font)

        # # 绘制端口标签文本
        # label_rect = QRectF(0, 0, self._port_label_size, self._port_icon_size)
        # painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, self.port_label)

        # 放置复选框
        self._proxy_widget.setPos(0, (self._port_icon_size - self._port_checkbox_width) / 2)

    def update_value(self):
        self.port_value = self.checkbox.isChecked()
        self.has_value_set = True