import speech_recognition as sr
import requests
import subprocess
from translate import Translator
from PIL import Image
import sys
from PyQt5.QtWidgets import QApplication,QFrame, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,QStyleFactory, QLabel,QTabWidget
from PyQt5.QtCore import Qt,QSize,QCoreApplication
from PyQt5.QtGui import QPalette, QColor,QIcon
import io
import pyautogui
from gtts import gTTS
import pygame

def query(text,function,model_id):
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    api_token = "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"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {
        "inputs": text,
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        if function=='text':
            response_json = response.json()
            generated_text = response_json[0]["generated_text"]
            return generated_text
        elif function=='image':
            image_bytes=response.content
            image = Image.open(io.BytesIO(image_bytes))
            image.save("your_image.jpg")
            subprocess.Popen(["start", 'your_image.jpg'], shell=True)
            return 'Succesful'
    else:
        return f"Lỗi xảy ra,thử lại sau vài phút.\nRequest failed with status code {response.status_code}: {response.text}"

def listen(langvi):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio, language='vi' if langvi==True else 'en')
        except sr.UnknownValueError:
            return "Không thể nhận dạng giọng nói"
        except:
            return "Lỗi trong quá trình kết nối với API"

        return text.lower()

def speak(text,langvi):
    tts = gTTS(text, lang='vi' if langvi==True else 'en')

    audio_data = io.BytesIO()
    tts.write_to_fp(audio_data)
    audio_data.seek(0)

    pygame.init()
    pygame.mixer.init()
    sound = pygame.mixer.Sound(audio_data)

    sound.play()

def Translate(string, fromlang, tolang):
    max_length = 450
    translator = Translator(from_lang=fromlang,to_lang=tolang)
    translated_parts = []

    for i in range(0, len(string), max_length):
        part = string[i:i + max_length]
        translation = translator.translate(part)
        translated_parts.append(translation)

    translated_text = ' '.join(translated_parts)
    return translated_text

class functionWidget(QWidget):
    input_vi=True
    input_voice=False
    response_vi=True
    response_voice=False    

    def reset_action(self,text_input,text_response,function):
        text_input.setText('')
        text_response.setText('')

        if self.input_voice==True:
            text_input.setText('Listening...')
            QCoreApplication.processEvents()

            text_input.setText(listen(self.input_vi))

            self.generate_action(function,text_input,text_response)

    def input_vot_action(self,para,text_input):
        button=para.sender()
        button.setIcon(QIcon('voice_button_true.jpg') if self.input_voice==False else QIcon('voice_button_false.jpg'))

        text_input.setReadOnly(not self.input_voice)
        
        self.input_voice=not self.input_voice

    def input_lang_action(self,para):
        button=para.sender()
        button.setText('VI' if self.input_vi==False else 'EN')

        self.input_vi=not self.input_vi

    def response_vot_action(self,para):
        button=para.sender()
        button.setIcon(QIcon('voice_button_true.jpg') if self.response_voice==False else QIcon('voice_button_false.jpg'))

        self.response_voice=not self.response_voice

    def response_lang_action(self,para):
        button=para.sender()
        button.setText('VI' if self.response_vi==False else 'EN')

        self.response_vi=not self.response_vi

    def generate_action(self,function,text_input,text_response):
        text_response.setText('...')
        QCoreApplication.processEvents()

        string=text_input.toPlainText()

        if self.input_vi==True:
            string=Translate(string,'vi','en')

        if function=='text':
            previousres='You are an AI assistant, answer this message: '+string+'.\n'
            response=query('You are an AI assistant, answer this message: '+string+'.','text',"tiiuae/falcon-7b-instruct")

            if response.split('\n')[0]!='Lỗi xảy ra,thử lại sau vài phút.':
                while(True):
                    strtmp=response[len(previousres):]
                    if self.response_vi==True:
                        strtmp=Translate(strtmp,'en','vi')
                        if (previousres!='You are an AI assistant, answer this message: '+string+'.\n'):
                            strtmp=' '+strtmp

                    if (previousres=='You are an AI assistant, answer this message: '+string+'.\n'):
                        text_response.setText('')
                        QCoreApplication.processEvents()

                    text_response.insertPlainText(strtmp)
                    QCoreApplication.processEvents()

                    previousres=response
                    response = query(previousres,'text',"tiiuae/falcon-7b-instruct")
                    if str(response)==str(previousres):
                        break 

                if self.response_voice==True:
                    speak(text_response.toPlainText(),self.response_vi)
            else:
                text_response.setText(response)
        elif function=='image':
            text_response.setText(query(string,'image',"stabilityai/stable-diffusion-xl-base-1.0"))
        else:
            previousres=query('You are an AI assistant, answer this message: write python code to '+string+' . gen code only .','text',"tiiuae/falcon-7b-instruct")
            while(True):
                response = query(previousres,'text',"tiiuae/falcon-7b-instruct")
                if str(response)==str(previousres):
                    break 
                previousres=response

            if response.split('\n')[0]!='Lỗi xảy ra,thử lại sau vài phút.':
                with open('action.py','w') as f:
                    f.write('\n'.join(response.split('\n')[1:]))
                try:
                    subprocess.run(["python",'action.py'], check=True)
                except:
                    text_response.setText("Lỗi.")
                else:
                    text_response.setText("Successful")
            else:
                text_response.setText(response)

    def __init__(self,function,hide_res_button):
        super().__init__()

        function_layout = QVBoxLayout()

        input_layout=QHBoxLayout()

        text_input = QTextEdit()
        text_input.setStyleSheet("color: white; font-size: 37px") 
        text_input.setPlaceholderText("Enter text")

        input_buttons_layout = QVBoxLayout()

        reset_button=QPushButton()
        reset_button.setIcon(QIcon('reset_button.png'))
        reset_button.setIconSize(QSize(45,45))
        reset_button.clicked.connect(lambda:self.reset_action(text_input,text_response,function))

        voice_or_text_button = QPushButton()
        voice_or_text_button.setIcon(QIcon('voice_button_false.jpg'))
        voice_or_text_button.setIconSize(QSize(45,45))
        voice_or_text_button.clicked.connect(lambda:self.input_vot_action(voice_or_text_button,text_input))
        
        vi_or_en_button = QPushButton("VI")
        vi_or_en_button.setStyleSheet('font-size:40px')
        vi_or_en_button.clicked.connect(lambda:self.input_lang_action(vi_or_en_button))
        
        input_buttons_layout.addWidget(reset_button)
        input_buttons_layout.addWidget(voice_or_text_button)
        input_buttons_layout.addWidget(vi_or_en_button)
        
        input_layout.addWidget(text_input)
        input_layout.addLayout(input_buttons_layout)

        response_layout=QHBoxLayout()

        text_response = QTextEdit()
        text_response.setStyleSheet("color: white; font-size: 37px") 
        text_response.setReadOnly(True)

        response_buttons_layout = QVBoxLayout()

        response_voice_or_text_button = QPushButton()
        response_voice_or_text_button.setIcon(QIcon('voice_button_false.jpg'))
        response_voice_or_text_button.setIconSize(QSize(45,45))
        response_voice_or_text_button.clicked.connect(lambda:self.response_vot_action(response_voice_or_text_button))
       
        response_vi_or_en_button = QPushButton("VI")
        response_vi_or_en_button.setStyleSheet('font-size:40px')
        response_vi_or_en_button.clicked.connect(lambda:self.response_lang_action(response_vi_or_en_button))
        
        response_buttons_layout.addWidget(response_voice_or_text_button)
        response_buttons_layout.addWidget(response_vi_or_en_button)
        response_layout.addWidget(text_response)
        if hide_res_button==False:
            response_layout.addLayout(response_buttons_layout)

        generate_button=QPushButton('GENERATE')
        generate_button.setStyleSheet('font-size:30px')
        generate_button.clicked.connect(lambda:self.generate_action(function,text_input,text_response))

        function_layout.addLayout(input_layout)
        function_layout.addWidget(generate_button)
        function_layout.addLayout(response_layout)
        self.setLayout(function_layout)

class VoiceAssistantApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Assistant")
        screen_width,screen_height = pyautogui.size()
        width=1000
        height=800
        self.setGeometry(screen_width//2-width//2,screen_height//2-height//2,width,height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.Highlight, QColor(142, 45, 197))
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setPalette(dark_palette)
        QApplication.setStyle(QStyleFactory.create("Fusion")) 

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabBar::tab {font-size:25px; height: 40px; width: 324px; }")
        # Function 1: Text generation
        tab_widget.addTab(functionWidget('text',False),'TEXT')
        # Function 2: Image generation
        tab_widget.addTab(functionWidget('image',True),'IMAGE')
        # Function 3: Action generation
        tab_widget.addTab(functionWidget('action',True),'ACTION')

        title = QLabel()
        title.setText('MY ASSISTANT')
        title.setStyleSheet('font-size:50px;font-weight: bold;')
        title.setAlignment(Qt.AlignCenter) 

        layout.addWidget(title)
        layout.addWidget(tab_widget)

app = QApplication(sys.argv)
window = VoiceAssistantApp()
window.setWindowFlags(Qt.FramelessWindowHint)
window.show()
sys.exit(app.exec_())
