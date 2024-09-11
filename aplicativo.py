import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, 
                             QFileDialog, QTextEdit, QProgressBar, QLineEdit, QSpinBox, QLabel, 
                             QHBoxLayout, QComboBox, QGridLayout)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFontDatabase, QFont, QPalette, QBrush, QPixmap, QIcon, QColor, QCursor, QPainter
import tradutor_de_video
from download_youtube_video import download_youtube_video
import re

def remove_brackets(text):
    return re.sub(r'\[.*?\]', '', text)

# Dicionário de traduções
translations = {
    "pt": {
        "title": "Pedra Rosetta\nAlimentada por IA",
        "youtube_url": "Digite a URL do YouTube",
        "download_button": "Baixar Vídeo do YouTube",
        "or_label": "OU",
        "select_video": "Selecionar Vídeo",
        "config_label": "Configure sua legenda",
        "language_label": "Idioma da legenda:",
        "context_label": "Tamanho do contexto (0-10):",
        "silence_label": "Duração mínima de silêncio (ms):",
        "create_subtitles": "Criar Legendas"
    },
    "en": {
        "title": "Rosetta Stone\nPowered by AI",
        "youtube_url": "Enter YouTube URL",
        "download_button": "Download YouTube Video",
        "or_label": "OR",
        "select_video": "Select Video",
        "config_label": "Configure your subtitle",
        "language_label": "Subtitle language:",
        "context_label": "Context size (0-10):",
        "silence_label": "Minimum silence duration (ms):",
        "create_subtitles": "Create Subtitles"
    },
    "es": {
        "title": "Piedra Rosetta\nImpulsada por IA",
        "youtube_url": "Ingrese la URL de YouTube",
        "download_button": "Descargar video de YouTube",
        "or_label": "O",
        "select_video": "Seleccionar video",
        "config_label": "Configurar subtítulo",
        "language_label": "Idioma del subtítulo:",
        "context_label": "Tamaño del contexto (0-10):",
        "silence_label": "Duración mínima del silencio (ms):",
        "create_subtitles": "Crear subtítulos"
    },
    "fr": {
        "title": "Pierre Rosette\nPropulsée par l'IA",
        "youtube_url": "Entrez l'URL YouTube",
        "download_button": "Télécharger la vidéo YouTube",
        "or_label": "OU",
        "select_video": "Sélectionner la vidéo",
        "config_label": "Configurer le sous-titre",
        "language_label": "Langue du sous-titre :",
        "context_label": "Taille du contexte (0-10) :",
        "silence_label": "Durée minimale du silence (ms) :",
        "create_subtitles": "Créer des sous-titres"
    },
    "de": {
        "title": "Stein Rosetta\nAngetrieben durch KI",
        "youtube_url": "YouTube-URL eingeben",
        "download_button": "YouTube-Video herunterladen",
        "or_label": "ODER",
        "select_video": "Video auswählen",
        "config_label": "Untertitel konfigurieren",
        "language_label": "Untertitelsprache:",
        "context_label": "Kontextgröße (0-10):",
        "silence_label": "Minimale Stille-Dauer (ms):",
        "create_subtitles": "Untertitel erstellen"
    },
    "it": {
        "title": "Stele Rosetta\nAlimentata dall'IA",
        "youtube_url": "Inserisci l'URL di YouTube",
        "download_button": "Scarica video da YouTube",
        "or_label": "O",
        "select_video": "Seleziona video",
        "config_label": "Configura sottotitoli",
        "language_label": "Lingua dei sottotitoli:",
        "context_label": "Dimensione del contesto (0-10):",
        "silence_label": "Durata minima del silenzio (ms):",
        "create_subtitles": "Crea sottotitoli"
    },
    "nl": {
        "title": "Steen Rosetta\nAangedreven door AI",
        "youtube_url": "Voer YouTube-URL in",
        "download_button": "YouTube-video downloaden",
        "or_label": "OF",
        "select_video": "Selecteer video",
        "config_label": "Configureer ondertiteling",
        "language_label": "Ondertiteltaal:",
        "context_label": "Contextgrootte (0-10):",
        "silence_label": "Minimale stilte duur (ms):",
        "create_subtitles": "Maak ondertiteling"
    },
    "pl": {
        "title": "Kamień Rosetty\nNapędzany AI",
        "youtube_url": "Wprowadź adres URL YouTube",
        "download_button": "Pobierz wideo z YouTube",
        "or_label": "LUB",
        "select_video": "Wybierz wideo",
        "config_label": "Skonfiguruj napisy",
        "language_label": "Język napisów:",
        "context_label": "Rozmiar kontekstu (0-10):",
        "silence_label": "Minimalna długość ciszy (ms):",
        "create_subtitles": "Utwórz napisy"
    },
    "ru": {
        "title": "Розеттский Камень\nна Основе ИИ",
        "youtube_url": "Введите URL YouTube",
        "download_button": "Скачать видео с YouTube",
        "or_label": "ИЛИ",
        "select_video": "Выбрать видео",
        "config_label": "Настроить субтитры",
        "language_label": "Язык субтитров:",
        "context_label": "Размер контекста (0-10):",
        "silence_label": "Минимальная длительность тишины (мс):",
        "create_subtitles": "Создать субтитры"
    },
    "ja": {
        "title": "AI駆動のロゼッタストーン",
        "youtube_url": "YouTubeのURLを入力",
        "download_button": "YouTubeビデオをダウンロード",
        "or_label": "または",
        "select_video": "ビデオを選択",
        "config_label": "字幕を設定",
        "language_label": "字幕言語:",
        "context_label": "コンテキストサイズ (0-10):",
        "silence_label": "最小静寂時間 (ms):",
        "create_subtitles": "字幕を作成"
    },
    "zh-CN": {
        "title": "人工智能驱动的罗塞塔石碑",
        "youtube_url": "输入YouTube网址",
        "download_button": "下载YouTube视频",
        "or_label": "或",
        "select_video": "选择视频",
        "config_label": "配置字幕",
        "language_label": "字幕语言:",
        "context_label": "上下文大小 (0-10):",
        "silence_label": "最小静音持续时间 (毫秒):",
        "create_subtitles": "创建字幕"
    },
    "zh-TW": {
        "title": "人工智慧驅動的羅塞塔石碑",
        "youtube_url": "輸入YouTube網址",
        "download_button": "下載YouTube影片",
        "or_label": "或",
        "select_video": "選擇影片",
        "config_label": "配置字幕",
        "language_label": "字幕語言:",
        "context_label": "上下文大小 (0-10):",
        "silence_label": "最小靜音持續時間 (毫秒):",
        "create_subtitles": "創建字幕"
    },
    "ko": {
        "title": "AI 기반 로제타 스톤",
        "youtube_url": "YouTube URL 입력",
        "download_button": "YouTube 비디오 다운로드",
        "or_label": "또는",
        "select_video": "비디오 선택",
        "config_label": "자막 설정",
        "language_label": "자막 언어:",
        "context_label": "컨텍스트 크기 (0-10):",
        "silence_label": "최소 침묵 시간 (ms):",
        "create_subtitles": "자막 생성"
    },
    "ar": {
        "title": "حجر رشيد\nمدعوم بالذكاء الاصطناعي",
        "youtube_url": "أدخل عنوان URL لـ YouTube",
        "download_button": "تنزيل فيديو YouTube",
        "or_label": "أو",
        "select_video": "اختر فيديو",
        "config_label": "تكوين الترجمة",
        "language_label": "لغة الترجمة:",
        "context_label": "حجم السياق (0-10):",
        "silence_label": "الحد الأدنى لمدة الصمت (مللي ثانية):",
        "create_subtitles": "إنشاء ترجمة"
    },
    "hi": {
        "title": "एआई द्वारा संचालित रोसेटा स्टोन",
        "youtube_url": "YouTube URL दर्ज करें",
        "download_button": "YouTube वीडियो डाउनलोड करें",
        "or_label": "या",
        "select_video": "वीडियो चुनें",
        "config_label": "सबटाइटल कॉन्फ़िगर करें",
        "language_label": "सबटाइटल भाषा:",
        "context_label": "संदर्भ आकार (0-10):",
        "silence_label": "न्यूनतम चुपचाप अवधि (मिलीसेकंड):",
        "create_subtitles": "सबटाइटल बनाएं"
    },
    "tr": {
        "title": "Yapay Zeka Destekli Rosetta Taşı",
        "youtube_url": "YouTube URL'sini girin",
        "download_button": "YouTube videosunu indir",
        "or_label": "VEYA",
        "select_video": "Video seç",
        "config_label": "Altyazıyı yapılandır",
        "language_label": "Altyazı dil:",
        "context_label": "Bağlam boyutu (0-10):",
        "silence_label": "Minimum sessizlik süresi (ms):",
        "create_subtitles": "Altyazı oluştur"
    },
    "sv": {
        "title": "Rosettastenen\nDriven av AI",
        "youtube_url": "Ange YouTube-URL",
        "download_button": "Ladda ner YouTube-video",
        "or_label": "ELLER",
        "select_video": "Välj video",
        "config_label": "Konfigurerera undertexter",
        "language_label": "Undertextspråk:",
        "context_label": "Kontekststorlek (0-10):",
        "silence_label": "Minsta tystnadslängd (ms):",
        "create_subtitles": "Skapa undertexter"
    },
    "da": {
        "title": "Rosettastenen\nDrevet af AI",
        "youtube_url": "Indtast YouTube-URL",
        "download_button": "Download YouTube-video",
        "or_label": "ELLER",
        "select_video": "Vælg video",
        "config_label": "Konfigurer undertekster",
        "language_label": "Undertekstsprog:",
        "context_label": "Kontekststørrelse (0-10):",
        "silence_label": "Minimum stilhedslængde (ms):",
        "create_subtitles": "Opret undertekster"
    },
    "no": {
        "title": "Rosettasteinen\nDrevet av AI",
        "youtube_url": "Skriv inn YouTube-URL",
        "download_button": "Last ned YouTube-video",
        "or_label": "ELLER",
        "select_video": "Velg video",
        "config_label": "Konfigurer undertekster",
        "language_label": "Undertekstspråk:",
        "context_label": "Kontekststørrelse (0-10):",
        "silence_label": "Minimum stilhetstid (ms):",
        "create_subtitles": "Opprett undertekster"
    },
    "fi": {
        "title": "Tekoälyn Voimalla Toimiva Rosettan Kivi",
        "youtube_url": "Syötä YouTube-URL",
        "download_button": "Lataa YouTube-video",
        "or_label": "TAI",
        "select_video": "Valitse video",
        "config_label": "Määritä tekstitys",
        "language_label": "Tekstityskieli:",
        "context_label": "Kontekstin koko (0-10):",
        "silence_label": "Vähintän vauva-aika (ms):",
        "create_subtitles": "Luo tekstitys"
    },
    "el": {
        "title": "Στήλη της Ροζέτας\nμε Τεχνητή Νοημοσύνη",
        "youtube_url": "Εισάγετε το URL του YouTube",
        "download_button": "Κατεβάστε το βίντεο του YouTube",
        "or_label": "Ή",
        "select_video": "Επιλέξτε βίντεο",
        "config_label": "Διαμορφώστε το υπότιτλο",
        "language_label": "Γλώσσα υποτίτλων:",
        "context_label": "Μέγεθος περιβάλλοντος (0-10):",
        "silence_label": "Ελάχιστη διάρκεια σιγουριάς (ms):",
        "create_subtitles": "Δημιουργήστε υπότιτλους"
    },
    "he": {
        "title": "אבן רוזטה\nמופעלת על ידי בינה מלאכותית",
        "youtube_url": "הזן את כתובת ה-URL של YouTube",
        "download_button": "הורד וידאו מ־YouTube",
        "or_label": "או",
        "select_video": "בחר וידאו",
        "config_label": "הגדר כתוביות",
        "language_label": "שפת הכתוביות:",
        "context_label": "גודל ההקשר (0-10):",
        "silence_label": "זמן השתקה מינימלי (מילישניות):",
        "create_subtitles": "צור כתוביות"
    },
    "eo": {
        "title": "Rozeta Ŝtono\nFunkciigita per Artefarita Inteligenteco",
        "youtube_url": "Enigu YouTube-URL",
        "download_button": "Elŝutu YouTube-videon",
        "or_label": "Aŭ",
        "select_video": "Elektu videon",
        "config_label": "Agordu subtitrojn",
        "language_label": "Subtitra lingvo:",
        "context_label": "Kunteksto grandeco (0-10):",
        "silence_label": "Minimuma silenta daŭro (ms):",
        "create_subtitles": "Krei subtitrojn"
    },
    "la": {
        "title": "Lapis Rosettae\nArtificio Intellegenti Instructus",
        "youtube_url": "Inscribe nexum YouTube",
        "download_button": "Descarge pelliculam ex YouTube",
        "or_label": "VEL",
        "select_video": "Elige pelliculam",
        "config_label": "Configura subscriptiones",
        "language_label": "Lingua subscriptionum:",
        "context_label": "Magnitudo contextus (0-10):",
        "silence_label": "Minimum tempus silentii (ms):",
        "create_subtitles": "Crea subscriptiones"
    }
}    

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)

    def __init__(self):
        super().__init__()
    
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
            
            self.update_output.emit(f"Arquivo SRT salvo em: {output_srt}")
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
        self.setGeometry(100, 100, 800, 600)

        # Definir o ícone da janela (favicon)
        self.setWindowIcon(QIcon("rosetta_logo.png"))

        # Definir a imagem de fundo
        background = QPixmap("rosetta_logo.png")
        background = background.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        
        # Criar uma imagem semitransparente
        transparent_background = QPixmap(background.size())
        transparent_background.fill(Qt.GlobalColor.transparent)
        painter = QPainter(transparent_background)
        painter.setOpacity(0.2)  # 80% de transparência
        painter.drawPixmap(0, 0, background)
        painter.end()
        
        # Criar uma paleta e definir o plano de fundo
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(transparent_background))
        self.setPalette(palette)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Create all UI elements
        self.create_ui()
        
        # Now update the language
        self.update_language("pt")  # Iniciar com português
        
        # Setup config labels
        self.setup_config_labels()

    def create_ui(self):
        # Criar todos os widgets primeiro
        self.title_label = QLabel()
        self.subtitle_label = QLabel()
        self.youtube_url_input = QLineEdit()
        self.download_button = QPushButton()
        self.select_button = QPushButton()
        self.or_label = QLabel()
        self.config_label = QLabel()
        self.language_label = QLabel()
        self.language_combo = QComboBox()
        self.context_label = QLabel()
        self.context_spinbox = QSpinBox()
        self.silence_label = QLabel()
        self.silence_spinbox = QSpinBox()
        self.process_button = QPushButton()
        
        # Configurar widgets
        self.populate_language_combo()
        
        # Remove a seta padrão do QComboBox
        self.language_combo.setStyleSheet("""
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border: none;
            }
            QComboBox::drop-down {
                width: 0;
                border: none;
            }
        """)
        
        # Adiciona um espaçador no topo para empurrar o conteúdo para baixo
        self.layout.addSpacing(20)

        # Adiciona título e subtítulo
        title_layout = QVBoxLayout()
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        self.layout.addLayout(title_layout)

        # Adiciona um espaçador após o título
        self.layout.addSpacing(20)

        # Adiciona input de URL do YouTube e botão de download
        youtube_layout = QHBoxLayout()
        youtube_layout.addWidget(self.youtube_url_input)
        youtube_layout.addWidget(self.download_button)
        self.layout.addLayout(youtube_layout)

        # Adiciona o label "OU"
        self.layout.addWidget(self.or_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Adiciona o botão de seleção de vídeo
        self.layout.addWidget(self.select_button)

        # Configurações
        config_layout = QGridLayout()
        config_layout.addWidget(self.config_label, 0, 0, 1, 2)
        config_layout.addWidget(self.language_label, 1, 0)
        config_layout.addWidget(self.language_combo, 1, 1)
        config_layout.addWidget(self.context_label, 2, 0)
        config_layout.addWidget(self.context_spinbox, 2, 1)
        config_layout.addWidget(self.silence_label, 3, 0)
        config_layout.addWidget(self.silence_spinbox, 3, 1)
        
        # Centralize os labels
        config_layout.setAlignment(self.config_label, Qt.AlignmentFlag.AlignCenter)
        config_layout.setAlignment(self.language_label, Qt.AlignmentFlag.AlignRight)
        config_layout.setAlignment(self.context_label, Qt.AlignmentFlag.AlignRight)
        config_layout.setAlignment(self.silence_label, Qt.AlignmentFlag.AlignRight)

        self.layout.addLayout(config_layout)

        # Adiciona o botão de processamento
        self.layout.addWidget(self.process_button)

        # Adiciona a barra de progresso
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        # Adiciona a área de texto de saída
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.layout.addWidget(self.output_text)

        # Adiciona um espaçador no final para empurrar o conteúdo para cima
        self.layout.addStretch(1)

        # Configura estilos e outras propriedades
        self.setup_styles()

        # Conectar os botões às suas funções
        self.download_button.clicked.connect(self.download_youtube)
        self.select_button.clicked.connect(self.select_video)
        self.process_button.clicked.connect(self.process_video)

        # Conectar o combo box de idiomas
        self.language_combo.currentTextChanged.connect(self.change_language)

    def populate_language_combo(self):
        languages = [
            "Português", "English", "Español", "Français", "Deutsch", 
            "Italiano", "Nederlands", "Polski", "Русский", "日本語", 
            "中文 (简体)", "中文 (繁體)", "한국어", "العربية", "हिन्दी", 
            "Türkçe", "Svenska", "Dansk", "Norsk", "Suomi", 
            "Ελληνικά", "עברית", "Esperanto", "Latin"
        ]
        self.language_combo.addItems(languages)
        self.language_combo.setCurrentText("Português")  # Define o português como padrão

    def setup_styles(self):
        # Configuração do título
        title_font = QFont(QApplication.font())
        title_font.setPointSize(int(QApplication.font().pointSize() * 3))  # 3 vezes maior
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Configuração do subtítulo
        subtitle_font = QFont(QApplication.font())
        subtitle_font.setPointSize(int(QApplication.font().pointSize() * 1.5))  # 1.5 vezes maior
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Configuração dos botões
        button_style = """
        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 11px 24px;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
            margin: 3px 2px;
            border-radius: 8px;
            min-height: 37px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        """
        self.download_button.setStyleSheet(button_style)
        self.select_button.setStyleSheet(button_style)
        self.process_button.setStyleSheet(button_style)

        # Configuração dos campos de entrada e combo box
        input_style = """
        QLineEdit, QComboBox, QSpinBox {
            padding: 7px;
            font-size: 14px;
            border: 1px solid #ddd;
            border-radius: 4px;
            min-height: 37px;
        }
        """
        self.youtube_url_input.setStyleSheet(input_style)
        self.language_combo.setStyleSheet(input_style)
        self.context_spinbox.setStyleSheet(input_style)
        self.silence_spinbox.setStyleSheet(input_style)
        self.context_spinbox.setValue(2)  # Define o valor padrão para 2
        self.context_spinbox.setRange(0, 10)  # Mantém o intervalo de 0 a 10
        self.context_spinbox.setSingleStep(1)  # Mantém o passo em 1

        # Para a duração mínima de silêncio
        self.silence_spinbox.setRange(100, 2000)  # Ajuste o intervalo conforme necessário
        self.silence_spinbox.setSingleStep(100) 
        self.silence_spinbox.setValue(400)  # Define o valor padrão para 400
        # Configuração do label "OU"
        or_font = QFont("Papyrus", 12)
        or_font.setBold(True)
        self.or_label.setFont(or_font)
        self.or_label.setStyleSheet("font-weight: bold; color: #333;")

        # Configuração dos labels de configuração
        config_font = QFont("Arial", 11)
        config_font.setBold(True)
        self.config_label.setFont(config_font)
        self.language_label.setFont(config_font)
        self.context_label.setFont(config_font)
        self.silence_label.setFont(config_font)

        # Configuração da barra de progresso
        self.progress_bar.setStyleSheet("""
        QProgressBar {
            border: 2px solid grey;
            border-radius: 4px;
            text-align: center;
            height: 22px;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            width: 7px;
            margin: 0.5px;
        }
        """)

        # Configuração da área de texto de saída
        self.output_text.setStyleSheet("""
        QTextEdit {
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 4px;
            font-family: Courier, monospace;
            font-size: 12px;
        }
        """)

        # Adicione isso ao final do método create_ui ou no início do setup_styles
        self.download_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.select_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.process_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def setup_config_labels(self):
        base_font_size = QApplication.font().pointSize()
        larger_font_size = int(base_font_size * 1.4)  # Aumenta em 40%

        config_label_style = """
            QLabel {{
                font-family: Papyrus;
                font-size: 120%;
                font-weight: bold;
            qproperty-alignment: AlignCenter;
            }}
        """
        self.config_label.setStyleSheet(config_label_style)
        self.language_label.setStyleSheet(config_label_style)
        self.context_label.setStyleSheet(config_label_style)
        self.silence_label.setStyleSheet(config_label_style)

        # Ajustar o tamanho da fonte para o QComboBox e QSpinBox
        input_style = """
            QComboBox, QSpinBox {{
                font-family: Papyrus;
                font-size: {larger_font_size}pt;
            }}
        """
        self.language_combo.setStyleSheet(self.language_combo.styleSheet() + input_style)
        self.context_spinbox.setStyleSheet(input_style)
        self.silence_spinbox.setStyleSheet(input_style)

        # Ajustar o tamanho dos widgets para acomodar o texto maior
        self.language_combo.setMinimumHeight(int(40 * 1.4))
        self.context_spinbox.setMinimumHeight(int(40 * 1.4))
        self.silence_spinbox.setMinimumHeight(int(40 * 1.4))

         # Definir a fonte diretamente para os QLabels
        papyrus_font = QFont("Papyrus", larger_font_size)
        papyrus_font.setBold(True)
        self.config_label.setFont(papyrus_font)
        self.language_label.setFont(papyrus_font)
        self.context_label.setFont(papyrus_font)
        self.silence_label.setFont(papyrus_font)

    def update_language(self, lang):
        trans = translations[lang]
        title_parts = trans["title"].split("\n")
        main_title = title_parts[0].strip()
        subtitle = title_parts[1].strip() if len(title_parts) > 1 else ""
        
        self.title_label.setText(main_title)
        self.subtitle_label.setText(subtitle)
        
        self.youtube_url_input.setPlaceholderText(trans["youtube_url"])
        self.download_button.setText(trans["download_button"])
        self.select_button.setText(trans["select_video"])
        self.or_label.setText(trans["or_label"])
        self.config_label.setText(trans["config_label"])
        self.language_label.setText(trans["language_label"])
        self.context_label.setText(trans["context_label"])
        self.silence_label.setText(trans["silence_label"])
        self.process_button.setText(trans["create_subtitles"])

    def change_language(self):
        selected_language = self.language_combo.currentText()
        lang_map = {
            "Português": "pt", "English": "en", "Español": "es", "Français": "fr",
            "Deutsch": "de", "Italiano": "it", "Nederlands": "nl", "Polski": "pl",
            "Русский": "ru", "日本語": "ja", "中文 (简体)": "zh-CN", "中文 (繁體)": "zh-TW",
            "한국어": "ko", "العربية": "ar", "हिन्दी": "hi", "Türkçe": "tr",
            "Svenska": "sv", "Dansk": "da", "Norsk": "no", "Suomi": "fi",
            "Ελληνικά": "el", "עברית": "he", "Esperanto": "eo", "Latin": "la"
        }
        self.update_language(lang_map.get(selected_language, "pt"))

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
        if not hasattr(self, 'video_path') or not self.video_path:
            self.output_text.append("Por favor, selecione um vídeo ou faça o download do YouTube antes de prosseguir.")
            return

        self.reset_progress_bar() 
        context_size = self.context_spinbox.value()
        min_silence_len = self.silence_spinbox.value()
        target_lang = self.get_target_lang_code()
        
        try:
            self.worker = WorkerThread()
            self.worker.video_path = self.video_path
            self.worker.context_size = context_size
            self.worker.min_silence_len = min_silence_len
            self.worker.target_lang = target_lang
            
            self.worker.update_progress.connect(self.update_progress)
            self.worker.update_output.connect(self.update_output)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.start()
            self.output_text.append("Processando vídeo...")
        except Exception as e:
            self.output_text.append(f"Erro ao iniciar o processamento: {str(e)}")

    def get_target_lang_code(self):
        lang_map = {
            "Português": "pt", "English": "en", "Español": "es", "Français": "fr",
            "Deutsch": "de", "Italiano": "it", "Nederlands": "nl", "Polski": "pl",
            "Русский": "ru", "日本語": "ja", "中文 (简体)": "zh-CN", "中文 (繁體)": "zh-TW",
            "한국어": "ko", "العربية": "ar", "हिन्दी": "hi", "Türkçe": "tr",
            "Svenska": "sv", "Dansk": "da", "Norsk": "no", "Suomi": "fi",
            "Ελληνικά": "el", "עברית": "he", "Esperanto": "eo", "Latin": "la"
        }
        selected_lang = self.language_combo.currentText()
        return lang_map.get(selected_lang, "pt")  # Default to Portuguese if not found

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, text):
        self.output_text.append(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        background = QPixmap("rosetta_logo.png")
        scaled_background = background.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        
        transparent_background = QPixmap(scaled_background.size())
        transparent_background.fill(Qt.GlobalColor.transparent)
        painter = QPainter(transparent_background)
        painter.setOpacity(0.2)  # 80% de transparência
        painter.drawPixmap(0, 0, scaled_background)
        painter.end()
        
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(transparent_background))
        self.setPalette(palette)

    def closeEvent(self, event):
        # Certifique-se de que todas as threads sejam encerradas
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()
        super().closeEvent(event)

    def setup_global_font(self):
        # Tenta carregar a fonte Papyrus
        font_id = QFontDatabase.addApplicationFont("path/to/Papyrus.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            font_family = "Papyrus"  # Usa o nome da fonte, esperando que esteja instalada no sistema

        # Cria a fonte
        font = QFont(font_family, 12)  # Tamanho base 12, ajuste conforme necessário
        
        # Aplica a fonte globalmente
        QApplication.setFont(font)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configurar a fonte global
    font_id = QFontDatabase.addApplicationFont("path/to/Papyrus.ttf")
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    else:
        font_family = "Papyrus"
    app.setFont(QFont(font_family, 12))
    
    window = MainWindow()
    app.setWindowIcon(window.windowIcon())
    window.show()
    sys.exit(app.exec())

