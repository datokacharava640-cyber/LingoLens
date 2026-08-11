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
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.utils import platform

# NotoSansGeorgian ფონტის რეგისტრირება
if os.path.exists("NotoSansGeorgian.ttf"):
    LabelBase.register(name="Roboto", fn_regular="NotoSansGeorgian.ttf")

API_KEY = "AIzaSy..."  # თქვენი Gemini API Key

# Android Native Audio და Permissions
if platform == 'android':
    from jnius import autoclass, jarray
    from android.permissions import request_permissions, Permission
    
    AudioRecord = autoclass('android.media.AudioRecord')
    AudioTrack = autoclass('android.media.AudioTrack')
    AudioFormat = autoclass('android.media.AudioFormat')
    MediaRecorder = autoclass('android.media.MediaRecorder')
    AudioManager = autoclass('android.media.AudioManager')

class LingoLensApp(App):
    def build(self):
        self.is_listening = False
        self.ws = None
        
        if platform == 'android':
            request_permissions([Permission.RECORD_AUDIO, Permission.INTERNET])

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.status_label = Label(
            text="LingoLens Live AI Translator", 
            font_size='20sp', 
            size_hint_y=0.1
        )
        layout.add_widget(self.status_label)
        
        self.chat_label = Label(
            text="დააჭირეთ ღილაკს საუბრის დასაწყებად...\n", 
            font_size='16sp', 
            size_hint_y=None, 
            text_size=(400, None),
            halign='left',
            valign='top'
        )
        self.chat_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        scroll = ScrollView(size_hint=(1, 0.75))
        scroll.add_widget(self.chat_label)
        layout.add_widget(scroll)
        
        self.btn = Button(
            text="საუბრის დაწყება", 
            font_size='18sp', 
            size_hint_y=0.15,
            background_color=(0.2, 0.7, 0.3, 1)
        )
        self.btn.bind(on_press=self.toggle_listening)
        layout.add_widget(self.btn)
        
        return layout

    def toggle_listening(self, instance):
        if not self.is_listening:
            self.is_listening = True
            self.btn.text = "შეჩერება"
            self.btn.background_color = (0.9, 0.2, 0.2, 1)
            self.append_text("\n[სისტემა]: Gemini Live ჩაირთო...\n")
            threading.Thread(target=self.start_websocket, daemon=True).start()
        else:
            self.is_listening = False
            self.btn.text = "საუბრის დაწყება"
            self.btn.background_color = (0.2, 0.7, 0.3, 1)
            if self.ws:
                self.ws.close()
            self.append_text("[სისტემა]: Gemini Live გაჩერდა.\n")

    def append_text(self, text):
        Clock.schedule_once(lambda dt: self._update_ui_text(text))

    def _update_ui_text(self, text):
        self.chat_label.text += text

    def start_websocket(self):
        ws_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={API_KEY}"
        
        def on_open(ws):
            self.append_text("[AI]: მიერთებულია! გისმენთ...\n")
            setup_msg = {
                "setup": {
                    "model": "models/gemini-2.0-flash-exp",
                    "generation_config": {
                        "response_modalities": ["AUDIO"]
                    },
                    "system_instruction": {
                        "parts": [{"text": "You are a real-time bi-directional translator between Georgian and English. Translate Georgian to English and English to Georgian."}]
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
                        if "inlineData" in part:
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
