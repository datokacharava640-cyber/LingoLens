import os
import time
import math
import struct
import base64
import threading
import requests

from kivy.app import App
from kivy.clock import mainthread
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform

# 1. ქართული ფონტის გლობალური რეგისტრაცია
FONT_PATH = "NotoSansGeorgian.ttf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name='Roboto', fn_regular=FONT_PATH)

# Gemini API Key
GEMINI_API_KEY = "AQ.Ab8RN6JyGk9aJiWj5FgodDfjlNblEFm_Oa67tjB6jg7fzrinoA"
STREAM_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?key={GEMINI_API_KEY}"


class HybridTTS:
    def __init__(self):
        self.tts = None
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                self.tts = TextToSpeech(PythonActivity.mActivity, None)
            except Exception as e:
                print(f"Native TTS Init Error: {e}")

    def speak(self, text, lang="en"):
        if lang == "ka":
            threading.Thread(target=self._speak_georgian_online, args=(text,), daemon=True).start()
        else:
            if self.tts:
                try:
                    from jnius import autoclass
                    Locale = autoclass('java.util.Locale')
                    self.tts.setLanguage(Locale(lang))
                    self.tts.speak(text, autoclass('android.speech.tts.TextToSpeech').QUEUE_FLUSH, None, None)
                except Exception as e:
                    print(f"TTS Speak Error: {e}")

    def _speak_georgian_online(self, text):
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='ka')
            file_path = "/sdcard/temp_ka.mp3"
            tts.save(file_path)
            sound = SoundLoader.load(file_path)
            if sound:
                sound.play()
        except Exception as e:
            print(f"Georgian Online TTS Error: {e}")


class RealTimeAudioVAD:
    def __init__(self, on_speech_complete_callback, silence_threshold=500, pause_duration=1.2):
        self.silence_threshold = silence_threshold
        self.pause_duration = pause_duration
        self.on_speech_complete = on_speech_complete_callback
        self.is_listening = False
        self.audio_buffer = bytearray()
        self.last_speech_time = time.time()
        self.thread = None

    def calculate_rms(self, chunk):
        count = len(chunk) // 2
        if count == 0:
            return 0
        shorts = struct.unpack(f"%dh" % count, chunk)
        sum_squares = sum(s**2 for s in shorts)
        return math.sqrt(sum_squares / count)

    def start_listening(self):
        self.is_listening = True
        self.audio_buffer.clear()
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.is_listening = False

    def _record_loop(self):
        if platform == 'android':
            try:
                from jnius import autoclass, jarray
                AudioRecord = autoclass('android.media.AudioRecord')
                AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
                AudioFormat = autoclass('android.media.AudioFormat')

                sample_rate = 16000
                channel_config = AudioFormat.CHANNEL_IN_MONO
                audio_format = AudioFormat.ENCODING_PCM_16BIT
                min_buf = AudioRecord.getMinBufferSize(sample_rate, channel_config, audio_format)
                buf_size = max(min_buf, 2048)

                recorder = AudioRecord(
                    AudioSource.MIC,
                    sample_rate,
                    channel_config,
                    audio_format,
                    buf_size
                )

                recorder.startRecording()
                java_buffer = jarray('b')(2048)

                while self.is_listening:
                    read_bytes = recorder.read(java_buffer, 0, 2048)
                    if read_bytes > 0:
                        chunk = bytes(java_buffer[:read_bytes])
                        self._process_chunk(chunk)

                recorder.stop()
                recorder.release()
            except Exception as e:
                print(f"Android AudioRecord Error: {e}")
        else:
            while self.is_listening:
                time.sleep(0.1)

    def _process_chunk(self, chunk):
        rms = self.calculate_rms(chunk)
        current_time = time.time()

        if rms > self.silence_threshold:
            self.audio_buffer.extend(chunk)
            self.last_speech_time = current_time
        else:
            if len(self.audio_buffer) > 0 and (current_time - self.last_speech_time) > self.pause_duration:
                complete_audio = bytes(self.audio_buffer)
                self.audio_buffer.clear()
                self.on_speech_complete(complete_audio)


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        self.status_label = Label(text="LingoLens: მზადაა სამუშაოდ", size_hint_y=0.15, font_size='18sp')
        self.add_widget(self.status_label)

        self.scroll = ScrollView(size_hint=(1, 0.65))
        self.chat_log = Label(
            text="დააჭირეთ ღილაკს რეალურ დროში საუბრის დასაწყებად...",
            size_hint_y=None,
            font_size='16sp',
            halign='left',
            valign='top'
        )
        self.chat_log.bind(size=lambda instance, value: setattr(instance, 'text_size', (value[0], None)))
        self.chat_log.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        self.scroll.add_widget(self.chat_log)
        self.add_widget(self.scroll)

        self.listen_btn = Button(text="საუბრის დაწყება", size_hint_y=0.2, font_size='18sp')
        self.listen_btn.bind(on_press=self.toggle_listening)
        self.add_widget(self.listen_btn)

        self.tts = HybridTTS()
        self.vad = RealTimeAudioVAD(self.process_audio_chunk)
        self.is_active = False

    def toggle_listening(self, instance):
        if not self.is_active:
            self.is_active = True
            self.listen_btn.text = "შეჩერება"
            self.status_label.text = "გასმენთ... (Real-Time Mic Active)"
            self.start_foreground_service()
            self.vad.start_listening()
        else:
            self.is_active = False
            self.listen_btn.text = "საუბრის დაწყება"
            self.status_label.text = "მოსმენა შეჩერებულია"
            self.vad.stop_listening()

    def start_foreground_service(self):
        if platform == 'android':
            try:
                from android import mActivity
                from jnius import autoclass
                service_class = autoclass('org.lingolens.ServiceLingoservice')
                service_class.start(mActivity, '')
            except Exception as e:
                print(f"Service Start Error: {e}")

    def process_audio_chunk(self, audio_bytes):
        self.update_status("ითარგმნება Gemini Streaming API-ით...")
        threading.Thread(target=self._stream_gemini, args=(audio_bytes,), daemon=True).start()

    def _stream_gemini(self, audio_bytes):
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        prompt = "Translate this speech to English (or Georgian if source is English). Output only translated text."

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}
                ]
            }]
        }

        try:
            response = requests.post(STREAM_URL, json=payload, stream=True, timeout=10)
            full_translated_text = ""

            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    full_translated_text += decoded + " "
                    self.append_chat_log(decoded)

            if full_translated_text:
                self.tts.speak(full_translated_text, lang="en")

        except Exception as e:
            self.append_chat_log(f"\n[API შეცდომა: {e}]")
        finally:
            self.update_status("გასმენთ... (Real-Time Mic Active)")

    @mainthread
    def update_status(self, text):
        self.status_label.text = text

    @mainthread
    def append_chat_log(self, text):
        self.chat_log.text += f"\n{text}"


class LingoLensApp(App):
    def build(self):
        return MainLayout()

    def on_start(self):
        self.request_android_permissions()

    def request_android_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                permissions = [
                    Permission.RECORD_AUDIO,
                    Permission.POST_NOTIFICATIONS,
                    Permission.FOREGROUND_SERVICE,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ]
                request_permissions(permissions)

                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')

                activity = PythonActivity.mActivity
                pkg_name = activity.getPackageName()
                pm = activity.getSystemService(PythonActivity.POWER_SERVICE)

                if not pm.isIgnoringBatteryOptimizations(pkg_name):
                    intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                    intent.setData(Uri.parse(f"package:{pkg_name}"))
                    activity.startActivity(intent)
            except Exception as e:
                print(f"Permission / Battery Optimization Error: {e}")


if __name__ == '__main__':
    LingoLensApp().run()
