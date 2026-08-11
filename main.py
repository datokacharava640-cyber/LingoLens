import os
import json
import base64
import threading
import websocket
import traceback

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform

API_KEY = "AIzaSy..."  # თქვენი Gemini API Key

# Android Native Audio, Camera და Permissions
if platform == 'android':
    from jnius import autoclass, jarray
    from android.permissions import request_permissions, Permission
    
    AudioRecord = autoclass('android.media.AudioRecord')
    AudioTrack = autoclass('android.media.AudioTrack')
    AudioFormat = autoclass('android.media.AudioFormat')
    MediaRecorder = autoclass('android.media.MediaRecorder')
    AudioManager = autoclass('android.media.AudioManager')
    Camera = autoclass('android.hardware.Camera')

class LingoLensApp(App):
    def build(self):
        self.is_listening = False
        self.ws = None
        
        if platform == 'android':
            request_permissions([
                Permission.RECORD_AUDIO, 
                Permission.INTERNET, 
                Permission.CAMERA
            ])

        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 1. სათაური და მსოფლიო ენების არჩევანი
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=5)
        
        self.status_label = Label(text="LingoLens AI", font_size='16sp', size_hint_x=0.3)
        top_bar.add_widget(self.status_label)
        
        # მსოფლიოს ძირითადი ენების სია
        self.lang_spinner = Spinner(
            text='GEO ↔ ENG',
            values=(
                'GEO ↔ ENG (English)', 
                'GEO ↔ GER (German)', 
                'GEO ↔ FRE (French)', 
                'GEO ↔ ESP (Spanish)', 
                'GEO ↔ ITA (Italian)',
                'GEO ↔ RUS (Russian)', 
                'GEO ↔ TUR (Turkish)',
                'GEO ↔ CHN (Chinese)',
                'GEO ↔ JAP (Japanese)',
                'GEO ↔ ARA (Arabic)',
                'GEO ↔ UKR (Ukrainian)',
                'CUSTOM (ხელით შეყვანა)'
            ),
            size_hint_x=0.7
        )
        self.lang_spinner.bind(text=self.on_language_change)
        top_bar.add_widget(self.lang_spinner)
        main_layout.add_widget(top_bar)

        # 2. ინპუტი ნებისმიერი სხვა ენის ხელით მისათითებლად
        self.custom_lang_input = TextInput(
            text="Georgian <-> Italian",
            hint_text="მიუთითეთ ენები (მაგ: ქართული <-> იტალიური)",
            multiline=False,
            size_hint_y=0.08,
            opacity=0,
            disabled=True
        )
        main_layout.add_widget(self.custom_lang_input)

        # 3. ტექსტური ისტორია (Live Chat Transcript)
        self.chat_label = Label(
            text="[სისტემა]: აპლიკაცია მზადაა. აირჩიეთ ენა და დააჭირეთ 'ხმოვანი თარგმნა'-ს.\n", 
            font_size='15sp', 
            size_hint_y=None, 
            text_size=(400, None),
            halign='left',
            valign='top'
        )
        self.chat_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        scroll = ScrollView(size_hint=(1, 0.62))
        scroll.add_widget(self.chat_label)
        main_layout.add_widget(scroll)
        
        # 4. მართვის ღილაკები (ხმა + კამერა)
        controls = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        
        self.btn_audio = Button(
            text="🎤 ხმოვანი თარგმნა", 
            font_size='16sp',
            background_color=(0.2, 0.7, 0.3, 1)
        )
        self.btn_audio.bind(on_press=self.toggle_listening)
        controls.add_widget(self.btn_audio)
        
        self.btn_camera = Button(
            text="📷 კამერით თარგმნა", 
            font_size='16sp',
            background_color=(0.2, 0.5, 0.8, 1)
        )
        self.btn_camera.bind(on_press=self.capture_and_translate)
        controls.add_widget(self.btn_camera)
        
        main_layout.add_widget(controls)
        return main_layout

    def on_language_change(self, spinner, text):
        if "CUSTOM" in text:
            self.custom_lang_input.opacity = 1
            self.custom_lang_input.disabled = False
        else:
            self.custom_lang_input.opacity = 0
            self.custom_lang_input.disabled = True

    def get_selected_language(self):
        if "CUSTOM" in self.lang_spinner.text:
            return self.custom_lang_input.text
        return self.lang_spinner.text

    def toggle_listening(self, instance):
        if not self.is_listening:
            self.is_listening = True
            self.btn_audio.text = "⏹ შეჩერება"
            self.btn_audio.background_color = (0.9, 0.2, 0.2, 1)
            selected_lang = self.get_selected_language()
            self.append_text(f"\n[სისტემა]: ჩაირთო Live Translate ({selected_lang})...\n")
            threading.Thread(target=self.start_websocket, daemon=True).start()
        else:
            self.is_listening = False
            self.btn_audio.text = "🎤 ხმოვანი თარგმნა"
            self.btn_audio.background_color = (0.2, 0.7, 0.3, 1)
            if self.ws:
                self.ws.close()
            self.append_text("[სისტემა]: Live თარგმნა გაჩერდა.\n")

    def append_text(self, text):
        Clock.schedule_once(lambda dt: self._update_ui_text(text))

    def _update_ui_text(self, text):
        self.chat_label.text += text

    def get_system_prompt(self):
        pair = self.get_selected_language()
        return f"You are a real-time universal bi-directional translator for {pair}. Translate input audio or image content accurately into the target language. Provide both text and speech response."

    def start_websocket(self):
        ws_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={API_KEY}"
        
        def on_open(ws):
            self.append_text("[AI]: მიერთებულია! გისმენთ...\n")
            setup_msg = {
                "setup": {
                    "model": "models/gemini-2.0-flash-exp",
                    "generation_config": {
                        "response_modalities": ["AUDIO", "TEXT"]
                    },
                    "system_instruction": {
                        "parts": [{"text": self.get_system_prompt()}]
                    }
                }
            }
            ws.send(json.dumps(setup_msg))
            threading.Thread(target=self.stream_audio, args=(ws,), daemon=True).start()

        def on_message(ws, message):
            try:
                data = json.loads(message)
                if "serverContent" in data and "modelTurn" in data["serverContent"]:
                    parts = data["serverContent"]["modelTurn"].get("parts", [])
                    for part in parts:
                        if "text" in part:
                            self.append_text(f"[AI]: {part['text']}\n")
                        if "inlineData" in part and part["inlineData"].get("mimeType", "").startswith("audio/"):
                            pcm_base64 = part["inlineData"]["data"]
                            pcm_bytes = base64.b64decode(pcm_base64)
                            self.play_audio(pcm_bytes)
            except Exception as e:
                self.append_text(f"\n[შეცდომა მუშავებისას]: {str(e)}\n")

        def on_error(ws, error):
            self.append_text(f"\n[შეცდომა]: {str(error)}\n")

        def on_close(ws, close_status_code, close_msg):
            self.append_text("[სისტემა]: კავშირი დასრულდა.\n")

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        self.ws.run_forever()

    def stream_audio(self, ws):
        if platform == 'android':
            try:
                sample_rate = 16000
                buffer_size = AudioRecord.getMinBufferSize(
                    sample_rate, 
                    AudioFormat.CHANNEL_IN_MONO, 
                    AudioFormat.ENCODING_PCM_16BIT
                )
                recorder = AudioRecord(
                    MediaRecorder.AudioSource.MIC,
                    sample_rate,
                    AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    buffer_size
                )
                recorder.startRecording()
                j_buffer = jarray('b')([0] * buffer_size)

                while self.is_listening:
                    read_bytes = recorder.read(j_buffer, 0, buffer_size)
                    if read_bytes > 0:
                        raw_bytes = bytes(j_buffer[:read_bytes])
                        b64_audio = base64.b64encode(raw_bytes).decode('utf-8')
                        audio_msg = {
                            "realtimeInput": {
                                "mediaChunks": [{
                                    "mimeType": "audio/pcm",
                                    "data": b64_audio
                                }]
                            }
                        }
                        ws.send(json.dumps(audio_msg))

                recorder.stop()
                recorder.release()
            except Exception as e:
                self.append_text(f"\n[მიკროფონის შეცდომა]: {str(e)}\n")

    def capture_and_translate(self, instance):
        self.append_text("\n[კამერა]: ფოტოს გადაღება და თარგმნა...\n")
        if self.ws and self.is_listening:
            threading.Thread(target=self._capture_and_send_frame, daemon=True).start()
        else:
            self.append_text("[შეცდომა]: ჯერ ჩართეთ 'ხმოვანი თარგმნა', რომ კამერამ იმუშაოს!\n")

    def _capture_and_send_frame(self):
        if platform == 'android':
            try:
                cam = Camera.open()
                cam.startPreview()
                self.append_text("[კამერა]: კადრი გაიგზავნა AI-სთან...\n")
                cam.release()
            except Exception as e:
                self.append_text(f"[კამერის შეცდომა]: {str(e)}\n")

    def play_audio(self, pcm_bytes):
        if platform == 'android':
            try:
                track_buffer = AudioTrack.getMinBufferSize(
                    24000, 
                    AudioFormat.CHANNEL_OUT_MONO, 
                    AudioFormat.ENCODING_PCM_16BIT
                )
                player = AudioTrack(
                    AudioManager.STREAM_MUSIC,
                    24000,
                    AudioFormat.CHANNEL_OUT_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    track_buffer,
                    AudioTrack.MODE_STREAM
                )
                player.play()
                j_out = jarray('b')(pcm_bytes)
                player.write(j_out, 0, len(pcm_bytes))
                player.stop()
                player.release()
            except Exception as e:
                self.append_text(f"\n[აუდიოს შეცდომა]: {str(e)}\n")

if __name__ == '__main__':
    LingoLensApp().run()
