from PySide6.QtCore import QThread, Signal
from contextlib import redirect_stdout

class QTextEditStdout:
    def __init__(self, log_signal):
        self.log_signal = log_signal

    def write(self, message):
        if message.strip():
            self.log_signal.emit(message)

    def flush(self):
        pass

class InferenceThread(QThread):
    log_signal = Signal(str)

    def __init__(self, input_node):
        super().__init__()
        self.input_node = input_node

    def run(self):
        try:
            self.log_signal.emit('Running editor')

            if self.input_node is None:
                self.log_signal.emit('No input node was added!')
                return

            # Redirect stdout to QTextEditStdout
            with redirect_stdout(QTextEditStdout(self.log_signal)):
                self._process_node(self.input_node)

            self.log_signal.emit('Process completed.')

        except Exception as e:
            self.log_signal.emit(f'Error: {str(e)}')
   

    def _process_node(self, node):
        if node is None:
            return
        node.run()
        for downstream_node in node.downstream_nodes:
            self._process_node(downstream_node)