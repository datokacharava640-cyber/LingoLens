import os
import json
import base64
import threading
import websocket
import queue
import time
import traceback

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.camera import Camera as KivyCamera
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

# ქართული შრიფტის ავტომატური შემოწმება
FONT_NAME = "NotoSansGeorgian.ttf" if os.path.exists("NotoSansGeorgian.ttf") else None

# Android Native Media & Permissions
if platform == 'android':
    from jnius import autoclass, jarray
    from android.permissions import request_permissions, Permission
    
    AudioRecord = autoclass('android.media.AudioRecord')
    AudioTrack = autoclass('android.media.AudioTrack')
    AudioFormat = autoclass('android.media.AudioFormat')
    MediaRecorder = autoclass('android.media.MediaRecorder')
    AudioManager = autoclass('android.media.AudioManager')
    
    # ეკრანის გათიშვისგან დაცვა (WakeLock)
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')

class LingoLensApp(App):
    def build(self):
        self.is_listening = False
        self.is_playing_audio = False
        self.ws = None
        self.should_reconnect = True
        
        # 1. აუდიო ნაკადის რიგი (Audio Queue Worker)
        self.audio_queue = queue.Queue()
        threading.Thread(target=self._audio_player_worker, daemon=True).start()

        # ლოკალური მეხსიერება API Key-ს შესანახად
        self.store = JsonStore('settings.json')
        saved_key = self.store.get('api')['key'] if self.store.exists('api') else ""

        # Android უფლებების მოთხოვნა და ეკრანის ჩართულ მდგომარეობაში დატოვება
        if platform == 'android':
            request_permissions([
                Permission.RECORD_AUDIO, 
                Permission.INTERNET, 
                Permission.CAMERA
            ])
            self.enable_keep_screen_on()

        main_layout = BoxLayout(orientation='vertical', padding=8, spacing=6)
        
        # 2. API Key-ს შეყვანის/შენახვის ზოლი
        key_bar = BoxLayout(orientation='horizontal', size_hint_y=0.07, spacing=5)
        self.api_input = TextInput(
            text=saved_key, 
            hint_text="შეიყვანეთ Gemini API Key", 
            password=True, 
            multiline=False,
            font_name=FONT_NAME
        )
        btn_save_key = Button(
            text="💾 შენახვა", 
            size_hint_x=0.3, 
            background_color=(0.3, 0.6, 0.9, 1),
            font_name=FONT_NAME
        )
        btn_save_key.bind(on_press=self.save_api_key)
        key_bar.add_widget(self.api_input)
        key_bar.add_widget(btn_save_key)
        main_layout.add_widget(key_bar)

        # 3. ენების არჩევანის ზოლი
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.07, spacing=5)
        self.status_label = Label(text="LingoLens AI", font_size='15sp', size_hint_x=0.3, font_name=FONT_NAME)
        top_bar.add_widget(self.status_label)
        
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
                'CUSTOM (ხელით შეყვანა)'
            ),
            size_hint_x=0.7,
            font_name=FONT_NAME
        )
        self.lang_spinner.bind(text=self.on_language_change)
        top_bar.add_widget(self.lang_spinner)
        main_layout.add_widget(top_bar)

        # Custom Language Field
        self.custom_lang_input = TextInput(
            text="Georgian <-> Italian",
            hint_text="მიუთითეთ ენები (მაგ: ქართული <-> იტალიური)",
            multiline=False,
            size_hint_y=0.06,
            opacity=0,
            disabled=True,
            font_name=FONT_NAME
        )
        main_layout.add_widget(self.custom_lang_input)

        # 4. კამერის Visual Preview ვიჯეტი
        try:
            self.camera_widget = KivyCamera(index=0, resolution=(640, 480), play=True, size_hint_y=0.35)
            main_layout.add_widget(self.camera_widget)
        except Exception as e:
            self.append_text(f"[კამერის ჩართვა]: {str(e)}\n")

        # 5. ტექსტური ისტორია (Live Transcript) ქართული ფონტის მხარდაჭერით
        self.chat_label = Label(
            text="[სისტემა]: შეიყვანეთ API Key, აირჩიეთ ენა და დააჭირეთ 'ხმოვანი თარგმნა'-ს.\n", 
            font_size='14sp', 
            size_hint_y=None, 
            text_size=(400, None),
            halign='left',
            valign='top',
            font_name=FONT_NAME
        )
        self.chat_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        scroll = ScrollView(size_hint=(1, 0.32))
        scroll.add_widget(self.chat_label)
        main_layout.add_widget(scroll)
        
        # 6. მართვის ღილაკები
        controls = BoxLayout(orientation='horizontal', size_hint_y=0.13, spacing=10)
        
        self.btn_audio = Button(
            text="🎤 ხმოვანი თარგმნა", 
            font_size='15sp',
            background_color=(0.2, 0.7, 0.3, 1),
            font_name=FONT_NAME
        )
        self.btn_audio.bind(on_press=self.toggle_listening)
        controls.add_widget(self.btn_audio)
        
        self.btn_camera = Button(
            text="📷 კამერით თარგმნა", 
            font_size='15sp',
            background_color=(0.2, 0.5, 0.8, 1),
            font_name=FONT_NAME
        )
        self.btn_camera.bind(on_press=self.capture_and_translate)
        controls.add_widget(self.btn_camera)
        
        main_layout.add_widget(controls)
        return main_layout

    def enable_keep_screen_on(self):
        """ეკრანის გათიშვისგან დაცვის ჩართვა"""
        try:
            activity = PythonActivity.mActivity
            activity.getWindow().addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
        except Exception as e:
            print(f"Keep screen on error: {e}")

    def save_api_key(self, instance):
        key = self.api_input.text.strip()
        self.store.put('api', key=key)
        self.append_text("[სისტემა]: API Key შენახულია მეხსიერებაში!\n")

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
            api_key = self.api_input.text.strip()
            if not api_key:
                self.append_text("[შეცდომა]: გთხოვთ ჯერ შეიყვანოთ Gemini API Key!\n")
                return
            
            self.is_listening = True
            self.should_reconnect = True
            self.btn_audio.text = "⏹ შეჩერება"
            self.btn_audio.background_color = (0.9, 0.2, 0.2, 1)
            selected_lang = self.get_selected_language()
            self.append_text(f"\n[სისტემა]: ჩაირთო Live Translate ({selected_lang})...\n")
            threading.Thread(target=self.start_websocket, daemon=True).start()
        else:
            self.is_listening = False
            self.should_reconnect = False
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
        return f"You are a real-time universal bi-directional translator for {pair}. Translate input audio or image content accurately into the target language. Respond with text and voice."

    def start_websocket(self):
        api_key = self.api_input.text.strip()
        ws_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={api_key}"
        
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
                            # აუდიოს ჩასმა დამუშავების რიგში
                            self.audio_queue.put(pcm_bytes)
            except Exception as e:
                self.append_text(f"\n[შეცდომა მუშავებისას]: {str(e)}\n")

        def on_error(ws, error):
            self.append_text(f"\n[შეცდომა]: {str(error)}\n")

        def on_close(ws, close_status_code, close_msg):
            self.append_text("[სისტემა]: კავშირი გაწყდა.\n")
            if self.is_listening and self.should_reconnect:
                self.append_text("[სისტემა]: ხელახლა დაკავშირება 3 წამში...\n")
                time.sleep(3)
                if self.is_listening:
                    self.start_websocket()

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
                    if self.is_playing_audio:
                        time.sleep(0.05)
                        continue

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
        if self.ws and self.is_listening:
            self.append_text("\n[კამერა]: კადრის გადაღება და გაგზავნა...\n")
            threading.Thread(target=self._capture_and_send_frame, daemon=True).start()
        else:
            self.append_text("[შეცდომა]: ჯერ ჩართეთ 'ხმოვანი თარგმნა'!\n")

    def _capture_and_send_frame(self):
        """კამერის რეალური კადრის ექსპორტი PNG-ში და გაგზავნა Gemini-სთან"""
        try:
            temp_filename = "camera_frame.png"
            if hasattr(self, 'camera_widget') and self.camera_widget:
                self.camera_widget.export_to_png(temp_filename)
                time.sleep(0.3)
                
                if os.path.exists(temp_filename):
                    with open(temp_filename, "rb") as f:
                        img_bytes = f.read()
                    
                    b64_image = base64.b64encode(img_bytes).decode('utf-8')
                    image_msg = {
                        "realtimeInput": {
                            "mediaChunks": [{
                                "mimeType": "image/png",
                                "data": b64_image
                            }]
                        }
                    }
                    if self.ws:
                        self.ws.send(json.dumps(image_msg))
                        self.append_text("[კამერა]: რეალური კადრი გაიგზავნა AI-სთან!\n")
                    
                    os.remove(temp_filename)
                else:
                    self.append_text("[კამერა]: კადრის შენახვა ვერ მოხერხდა.\n")
        except Exception as e:
            self.append_text(f"[კამერის შეცდომა]: {str(e)}\n")

    def _audio_player_worker(self):
        """აუდიო რიგის ფონური დამუშავება"""
        while True:
            pcm_bytes = self.audio_queue.get()
            if pcm_bytes is None:
                break
            self._play_pcm_chunk(pcm_bytes)
            self.audio_queue.task_done()

    def _play_pcm_chunk(self, pcm_bytes):
        if platform == 'android':
            try:
                self.is_playing_audio = True
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
                print(f"Audio playback error: {e}")
            finally:
                self.is_playing_audio = False

if __name__ == '__main__':
    LingoLensApp().run()
