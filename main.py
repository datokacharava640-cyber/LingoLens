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
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.camera import Camera as KivyCamera
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

FONT_NAME = "NotoSansGeorgian.ttf" if os.path.exists("NotoSansGeorgian.ttf") else None

if platform == 'android':
    from jnius import autoclass, jarray
    from android.permissions import request_permissions, Permission
    
    AudioRecord = autoclass('android.media.AudioRecord')
    AudioTrack = autoclass('android.media.AudioTrack')
    AudioFormat = autoclass('android.media.AudioFormat')
    MediaRecorder = autoclass('android.media.MediaRecorder')
    AudioManager = autoclass('android.media.AudioManager')
    
    # AudioFX ხმაურის ჩასახშობად
    NoiseSuppressor = autoclass('android.media.audiofx.NoiseSuppressor')
    AutomaticGainControl = autoclass('android.media.audiofx.AutomaticGainControl')
    
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')

class LingoLensApp(App):
    def build(self):
        self.is_listening = False
        self.is_playing_audio = False
        self.is_live_cam_active = False
        self.ws = None
        self.should_reconnect = True
        self.last_ping_time = 0
        
        # აუდიო ნაკადის რიგი
        self.audio_queue = queue.Queue()
        threading.Thread(target=self._audio_player_worker, daemon=True).start()

        self.store = JsonStore('settings.json')
        saved_key = self.store.get('api')['key'] if self.store.exists('api') else ""

        if platform == 'android':
            request_permissions([
                Permission.RECORD_AUDIO, 
                Permission.INTERNET, 
                Permission.CAMERA
            ])
            self.enable_keep_screen_on()

        main_layout = BoxLayout(orientation='vertical', padding=8, spacing=6)
        
        # 1. API Key + Ping / Latency Indicator
        key_bar = BoxLayout(orientation='horizontal', size_hint_y=0.07, spacing=5)
        self.api_input = TextInput(
            text=saved_key, 
            hint_text="Gemini API Key", 
            password=True, 
            multiline=False,
            font_name=FONT_NAME
        )
        btn_save_key = Button(
            text="💾", 
            size_hint_x=0.15, 
            background_color=(0.3, 0.6, 0.9, 1),
            font_name=FONT_NAME
        )
        btn_save_key.bind(on_press=self.save_api_key)
        
        self.ping_label = Label(
            text="🔴 Offline", 
            size_hint_x=0.25, 
            font_size='12sp',
            font_name=FONT_NAME
        )
        key_bar.add_widget(self.api_input)
        key_bar.add_widget(btn_save_key)
        key_bar.add_widget(self.ping_label)
        main_layout.add_widget(key_bar)

        # 2. ენების არჩევანი
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.07, spacing=5)
        self.status_label = Label(text="LingoLens Live", font_size='15sp', size_hint_x=0.3, font_name=FONT_NAME)
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
                'CUSTOM (ხელით შეყვანა)'
            ),
            size_hint_x=0.7,
            font_name=FONT_NAME
        )
        self.lang_spinner.bind(text=self.on_language_change)
        top_bar.add_widget(self.lang_spinner)
        main_layout.add_widget(top_bar)

        self.custom_lang_input = TextInput(
            text="Georgian <-> Italian",
            hint_text="მიუთითეთ ენები",
            multiline=False,
            size_hint_y=0.06,
            opacity=0,
            disabled=True,
            font_name=FONT_NAME
        )
        main_layout.add_widget(self.custom_lang_input)

        # 3. კამერის Preview + AR Text Overlay
        cam_container = FloatLayout(size_hint_y=0.38)
        try:
            self.camera_widget = KivyCamera(index=0, resolution=(640, 480), play=True, pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))
            cam_container.add_widget(self.camera_widget)
        except Exception as e:
            self.append_text(f"[კამერის ჩართვა]: {str(e)}\n")

        # AR Overlay Label (ტექსტი კამერის თავზე)
        self.ar_overlay_label = Label(
            text="[AR Live Translation]", 
            font_size='16sp',
            pos_hint={'x': 0.05, 'y': 0.75},
            size_hint=(0.9, 0.2),
            color=(1, 1, 0, 1),
            font_name=FONT_NAME
        )
        cam_container.add_widget(self.ar_overlay_label)
        main_layout.add_widget(cam_container)

        # 4. ტექსტური ისტორია
        self.chat_label = Label(
            text="[სისტემა]: აპლიკაცია მზადაა.\n", 
            font_size='13sp', 
            size_hint_y=None, 
            text_size=(400, None),
            halign='left',
            valign='top',
            font_name=FONT_NAME
        )
        self.chat_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        scroll = ScrollView(size_hint=(1, 0.28))
        scroll.add_widget(self.chat_label)
        main_layout.add_widget(scroll)
        
        # 5. მართვის ღილაკები
        controls = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=5)
        
        self.btn_audio = Button(
            text="🎤 ხმა", 
            font_size='14sp',
            background_color=(0.2, 0.7, 0.3, 1),
            font_name=FONT_NAME
        )
        self.btn_audio.bind(on_press=self.toggle_listening)
        controls.add_widget(self.btn_audio)
        
        self.btn_live_cam = Button(
            text="📷 Live Cam", 
            font_size='14sp',
            background_color=(0.2, 0.5, 0.8, 1),
            font_name=FONT_NAME
        )
        self.btn_live_cam.bind(on_press=self.toggle_live_camera)
        controls.add_widget(self.btn_live_cam)

        # Barge-in/Interruption Button
        self.btn_interrupt = Button(
            text="⛔ შეწყვეტა", 
            font_size='14sp',
            background_color=(0.8, 0.3, 0.2, 1),
            font_name=FONT_NAME
        )
        self.btn_interrupt.bind(on_press=self.interrupt_ai_speech)
        controls.add_widget(self.btn_interrupt)
        
        main_layout.add_widget(controls)
        return main_layout

    def enable_keep_screen_on(self):
        try:
            activity = PythonActivity.mActivity
            activity.getWindow().addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
        except Exception as e:
            print(f"Keep screen on error: {e}")

    def save_api_key(self, instance):
        key = self.api_input.text.strip()
        self.store.put('api', key=key)
        self.append_text("[სისტემა]: API Key შენახულია!\n")

    def interrupt_ai_speech(self, instance=None):
        """Barge-in / AI საუბრის შეწყვეტა"""
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
        self.is_playing_audio = False
        self.append_text("[სისტემა]: AI საუბარი შეწყდა.\n")

    def toggle_live_camera(self, instance):
        """Auto Live Video Streaming Toggle"""
        self.is_live_cam_active = not self.is_live_cam_active
        if self.is_live_cam_active:
            self.btn_live_cam.text = "📷 Live: ON"
            self.btn_live_cam.background_color = (0.9, 0.5, 0.1, 1)
            Clock.schedule_interval(self._auto_capture_frame, 2.0)
            self.append_text("[კამერა]: Live კადრების ავტო-გაგზავნა ჩაირთო (2s).\n")
        else:
            self.btn_live_cam.text = "📷 Live Cam"
            self.btn_live_cam.background_color = (0.2, 0.5, 0.8, 1)
            Clock.unschedule(self._auto_capture_frame)
            self.append_text("[კამერა]: Live კადრების ავტო-გაგზავნა გაჩერდა.\n")

    def _auto_capture_frame(self, dt):
        if self.ws and self.is_listening:
            threading.Thread(target=self._capture_and_send_frame, daemon=True).start()

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
                self.append_text("[შეცდომა]: შეიყვანეთ Gemini API Key!\n")
                return
            
            self.is_listening = True
            self.should_reconnect = True
            self.btn_audio.text = "⏹ გაჩერება"
            self.btn_audio.background_color = (0.9, 0.2, 0.2, 1)
            self.append_text(f"\n[სისტემა]: Live Translate ({self.get_selected_language()})...\n")
            threading.Thread(target=self.start_websocket, daemon=True).start()
        else:
            self.is_listening = False
            self.should_reconnect = False
            self.btn_audio.text = "🎤 ხმა"
            self.btn_audio.background_color = (0.2, 0.7, 0.3, 1)
            if self.ws:
                self.ws.close()
            self.ping_label.text = "🔴 Offline"
            self.append_text("[სისტემა]: გაჩერდა.\n")

    def append_text(self, text):
        Clock.schedule_once(lambda dt: self._update_ui_text(text))

    def _update_ui_text(self, text):
        self.chat_label.text += text

    def get_system_prompt(self):
        pair = self.get_selected_language()
        return f"You are a real-time universal bi-directional translator for {pair}. Translate input audio or image content accurately into the target language. Respond with text and speech."

    def start_websocket(self):
        api_key = self.api_input.text.strip()
        ws_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={api_key}"
        
        def on_open(ws):
            self.last_ping_time = time.time()
            self.append_text("[AI]: მიერთებულია!\n")
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
            # Ping/Latency გამოთვლა
            latency = int((time.time() - self.last_ping_time) * 1000)
            self.last_ping_time = time.time()
            Clock.schedule_once(lambda dt: setattr(self.ping_label, 'text', f"🟢 {latency}ms"))

            try:
                data = json.loads(message)
                if "serverContent" in data and "modelTurn" in data["serverContent"]:
                    parts = data["serverContent"]["modelTurn"].get("parts", [])
                    for part in parts:
                        if "text" in part:
                            translated_text = part['text']
                            self.append_text(f"[AI]: {translated_text}\n")
                            # AR Overlay-ზე ტექსტის გამოჩენა
                            Clock.schedule_once(lambda dt: setattr(self.ar_overlay_label, 'text', translated_text))
                        if "inlineData" in part and part["inlineData"].get("mimeType", "").startswith("audio/"):
                            pcm_base64 = part["inlineData"]["data"]
                            pcm_bytes = base64.b64decode(pcm_base64)
                            self.audio_queue.put(pcm_bytes)
            except Exception as e:
                self.append_text(f"\n[შეცდომა]: {str(e)}\n")

        def on_error(ws, error):
            Clock.schedule_once(lambda dt: setattr(self.ping_label, 'text', "🟡 Err"))
            self.append_text(f"\n[შეცდომა]: {str(error)}\n")

        def on_close(ws, close_status_code, close_msg):
            Clock.schedule_once(lambda dt: setattr(self.ping_label, 'text', "🔴 Offline"))
            self.append_text("[სისტემა]: კავშირი გაწყდა.\n")
            if self.is_listening and self.should_reconnect:
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
        """Android Native Audio Recording + Noise Suppression & AGC"""
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

                # Noise Suppression & AGC
                try:
                    session_id = recorder.getAudioSessionId()
                    if NoiseSuppressor.isAvailable():
                        NoiseSuppressor.create(session_id)
                    if AutomaticGainControl.isAvailable():
                        AutomaticGainControl.create(session_id)
                except Exception as fx_err:
                    print(f"AudioFX init error: {fx_err}")

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

    def _capture_and_send_frame(self):
        try:
            temp_filename = "camera_frame.png"
            if hasattr(self, 'camera_widget') and self.camera_widget:
                self.camera_widget.export_to_png(temp_filename)
                time.sleep(0.2)
                
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
                    
                    os.remove(temp_filename)
        except Exception as e:
            print(f"Frame capture error: {e}")

    def _audio_player_worker(self):
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
