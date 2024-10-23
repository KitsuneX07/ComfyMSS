from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QPen

class CircularProgress(QWidget):
    def __init__(
        self,
        value=0,
        progress_width=10,
        is_rounded=True,
        max_value=100,
        progress_color="#39c5bb",
        enable_text=True,
        font_family="Segoe UI",
        font_size=12,
        suffix="%",
        text_color="#39c5bb",
        enable_bg=True,
        bg_color="#44475a"
    ):
        super().__init__()
        self.current_value = value
        self.target_value = value
        self.progress_width = progress_width
        self.progress_rounded_cap = is_rounded
        self.max_value = max_value
        self.progress_color = progress_color
        self.enable_text = enable_text
        self.font_family = font_family
        self.font_size = font_size
        self.suffix = suffix
        self.text_color = text_color
        self.enable_bg = enable_bg
        self.bg_color = bg_color

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(15)

    def add_shadow(self, enable):
        if enable:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)
            shadow.setYOffset(0)
            shadow.setColor(QColor(0, 0, 0, 80))
            self.setGraphicsEffect(shadow)

    def set_value(self, value):
        self.target_value = value

    def animate(self):
        if self.current_value < self.target_value:
            self.current_value += 1
        elif self.current_value > self.target_value:
            self.current_value -= 1
        self.repaint()

    def paintEvent(self, e):
        width = self.width() - self.progress_width
        height = self.height() - self.progress_width
        margin = self.progress_width / 2
        value = self.current_value * 360 / self.max_value

        paint = QPainter(self)
        paint.setRenderHint(QPainter.Antialiasing)
        paint.setFont(QFont(self.font_family, self.font_size))

        rect = QRect(0, 0, self.width(), self.height())
        paint.setPen(Qt.NoPen)

        pen = QPen()
        pen.setWidth(self.progress_width)

        if self.progress_rounded_cap:
            pen.setCapStyle(Qt.RoundCap)

        if self.enable_bg:
            pen.setColor(QColor(self.bg_color))
            paint.setPen(pen)
            paint.drawArc(margin, margin, width, height, 0, 360 * 16)

        pen.setColor(QColor(self.progress_color))
        paint.setPen(pen)
        paint.drawArc(margin, margin, width, height, -90 * 16, -value * 16)

        if self.enable_text:
            pen.setColor(QColor(self.text_color))
            paint.setPen(pen)
            paint.drawText(rect, Qt.AlignCenter, f"{self.current_value}{self.suffix}")

        paint.end()

if __name__ == '__main__':
    app = QApplication([])

    window = QWidget()
    layout = QVBoxLayout(window)

    circular_progress = CircularProgress(value=25)  # Starting value
    circular_progress.setFixedSize(120, 120)

    layout.addWidget(circular_progress)

    window.setWindowTitle("Smooth Circular Progress")
    window.show()

    # Simulate updating the progress
    def update():
        from random import randint
        new_value = randint(0, 100)
        circular_progress.set_value(new_value)

    # Timer to simulate periodic updates
    QTimer.singleShot(1000, update)

    app.exec()