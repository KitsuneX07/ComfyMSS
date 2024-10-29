from PySide6.QtCore import QThread, Signal
from contextlib import redirect_stdout
from huggingface_hub import hf_hub_url
import sys
import os
sys.path.append(os.getcwd())
from inference.comfy_infer import ComfyMSST, ComfyVR
from time import sleep
import time
import requests


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

class DownloadThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    speed_signal = Signal(float)

    def __init__(self, model_type, model_name):
        super().__init__()
        self.model_type = model_type
        self.model_name = model_name
        # 设置下载路径为指定的目录结构
        self.download_path = f"./pretrain/{self.model_type}"

    def run(self):
        try:
            url = hf_hub_url(
                repo_id="Sucial/MSST-WebUI",
                filename=f"All_Models/{self.model_type}/{self.model_name}",
                endpoint="https://hf-mirror.com"
            )
            self.log_signal.emit(f"Downloading {self.model_name} from {url}")
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 1024  # 1 KB
            downloaded_size = 0
            start_time = time.time()

            # 确保下载路径存在
            os.makedirs(self.download_path, exist_ok=True)
            file_path = os.path.join(self.download_path, self.model_name)

            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed = (downloaded_size / 1024 / 1024) / elapsed_time  # MB/s
                            self.speed_signal.emit(speed)
                        progress = int((downloaded_size / total_size) * 100)
                        self.progress_signal.emit(progress)

            self.log_signal.emit(f"{self.model_name} download completed. Saved to {file_path}")

        except Exception as e:
            self.log_signal.emit(f"DownloadThread Error: {str(e)}")
