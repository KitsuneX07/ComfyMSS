from PySide6.QtCore import QThread, Signal
from contextlib import redirect_stdout
from inference.comfy_infer import ComfyMSST, ComfyVR
from time import sleep

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
            self.quit()

        except Exception as e:
            self.log_signal.emit(f'InferenceThread Error: {str(e)}')
   

    def _process_node(self, node):
        if node is None:
            return
        node.update_params()
        if node.__class__.__name__ == "VRModelNode":
            params = node.params
            separator = ComfyVR(
                model_file=params["model_file"],
                output_dir=params["output_folder"],
                invert_using_spec=params["invert_using_spec"],
                use_cpu=params["use_cpu"],
                vr_params=params["vr_params"],
                debug=True
            )
            separator.process_folder(params["input_path"])
            separator.del_cache()
            sleep(5)

        elif node.__class__.__name__ == "MSSTModelNode":
            params = node.params
            separator = ComfyMSST(
                model_type = params["model_type"],
                config_path = params["config_path"],
                model_path = params["model_path"],
                device = 'auto',
                device_ids = [0],
                output_format = params["output_format"],
                use_tta = params["use_tta"],
                store_dirs = params["store_dirs"],
                debug = True
            )
            separator.process_folder(params["input_path"])
            separator.del_cache()
            sleep(5)

        for downstream_node in node.downstream_nodes:
            self._process_node(downstream_node)