import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QTextEdit, QProgressBar, QLineEdit
from PyQt6.QtCore import QThread, pyqtSignal
import tradutor_de_video
from download_youtube_video import download_youtube_video
import re

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        try:
            video_name = os.path.splitext(os.path.basename(self.video_path))[0]
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            output_srt = os.path.join(downloads_folder, f"{video_name}.srt")
            tradutor_de_video.main(self.video_path, output_srt, self.update_progress.emit, self.update_output.emit)
            self.update_output.emit(f"SRT file saved in: {output_srt}")
        except Exception as e:
            self.update_output.emit(f"Error: {str(e)}")

class DownloadThread(QThread):
    update_progress = pyqtSignal(dict)  # Change this to dict
    update_output = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            output_path = download_youtube_video(self.url, self.update_progress.emit, downloads_folder)
            self.finished.emit(output_path)
        except Exception as e:
            self.update_output.emit(f"Error downloading video: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Subtitle Generator")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.youtube_url_input = QLineEdit()
        self.youtube_url_input.setPlaceholderText("Enter YouTube URL")
        layout.addWidget(self.youtube_url_input)

        self.download_button = QPushButton("Download YouTube Video")
        self.download_button.clicked.connect(self.download_youtube)
        layout.addWidget(self.download_button)

        self.select_button = QPushButton("Selecione Video")
        self.select_button.clicked.connect(self.select_video)
        layout.addWidget(self.select_button)

        self.process_button = QPushButton("Criar Legendas")
        self.process_button.clicked.connect(self.process_video)
        layout.addWidget(self.process_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.video_path = None

    def reset_progress_bar(self):
        self.progress_bar.setValue(0)

    def download_youtube(self):
        url = self.youtube_url_input.text()
        if not url:
            self.output_text.append("Entre a URL do Youtube.")
            return

        self.reset_progress_bar()  # Reset progress bar before starting download
        self.download_thread = DownloadThread(url)
        self.download_thread.update_progress.connect(self.update_download_progress)
        self.download_thread.update_output.connect(self.update_output)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()
        self.output_text.append("Baixando video...")

    def update_download_progress(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').replace('%', '').strip()
            try:
                value = int(float(percent))
                self.progress_bar.setValue(value)
            except ValueError:
                print(f"Unable to parse progress: {percent}")
        elif d['status'] == 'finished':
            self.progress_bar.setValue(100)
            self.output_text.append("Download completed. Processing video...")

    def download_finished(self, output_path):
        self.video_path = output_path
        self.output_text.append(f"Video baixado: {output_path}")
        self.progress_bar.setValue(100)

    def select_video(self):
        self.reset_progress_bar() 
        file_dialog = QFileDialog()
        self.video_path, _ = file_dialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if self.video_path:
            self.output_text.append(f"Selecione o Vídeo: {self.video_path}")

    def process_video(self):
        self.reset_progress_bar() 
        if not self.video_path:
            self.output_text.append("Selecione um vídeo ou faça o download do Youtube antes de prosseguir.")
            return

        self.reset_progress_bar()  # Reset progress bar before processing
        self.worker = WorkerThread(self.video_path)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.update_output.connect(self.update_output)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, text):
        self.output_text.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())