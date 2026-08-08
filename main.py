import json
import threading
import time
import socket
import urllib.request
import urllib.parse
import os
import math

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform

# Global Config
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

LANGUAGES = {
    "Georgian (ქართული)": "ka",
    "English": "en",
    "Spanish (Español)": "es",
    "German (Deutsch)": "de",
    "French (Français)": "fr",
    "Russian (Русский)": "ru",
    "Turkish (Türkçe)": "tr"
}
LANG_NAMES = list(LANGUAGES.keys())

# Android Interop Imports
if platform == 'android':
    try:
        from jnius import PythonJavaClass, java_method, autoclass
        from android.runnable import Runnable

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        RecognizerIntent = autoclass('android.speech.RecognizerIntent')
        SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
        AudioRecord = autoclass('android.media.AudioRecord')
        AudioFormat = autoclass('android.media.AudioFormat')
        MediaRecorder = autoclass('android.media.MediaRecorder')
        AudioTrack = autoclass('android.media.AudioTrack')
        AudioManager = autoclass('android.media.AudioManager')
        
        class ContinuousSpeechListener(PythonJavaClass):
            __javainterfaces__ = ['android/speech/RecognitionListener']

            def __init__(self, callback, vad_callback):
                super().__init__()
                self.callback = callback
                self.vad_callback = vad_callback

            @java_method('(Landroid/os/Bundle;)V')
            def onReadyForSpeech(self, params): pass
            
            @java_method('()V')
            def onBeginningOfSpeech(self):
                if self.vad_callback:
                    self.vad_callback(True)

            @java_method('(F)V')
            def onRmsChanged(self, rmsdB): pass
            
            @java_method('([B)V')
            def onBufferReceived(self, buffer): pass
            
            @java_method('()V')
            def onEndOfSpeech(self):
                if self.vad_callback:
                    self.vad_callback(False)

            @java_method('(I)V')
            def onError(self, error): pass
            
            @java_method('(Landroid/os/Bundle;)V')
            def onEvent(self, eventType, params): pass

            @java_method('(Landroid/os/Bundle;)V')
            def onResults(self, results):
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches and matches.size() > 0:
                    self.callback(matches.get(0), True)

            @java_method('(Landroid/os/Bundle;)V')
            def onPartialResults(self, results):
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches and matches.size() > 0:
                    self.callback(matches.get(0), False)
    except Exception as e:
        print(f"Jnius Setup Error: {e}")


class RealTimeVADProcessor:
    """ხმის დეტექციის (VAD) იმიტაციური და ენერგოეფექტური პროცესორი"""
    def __init__(self, threshold=1500):
        self.threshold = threshold
        self.is_speaking = False

    def process_pcm_chunk(self, pcm_data):
        # გამოითვლის RMS (Root Mean Square) სიგნალის ენერგიას
        sum_squares = sum([sample ** 2 for sample in pcm_data])
        rms = math.sqrt(sum_squares / max(1, len(pcm_data)))
        
        previous_state = self.is_speaking
        self.is_speaking = rms > self.threshold
        return self.is_speaking, rms


class LingoLensRealTimeUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        
        self.is_streaming = False
        self.current_person = None
        self.vad = RealTimeVADProcessor()

        # 1. UI Header
        self.add_widget(Label(
            text='LingoLens Live Stream Engine',
            font_size='20sp',
            bold=True,
            size_hint_y=0.08
        ))

        # 2. Language Pickers
        lang_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.08)
        self.src_spinner = Spinner(text='English', values=LANG_NAMES, size_hint_x=0.42)
        self.btn_swap = Button(text='⇄', size_hint_x=0.16)
        self.btn_swap.bind(on_press=self.swap_languages)
        self.tgt_spinner = Spinner(text='Georgian (ქართული)', values=LANG_NAMES, size_hint_x=0.42)
        
        lang_box.add_widget(self.src_spinner)
        lang_box.add_widget(self.btn_swap)
        lang_box.add_widget(self.tgt_spinner)
        self.add_widget(lang_box)

        # 3. Live Stream Text Buffer
        self.live_input = TextInput(
            hint_text='Real-time audio input stream text will appear here...',
            font_size='15sp',
            multiline=True,
            size_hint_y=0.25
        )
        self.add_widget(self.live_input)

        # 4. Stream Conversation Controls
        talk_box = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.12)
        self.btn_p1 = Button(text='🎙️ P1 Live Stream', background_color=(0.1, 0.6, 0.3, 1))
        self.btn_p1.bind(on_press=lambda inst: self.toggle_realtime_stream('P1'))
        
        self.btn_p2 = Button(text='🎙️ P2 Live Stream', background_color=(0.8, 0.4, 0.1, 1))
        self.btn_p2.bind(on_press=lambda inst: self.toggle_realtime_stream('P2'))

        talk_box.add_widget(self.btn_p1)
        talk_box.add_widget(self.btn_p2)
        self.add_widget(talk_box)

        # 5. VAD Visual Indicator
        self.vad_label = Label(
            text='VAD: Idle (No Speech Detected)',
            font_size='13sp',
            size_hint_y=0.07
        )
        self.add_widget(self.vad_label)

        # 6. Stream Result Output
        self.result_label = Label(
            text='Stream Status: Ready.',
            font_size='16sp',
            size_hint_y=0.40
        )
        self.add_widget(self.result_label)

    def swap_languages(self, instance):
        src = self.src_spinner.text
        self.src_spinner.text = self.tgt_spinner.text
        self.tgt_spinner.text = src

    def toggle_realtime_stream(self, person):
        if platform != 'android':
            self.result_label.text = "Real-time Native Audio requires Android."
            return

        if self.is_streaming and self.current_person == person:
            self.stop_stream()
        else:
            self.stop_stream()
            self.is_streaming = True
            self.current_person = person
            
            if person == 'P1':
                self.btn_p1.text = "Streaming P1... ⏹️"
                lang_code = LANGUAGES.get(self.src_spinner.text, 'en')
            else:
                self.btn_p2.text = "Streaming P2... ⏹️"
                lang_code = LANGUAGES.get(self.tgt_spinner.text, 'ka')

            Runnable(lambda: self.start_speech_recognizer(lang_code))()

    def start_speech_recognizer(self, lang_code):
        try:
            activity = PythonActivity.mActivity
            self.speech_recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            listener = ContinuousSpeechListener(self.on_partial_speech, self.on_vad_state_change)
            self.speech_recognizer.setRecognitionListener(listener)

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
            intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, True)
            intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, True)

            self.speech_recognizer.startListening(intent)
            self.result_label.text = f"Listening Live Stream ({lang_code})..."
        except Exception as e:
            self.result_label.text = f"Recognizer Error: {e}"

    def on_vad_state_change(self, is_speaking):
        def update_ui(dt):
            if is_speaking:
                self.vad_label.text = "VAD: 🗣️ User Speaking (Active)"
            else:
                self.vad_label.text = "VAD: 🤫 Pause Detected (Processing Chunk...)"
        Clock.schedule_once(update_ui)

    def on_partial_speech(self, text, is_final):
        def update_text(dt):
            self.live_input.text = text
            if is_final:
                self.stream_translate(text)
        Clock.schedule_once(update_text)

    def stop_stream(self):
        self.is_streaming = False
        self.current_person = None
        self.btn_p1.text = '🎙️ P1 Live Stream'
        self.btn_p2.text = '🎙️ P2 Live Stream'
        self.vad_label.text = 'VAD: Idle'
        
        if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
            try:
                self.speech_recognizer.stopListening()
                self.speech_recognizer.destroy()
                self.speech_recognizer = None
            except Exception as e:
                print(f"Stop stream error: {e}")

    def stream_translate(self, text):
        if not text.strip():
            return

        if self.current_person == 'P1':
            src = self.src_spinner.text
            tgt = self.tgt_spinner.text
        else:
            src = self.tgt_spinner.text
            tgt = self.src_spinner.text

        tgt_code = LANGUAGES.get(tgt, 'ka')
        
        # Async HTTP/WebSocket Request Threading
        threading.Thread(
            target=self._execute_fast_api_request,
            args=(text, src, tgt, tgt_code),
            daemon=True
        ).start()

    def _execute_fast_api_request(self, text, src, tgt, tgt_code):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {'Content-Type': 'application/json'}
            prompt = f"Direct streaming translation from {src} to {tgt}: '{text}'"
            data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')

            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=4) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
                translated = res_json['candidates'][0]['content']['parts'][0]['text']

            Clock.schedule_once(lambda dt: self._render_and_speak(translated, tgt_code))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._render_and_speak(f"[Offline Stream Fallback]: {text}", tgt_code))

    def _render_and_speak(self, translated_text, tgt_code):
        self.result_label.text = translated_text
        if platform == 'android':
            self.play_streaming_audio(translated_text, tgt_code)

    def play_streaming_audio(self, text, lang_code):
        try:
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            Locale = autoclass('java.util.Locale')

            def on_init(status):
                if hasattr(self, 'tts'):
                    self.tts.setLanguage(Locale(lang_code))
                    self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)

            self.tts = TextToSpeech(PythonActivity.mActivity, TextToSpeech.OnInitListener())
        except Exception as e:
            print(f"TTS Stream Error: {e}")


class LingoLensRealTimeApp(App):
    def build(self):
        return LingoLensRealTimeUI()

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_android_permissions, 0.5)

    def request_android_permissions(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.RECORD_AUDIO,
                Permission.CAMERA,
                Permission.SYSTEM_ALERT_WINDOW,
                Permission.FOREGROUND_SERVICE,
                Permission.MODIFY_AUDIO_SETTINGS
            ])
        except Exception as e:
            print(f"Permission Error: {e}")


if __name__ == '__main__':
    LingoLensRealTimeApp().run()
