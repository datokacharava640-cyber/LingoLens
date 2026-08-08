import json
import base64
import threading
import urllib.request
import urllib.parse
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.utils import platform

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# მსოფლიო ენების სია (სახელი: ISO კოდი)
LANGUAGES = {
    "Georgian (ქართული)": "ka",
    "English": "en",
    "Spanish (Español)": "es",
    "German (Deutsch)": "de",
    "French (Français)": "fr",
    "Russian (Русский)": "ru",
    "Turkish (Türkçe)": "tr",
    "Italian (Italiano)": "it",
    "Chinese (中文)": "zh",
    "Arabic (العربية)": "ar"
}

LANG_NAMES = list(LANGUAGES.keys())

# Android ქართული შრიფტი
GEORGIAN_FONT = None
if platform == 'android':
    possible_fonts = [
        "/system/fonts/NotoSansGeorgian-Regular.ttf",
        "/system/fonts/NotoSansGeorgian-VF.ttf",
        "/system/fonts/DroidSans.ttf"
    ]
    for font_path in possible_fonts:
        if os.path.exists(font_path):
            GEORGIAN_FONT = font_path
            break

# Android Native Java Interop
if platform == 'android':
    try:
        from jnius import PythonJavaClass, java_method, autoclass
        from android.runnable import Runnable

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        RecognizerIntent = autoclass('android.speech.RecognizerIntent')
        SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
        PixelFormat = autoclass('android.graphics.PixelFormat')
        WindowManager = autoclass('android.view.WindowManager')
        LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
        TextView = autoclass('android.widget.TextView')

        class ContinuousSpeechListener(PythonJavaClass):
            __javainterfaces__ = ['android/speech/RecognitionListener']

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method('(Landroid/os/Bundle;)V')
            def onReadyForSpeech(self, params): pass
            @java_method('()V')
            def onBeginningOfSpeech(self): pass
            @java_method('(F)V')
            def onRmsChanged(self, rmsdB): pass
            @java_method('([B)V')
            def onBufferReceived(self, buffer): pass
            @java_method('()V')
            def onEndOfSpeech(self): pass
            @java_method('(I)V')
            def onError(self, error): pass
            @java_method('(Landroid/os/Bundle;)V')
            def onEvent(self, eventType, params): pass

            @java_method('(Landroid/os/Bundle;)V')
            def onResults(self, results):
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches and matches.size() > 0:
                    self.callback(matches.get(0))

            @java_method('(Landroid/os/Bundle;)V')
            def onPartialResults(self, results):
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches and matches.size() > 0:
                    self.callback(matches.get(0))
    except Exception as e:
        print(f"Jnius setup exception: {e}")


class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 12
        self.spacing = 8
        self.debounce_event = None
        self.speech_recognizer = None
        self.current_listening_mode = None

        # 1. სათაური
        self.add_widget(Label(
            text='LingoLens 2-Way AI Live',
            font_size='20sp',
            bold=True,
            size_hint_y=0.08
        ))

        # 2. ენების არჩევის პანელი (Source -> Swap -> Target)
        lang_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.08)
        
        self.src_spinner = Spinner(
            text='English',
            values=LANG_NAMES,
            size_hint_x=0.42
        )
        self.btn_swap = Button(text='⇄', size_hint_x=0.16, background_color=(0.3, 0.3, 0.8, 1))
        self.btn_swap.bind(on_press=self.swap_languages)
        
        self.tgt_spinner = Spinner(
            text='Georgian (ქართული)',
            values=LANG_NAMES,
            size_hint_x=0.42
        )

        lang_box.add_widget(self.src_spinner)
        lang_box.add_widget(self.btn_swap)
        lang_box.add_widget(self.tgt_spinner)
        self.add_widget(lang_box)

        # 3. ტექსტის შეყვანის ველი
        self.input_text = TextInput(
            hint_text='Type text or use 2-Way Speech below...',
            font_size='15sp',
            multiline=True,
            size_hint_y=0.24
        )
        self.input_text.bind(text=self.on_text_change)
        self.add_widget(self.input_text)

        # 4. ორმხრივი დიალოგის ღილაკები (Two-Way Live Voice)
        talk_box = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.12)
        
        self.btn_talk_p1 = Button(text='🎙️ Person 1 Speak', background_color=(0.1, 0.6, 0.3, 1))
        self.btn_talk_p1.bind(on_press=lambda inst: self.toggle_voice_mode('P1'))
        
        self.btn_talk_p2 = Button(text='🎙️ Person 2 Speak', background_color=(0.8, 0.4, 0.1, 1))
        self.btn_talk_p2.bind(on_press=lambda inst: self.toggle_voice_mode('P2'))

        talk_box.add_widget(self.btn_talk_p1)
        talk_box.add_widget(self.btn_talk_p2)
        self.add_widget(talk_box)

        # 5. დამატებითი ინსტრუმენტების პანელი
        grid = GridLayout(cols=3, spacing=8, size_hint_y=0.12)

        btn_ai = Button(text='Translate', background_color=(0.1, 0.5, 0.9, 1))
        btn_ai.bind(on_press=lambda inst: self.trigger_translation())
        grid.add_widget(btn_ai)

        btn_cam = Button(text='OCR Cam', background_color=(0.6, 0.3, 0.7, 1))
        btn_cam.bind(on_press=self.open_camera_ocr)
        grid.add_widget(btn_cam)

        btn_overlay = Button(text='Overlay', background_color=(0.3, 0.7, 0.8, 1))
        btn_overlay.bind(on_press=self.enable_overlay_window)
        grid.add_widget(btn_overlay)

        self.add_widget(grid)

        # 6. შედეგის ფანჯარა
        label_kwargs = {
            'text': 'Ready for 2-way real-time translation.',
            'font_size': '15sp',
            'size_hint_y': 0.36
        }
        if GEORGIAN_FONT:
            label_kwargs['font_name'] = GEORGIAN_FONT

        self.result_label = Label(**label_kwargs)
        self.add_widget(self.result_label)

    def swap_languages(self, instance):
        src = self.src_spinner.text
        self.src_spinner.text = self.tgt_spinner.text
        self.tgt_spinner.text = src

    def on_text_change(self, instance, value):
        if self.debounce_event:
            self.debounce_event.cancel()
        if value.strip() and not self.current_listening_mode:
            self.debounce_event = Clock.schedule_once(lambda dt: self.trigger_translation(), 0.4)

    # 1️⃣ ORMXRIVI DIALOGI (Two-Way Live Voice)
    def toggle_voice_mode(self, person):
        if platform != 'android':
            self.result_label.text = "Voice speech is supported on Android."
            return

        if self.current_listening_mode == person:
            self.stop_speech()
        else:
            self.stop_speech()
            self.current_listening_mode = person
            if person == 'P1':
                self.btn_talk_p1.text = "Listening P1... ⏹️"
                lang_code = LANGUAGES.get(self.src_spinner.text, 'en')
            else:
                self.btn_talk_p2.text = "Listening P2... ⏹️"
                lang_code = LANGUAGES.get(self.tgt_spinner.text, 'ka')

            Runnable(lambda: self.start_speech(lang_code))()

    def start_speech(self, lang_code):
        try:
            activity = PythonActivity.mActivity
            self.speech_recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            listener = ContinuousSpeechListener(self.on_speech_recognized)
            self.speech_recognizer.setRecognitionListener(listener)

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
            intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, True)
            
            self.speech_recognizer.startListening(intent)
            self.result_label.text = f"Listening in ({lang_code})..."
        except Exception as e:
            self.result_label.text = f"Speech Error: {e}"

    def stop_speech(self):
        self.btn_talk_p1.text = '🎙️ Person 1 Speak'
        self.btn_talk_p2.text = '🎙️ Person 2 Speak'
        self.current_listening_mode = None
        if self.speech_recognizer:
            try:
                self.speech_recognizer.stopListening()
                self.speech_recognizer.destroy()
                self.speech_recognizer = None
            except Exception as e:
                print(f"Stop speech error: {e}")

    def on_speech_recognized(self, text):
        Clock.schedule_once(lambda dt: self._process_speech_input(text))

    def _process_speech_input(self, text):
        self.input_text.text = text
        # ორმხრივ დიალოგში თარგმნა სრულდება და ავტომატურად იკითხება ხმით (Auto TTS)
        if self.current_listening_mode == 'P1':
            src_lang = self.src_spinner.text
            tgt_lang = self.tgt_spinner.text
        else:
            src_lang = self.tgt_spinner.text
            tgt_lang = self.src_spinner.text

        self.trigger_translation(custom_src=src_lang, custom_tgt=tgt_lang, auto_speak=True)

    # 2️⃣ GEMINI DYNAMIC TRANSLATION
    def trigger_translation(self, custom_src=None, custom_tgt=None, auto_speak=False):
        text = self.input_text.text.strip()
        if not text:
            return

        src_name = custom_src if custom_src else self.src_spinner.text
        tgt_name = custom_tgt if custom_tgt else self.tgt_spinner.text
        tgt_code = LANGUAGES.get(tgt_name, 'ka')

        self.result_label.text = f"Translating {src_name} -> {tgt_name}..."
        threading.Thread(
            target=self._fetch_translation,
            args=(text, src_name, tgt_name, tgt_code, auto_speak),
            daemon=True
        ).start()

    def _fetch_translation(self, text, src_name, tgt_name, tgt_code, auto_speak):
        try:
            if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                headers = {'Content-Type': 'application/json'}
                prompt = f"Translate accurately from {src_name} to {tgt_name}: '{text}'"
                data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
                
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=6) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    translated = res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                sl = LANGUAGES.get(src_name, 'auto')
                tl = LANGUAGES.get(tgt_name, 'ka')
                encoded = urllib.parse.quote(text)
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={encoded}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    translated = "".join([s[0] for s in res_data[0] if s[0]])

            Clock.schedule_once(lambda dt: self._update_result(translated, tgt_code, auto_speak))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_result(f"Translation Error: {e}", None, False))

    def _update_result(self, text, tgt_code, auto_speak):
        self.result_label.text = text
        if auto_speak and tgt_code and platform == 'android':
            self.speak_audio(text, tgt_code)

    def speak_audio(self, text, lang_code):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            Locale = autoclass('java.util.Locale')

            def on_init(status):
                if hasattr(self, 'tts'):
                    self.tts.setLanguage(Locale(lang_code))
                    self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)

            self.tts = TextToSpeech(PythonActivity.mActivity, TextToSpeech.OnInitListener())
        except Exception as e:
            print(f"TTS error: {e}")

    # 3️⃣ CAMERA OCR
    def open_camera_ocr(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        try:
            self.cam = Camera(play=True, resolution=(640, 480))
            content.add_widget(self.cam)
        except Exception as e:
            content.add_widget(Label(text=f"Camera error: {e}"))

        btn_capture = Button(text="Scan Text", size_hint_y=0.2, background_color=(0.2, 0.8, 0.2, 1))
        btn_capture.bind(on_press=self._process_ocr_scan)
        content.add_widget(btn_capture)

        self.cam_popup = Popup(title="AI OCR Scanner", content=content, size_hint=(0.95, 0.85))
        self.cam_popup.open()

    def _process_ocr_scan(self, instance):
        try:
            self.cam.export_to_png("ocr_frame.png")
            if hasattr(self, 'cam_popup'):
                self.cam_popup.dismiss()
            
            self.result_label.text = "Extracting text..."
            threading.Thread(target=self._run_ai_ocr, daemon=True).start()
        except Exception as e:
            self.result_label.text = f"OCR Error: {e}"

    def _run_ai_ocr(self):
        try:
            if os.path.exists("ocr_frame.png") and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
                with open("ocr_frame.png", "rb") as image_file:
                    img_b64 = base64.b64encode(image_file.read()).decode('utf-8')
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                headers = {'Content-Type': 'application/json'}
                data = json.dumps({
                    "contents": [{
                        "parts": [
                            {"text": "Extract all text from this image directly."},
                            {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                        ]
                    }]
                }).encode('utf-8')

                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=8) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    extracted = res_json['candidates'][0]['content']['parts'][0]['text']
                    Clock.schedule_once(lambda dt: self._set_ocr_text(extracted))
            else:
                Clock.schedule_once(lambda dt: self._set_ocr_text("Extracted text sample"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_result(f"OCR Error: {e}", None, False))

    def _set_ocr_text(self, text):
        self.input_text.text = text.strip()

    # 4️⃣ OVERLAY WINDOW
    def enable_overlay_window(self, instance):
        if platform == 'android':
            try:
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                activity = PythonActivity.mActivity

                if not Settings.canDrawOverlays(activity):
                    self.result_label.text = "Grant Overlay Permission..."
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    Runnable(self.spawn_floating_widget)()
            except Exception as e:
                self.result_label.text = f"Overlay error: {e}"
        else:
            self.result_label.text = "Overlay Mode active."

    def spawn_floating_widget(self):
        try:
            activity = PythonActivity.mActivity
            wm = activity.getSystemService(activity.WINDOW_SERVICE)

            tv = TextView(activity)
            tv.setText(" LingoLens Live ")
            tv.setTextSize(16.0)

            params = LayoutParams(
                LayoutParams.WRAP_CONTENT,
                LayoutParams.WRAP_CONTENT,
                LayoutParams.TYPE_APPLICATION_OVERLAY,
                LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT
            )
            wm.addView(tv, params)
            self.result_label.text = "Floating Widget Attached!"
        except Exception as e:
            self.result_label.text = f"Widget spawn error: {e}"


class LingoLensApp(App):
    def build(self):
        return LingoLensUI()

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.get_permissions, 0.5)

    def get_permissions(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.SYSTEM_ALERT_WINDOW,
                Permission.FOREGROUND_SERVICE
            ])
        except Exception as e:
            print(f"Permissions error: {e}")


if __name__ == '__main__':
    LingoLensApp().run()
