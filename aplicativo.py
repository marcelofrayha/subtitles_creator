import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QTextEdit, QProgressBar, QLineEdit, QSpinBox, QLabel, QHBoxLayout, QComboBox, QGraphicsOpacityEffect, QSpacerItem, QSizePolicy, QScrollArea
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPalette, QBrush, QPixmap, QIcon, QColor
import tradutor_de_video
from download_youtube_video import download_youtube_video
import re

def remove_brackets(text):
    return re.sub(r'\[.*?\]', '', text)

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)

    def __init__(self, video_path, context_size, min_silence_len, target_lang):
        super().__init__()
        self.video_path = video_path
        self.context_size = context_size
        self.min_silence_len = min_silence_len
        self.target_lang = target_lang

    def run(self):
        try:
            print(f"Video Selecionado: {self.video_path}, Tamanho do Contexto da Tradução: {self.context_size}, Velocidade da fala: {self.min_silence_len}, Target language: {self.target_lang}")
            video_name = os.path.splitext(os.path.basename(self.video_path))[0]
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            output_srt = os.path.join(downloads_folder, f"{video_name}.srt")
            
            tradutor_de_video.main(
                self.video_path,
                output_srt,
                self.context_size,
                update_progress=self.update_progress.emit,
                update_output=lambda x: self.update_output.emit(remove_brackets(x)),
                min_silence_len=self.min_silence_len,
                target_lang=self.target_lang
            )
            
            self.update_output.emit(f"SRT file saved in: {output_srt}")
        except Exception as e:
            print(f"Debug: Error in WorkerThread: {str(e)}")
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
        self.setWindowTitle("Criador Automático de Legendas")
        self.setGeometry(100, 100, 600, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 20, 10, 10)  # Aumentar a margem superior para 20

        # Adicionar espaço extra no topo
        layout.addSpacing(10)

        # Configurar a imagem de fundo
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "rosetta_logo.png")
        
        background_label = QLabel(self)
        background_pixmap = QPixmap(image_path)
        background_label.setPixmap(background_pixmap)
        background_label.setScaledContents(True)
        background_label.resize(self.size())

        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.15)
        background_label.setGraphicsEffect(opacity_effect)

        background_label.lower()

        # Adicionar título com estilo egípcio
        title_label = QLabel("Rosetta Stone Powered by AI")
        title_font = QFont("Papyrus", 24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setContentsMargins(0, 10, 0, 30)
        layout.addWidget(title_label)

        # Espaçador após o título (pequeno e fixo)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Container para os elementos de entrada
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        
        # Adicionar os elementos de entrada ao input_layout
        youtube_layout = QHBoxLayout()
        youtube_layout.setSpacing(5)
        self.youtube_url_input = QLineEdit()
        self.youtube_url_input.setPlaceholderText("Enter YouTube URL")
        youtube_layout.addWidget(self.youtube_url_input)
        self.download_button = QPushButton("Download Video do YouTube")
        self.download_button.clicked.connect(self.download_youtube)
        youtube_layout.addWidget(self.download_button)
        input_layout.addLayout(youtube_layout)

        ou_label = QLabel("OU")
        ou_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ou_label.setContentsMargins(0, 2, 0, 2)
        input_layout.addWidget(ou_label)

        self.select_button = QPushButton("Selecione Video")
        self.select_button.clicked.connect(self.select_video)
        input_layout.addWidget(self.select_button)

        input_layout.addSpacing(20)

        config_label = QLabel("Configure sua legenda")
        config_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        config_label.setStyleSheet("font-weight: bold;")
        input_layout.addWidget(config_label)

        input_layout.addSpacing(10)

        language_layout = QHBoxLayout()
        language_label = QLabel("Idioma da legenda:")
        language_layout.addWidget(language_label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "Português", "English", "Español", "Français", "Deutsch", "Italiano",
            "Nederlands", "Polski", "Русский", "日本語", "中文 (简体)", "中 (繁體)",
            "한국어", "العربية", "हिन्दी", "Türkçe", "Svenska", "Dansk", "Norsk",
            "Suomi", "Ελληικά", "עברית", "Esperanto", "Latin"
        ])
        language_layout.addWidget(self.language_combo)
        
        input_layout.addLayout(language_layout)

        input_layout.addSpacing(10)

        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(5)
        context_label = QLabel("Tamanho do contexto (0-10):")
        inputs_layout.addWidget(context_label)
        self.context_spinbox = QSpinBox()
        self.context_spinbox.setRange(0, 10)
        self.context_spinbox.setValue(2)
        self.context_spinbox.setToolTip("Define o número de frases anteriores e posteriores a serem consideradas para melhorar a tradução. Um valor maior pode melhorar a precisão, mas aumenta o tempo de processamento.")
        inputs_layout.addWidget(self.context_spinbox)
        inputs_layout.addSpacing(10)
        silence_label = QLabel("Duração mínima de silêncio (ms):")
        inputs_layout.addWidget(silence_label)
        self.silence_spinbox = QSpinBox()
        self.silence_spinbox.setRange(100, 2000)
        self.silence_spinbox.setValue(500)
        self.silence_spinbox.setSingleStep(100)
        self.silence_spinbox.setToolTip("Define a duração mínima de silêncio (em milissegundos) para considerar uma pausa na fala. Valores menores podem resultar em legendas mais precisas, mas podem aumentar o número de legendas geradas.")
        inputs_layout.addWidget(self.silence_spinbox)
        input_layout.addLayout(inputs_layout)

        input_layout.addSpacing(10)

        self.process_button = QPushButton("Criar Legendas")
        self.process_button.clicked.connect(self.process_video)
        input_layout.addWidget(self.process_button)

        layout.addWidget(input_container)

        # Espaçador flexível antes do progress bar (fator de estiramento menor)
        layout.addStretch(1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)

        # Caixa de informação com rolagem
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        scroll_area.setWidget(self.output_text)
        scroll_area.setMinimumHeight(300)  # Definir altura mínima para o scroll area
        layout.addWidget(scroll_area)

        # Espaçador flexível após a caixa de informação (fator de estiramento maior)
        layout.addStretch(2)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        icon_path = os.path.join(current_dir, "rosetta_logo.png")
        app_icon = QIcon(icon_path)
        self.setWindowIcon(app_icon)

        common_style = """
        QWidget {
            font-family: Papyrus, 'Trajan Pro', 'Cinzel', 'Times New Roman', serif;
            font-size: 16px;
            padding: 10px;
            margin: 4px 2px;
            border-radius: 8px;
            min-height: 20px;
        }
        """

        button_style = common_style + """
        QPushButton {
            background-color: #66BB6A;
            border: none;
            color: white;
            text-align: center;
            text-decoration: none;
            min-width: 200px;
        }
        QPushButton:hover {
            background-color: #81C784;
        }
        """

        input_style = common_style + """
        QLineEdit, QSpinBox, QComboBox {
            background-color: white;
            border: 1px solid #BDBDBD;
        }
        """

        self.setStyleSheet(input_style)
        self.youtube_url_input.setStyleSheet(input_style)
        self.context_spinbox.setStyleSheet(input_style)
        self.silence_spinbox.setStyleSheet(input_style)
        self.language_combo.setStyleSheet(input_style)

        self.download_button.setStyleSheet(button_style)
        self.select_button.setStyleSheet(button_style)
        self.process_button.setStyleSheet(button_style)

        progress_bar_style = """
        QProgressBar {
            border: 1px solid #BDBDBD;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #66BB6A;
            width: 10px;
        }
        """
        self.progress_bar.setStyleSheet(progress_bar_style)

    def reset_progress_bar(self):
        self.progress_bar.setValue(0)

    def download_youtube(self):
        url = self.youtube_url_input.text()
        if not url:
            self.output_text.append("Entre a URL do Youtube.")
            return

        self.reset_progress_bar()
        self.download_thread = DownloadThread(url)
        self.download_thread.update_progress.connect(self.update_download_progress)
        self.download_thread.update_output.connect(self.update_output)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()
        self.output_text.append("Baixando video...")

    def update_download_progress(self, d):
        print("Debug: update_download_progress called")
        print(f"Debug: d = {d}")
        if not isinstance(d, dict):
            print(f"Unexpected data type: {type(d)}")
            return

        status = d.get('status')
        if status == 'downloading':
            percent_str = d.get('_percent_str')
            if percent_str is None:
                print("No '_percent_str' found in download data")
                return
            
            try:
                percent = float(percent_str.replace('%', '').strip())
                self.progress_bar.setValue(int(percent))
            except (ValueError, AttributeError) as e:
                print(f"Error parsing progress: {e}")
        elif status == 'finished':
            self.progress_bar.setValue(100)
            self.output_text.append("Download completed. Processing video...")
        else:
            print(f"Unknown status: {status}")

    def download_finished(self, output_path):
        self.video_path = output_path
        self.output_text.append(f"Video baixado: {output_path}")
        self.progress_bar.setValue(100)

    def select_video(self):
        self.reset_progress_bar() 
        file_dialog = QFileDialog()
        self.video_path, _ = file_dialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if self.video_path:
            self.output_text.append(f"Vídeo selecionado: {self.video_path}")

    def process_video(self):
        if not self.video_path:
            self.output_text.append("Selecione um vídeo ou faça o download do Youtube antes de prosseguir.")
            return

        self.reset_progress_bar() 
        context_size = self.context_spinbox.value()
        min_silence_len = self.silence_spinbox.value()
        target_lang = self.get_target_lang_code()
        print(f"Vídeo em processamento: {self.video_path}, Tamanho do Contexto de Tradução: {context_size}, Velocidade da fala: {min_silence_len}, Idioma alvo: {target_lang}")
        self.worker = WorkerThread(self.video_path, context_size, min_silence_len, target_lang)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.update_output.connect(self.update_output)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()
        print("Debug: WorkerThread started")

    def get_target_lang_code(self):
        lang_map = {
            "Português": "pt", "English": "en", "Español": "es", "Français": "fr",
            "Deutsch": "de", "Italiano": "it", "Nederlands": "nl", "Polski": "pl",
            "Русский": "ru", "日本語": "ja", "中文 (简体)": "zh-CN", "中文 (繁體)": "zh-TW",
            "한국어": "ko", "العربية": "ar", "हिन्दी": "hi", "Türkçe": "tr",
            "Svenska": "sv", "Dansk": "da", "Norsk": "no", "Suomi": "fi",
            "Ελνικά": "el", "עברית": "he", "Esperanto": "eo", "Latin": "la"
        }
        selected_lang = self.language_combo.currentText()
        return lang_map.get(selected_lang, "pt")  # Default to Portuguese if not found

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, text):
        self.output_text.append(text)

    def resizeEvent(self, event):
        background_label = self.findChild(QLabel)
        if background_label:
            background_label.resize(self.size())
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    app.setWindowIcon(window.windowIcon())  # Define o ícone para toda a aplicação
    window.show()
    sys.exit(app.exec())