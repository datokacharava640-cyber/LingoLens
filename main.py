import os
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
import threading

try:
    from jnius import autoclass, PythonJavaClass, java_method
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    String = autoclass('java.lang.String')
    MediaStore = autoclass('android.provider.MediaStore')

    class TTSInitListener(PythonJavaClass):
        __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
        def __init__(self):
            super().__init__()
        @java_method('(I)V')
        def onInit(self, status):
            pass

    ANDROID_NATIVE_AVAILABLE = True
except Exception:
    ANDROID_NATIVE_AVAILABLE = False

try:
    from plyer import gps
    from android.permissions import request_permissions, Permission
    ANDROID_PLYER_AVAILABLE = True
except Exception:
    ANDROID_PLYER_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

WORLD_LANGUAGES = {
    "Georgian": "ka",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Russian": "ru",
    "Chinese": "zh",
    "Japanese": "ja",
    "Arabic": "ar",
    "Tagalog": "tl",
    "Portuguese": "pt",
    "Italian": "it",
    "Turkish": "tr",
    "Korean": "ko",
    "Hindi": "hi",
    "Ukrainian": "uk",
    "Polish": "pl",
    "Greek": "el",
    "Hebrew": "he",
    "Armenian": "hy",
    "Azerbaijani": "az",
    "Persian": "fa"
}

Window.clearcolor = (0.07, 0.08, 0.10, 1)
Window.softinput_mode = "below_target"


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.selected_lang_name = "Georgian"
        self.target_lang_code = "ka"
        self.chat_history = []
        self.tts = None
        self.tts_listener = None
        self.last_ai_text = ""

        if ANDROID_PLYER_AVAILABLE:
            try:
                request_permissions([
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.ACCESS_FINE_LOCATION,
                    Permission.ACCESS_COARSE_LOCATION,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception as perm_err:
                print("Permission request error:", perm_err)

        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                self.tts_listener = TTSInitListener()
                self.tts = TextToSpeech(activity, self.tts_listener)
                activity.bind(on_activity_result=self.on_activity_result)
            except Exception as e:
                print("Native Init Error:", e)

        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        root = BoxLayout(orientation='vertical', padding=6, spacing=4)

        self.title_label = Label(text="LingoLens AI - Public Translation Engine", size_hint=(1, 0.035), font_size=11, bold=True, color=(0.95, 0.95, 0.97, 1), **font_kwargs)
        root.add_widget(self.title_label)

        nav_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.045), spacing=4)
        self.lang_spinner = Spinner(
            text=self.selected_lang_name,
            values=list(WORLD_LANGUAGES.keys()),
            size_hint=(0.6, 1),
            background_color=(0.2, 0.25, 0.35, 1),
            **font_kwargs
        )
        self.lang_spinner.bind(text=self.on_language_select)
        nav_bar.add_widget(self.lang_spinner)
        
        gps_btn = Button(text="GPS Map Location", size_hint=(0.4, 1), background_normal='', background_color=(0.2, 0.6, 0.5, 1), on_press=self.open_gps_map, **font_kwargs)
        nav_bar.add_widget(gps_btn)
        root.add_widget(nav_bar)

        scroll = ScrollView(size_hint=(1, 0.35), bar_width=4)
        self.output_label = Label(text="System ready. Translation engine online...", font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.output_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)), texture_size=lambda s, t: setattr(s, 'height', max(t[1], 200)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        # მართვის პანელის ძირითადი ფუნქციური ღილაკები
        action_row = BoxLayout(orientation='horizontal', size_hint=(1, 0.05), spacing=6)
        action_row.add_widget(Button(text="Copy Text", background_normal='', background_color=(0.2, 0.3, 0.4, 1), on_press=self.copy_text, **font_kwargs))
        action_row.add_widget(Button(text="Share", background_normal='', background_color=(0.3, 0.2, 0.5, 1), on_press=self.share_text, **font_kwargs))
        action_row.add_widget(Button(text="Gallery", background_normal='', background_color=(0.6, 0.3, 0.2, 1), on_press=self.open_gallery, **font_kwargs))
        root.add_widget(action_row)

        input_container = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, 0.35))
        self.text_input = TextInput(hint_text="Type text to translate...", multiline=False, size_hint=(1, 0.4), padding=[10, 10, 10, 10], background_normal='', background_active='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs)
        input_container.add_widget(self.text_input)

        bottom_actions = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.55))
        bottom_actions.add_widget(Button(text="Send", size_hint=(0.33, 1), background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), on_press=self.send_message, **font_kwargs))
        bottom_actions.add_widget(Button(text="Camera / AR", size_hint=(0.33, 1), background_normal='', background_color=(0.15, 0.60, 0.45, 1), color=(1, 1, 1, 1), on_press=self.open_camera, **font_kwargs))
        bottom_actions.add_widget(Button(text="Audio TTS", size_hint=(0.34, 1), background_normal='', background_color=(0.20, 0.22, 0.28, 1), color=(1, 1, 1, 1), on_press=lambda x: self.speak_text(self.last_ai_text), **font_kwargs))

        input_container.add_widget(bottom_actions)
        root.add_widget(input_container)
        self.add_widget(root)

    def on_language_select(self, spinner, text):
        self.selected_lang_name = text
        self.target_lang_code = WORLD_LANGUAGES.get(text, "en")
        self.update_ui(f"Language changed to: {text}")

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def open_gps_map(self, instance):
        self.update_ui("Opening GPS map...")
        if ANDROID_PLYER_AVAILABLE:
            try:
                gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
                gps.start(minTime=1000, minDistance=1)
            except Exception:
                self.launch_map_intent(41.7151, 44.8271)
        else:
            self.launch_map_intent(41.7151, 44.8271)

    def on_gps_location(self, **kwargs):
        lat = kwargs.get('lat', 41.7151)
        lon = kwargs.get('lon', 44.8271)
        try:
            gps.stop()
        except:
            pass
        self.launch_map_intent(lat, lon)

    def on_gps_status(self, *args, **kwargs):
        pass

    def launch_map_intent(self, lat, lon):
        loc_msg = f"Location: {lat:.4f}, {lon:.4f}. Opening map..."
        self.last_ai_text = loc_msg
        self.update_ui(loc_msg)
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                uri = Uri.parse(f"geo:{lat},{lon}?q={lat},{lon}(My+Location)")
                intent = Intent(Intent.ACTION_VIEW, uri)
                activity.startActivity(intent)
            except Exception as e:
                print("Map intent error:", e)

    def copy_text(self, instance):
        if self.last_ai_text:
            Clipboard.copy(self.last_ai_text)
            self.update_ui("Copied to clipboard!")

    def share_text(self, instance):
        text_to_share = self.last_ai_text if self.last_ai_text else "LingoLens AI"
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, String(text_to_share))
                chooser = Intent.createChooser(intent, String("Share"))
                activity.startActivity(chooser)
            except Exception as e:
                self.update_ui(f"Share error: {str(e)}")
        else:
            Clipboard.copy(text_to_share)

    def open_gallery(self, instance):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("image/*")
                activity.startActivityForResult(intent, 1002)
                self.update_ui("Gallery opened. Select an image...")
            except Exception as e:
                self.update_ui(f"Gallery error: {str(e)}")
        else:
            self.update_ui("Gallery simulation: Processing image...")
            threading.Thread(target=lambda: self.translate_text("Hello from gallery image"), daemon=True).start()

    def open_camera(self, instance):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                activity.startActivityForResult(intent, 1003)
                self.update_ui("Camera opened. Capture text...")
            except Exception as e:
                self.update_ui(f"Camera error: {str(e)}")
        else:
            self.update_ui("Camera simulation: Extracting text via OCR...")
            threading.Thread(target=lambda: self.translate_text("Hello from camera capture"), daemon=True).start()

    def on_activity_result(self, requestCode, resultCode, intent):
        if resultCode == -1:
            if requestCode == 1002 and intent is not None:
                self.update_ui("Image selected from gallery. Translating...")
                prompt = f"Translate image content to {self.selected_lang_name}"
                threading.Thread(target=lambda: self.translate_text(prompt), daemon=True).start()
            elif requestCode == 1003:
                self.update_ui("Image captured. Translating...")
                prompt = f"Translate camera capture to {self.selected_lang_name}"
                threading.Thread(target=lambda: self.translate_text(prompt), daemon=True).start()

    def speak_text(self, text):
        if ANDROID_NATIVE_AVAILABLE and self.tts and text:
            try:
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print("TTS Error:", e)

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg: return
        self.text_input.text = ""
        self.chat_history.append(f"User: {msg}")
        self.update_ui(f"Translating to {self.selected_lang_name}...")
        
        threading.Thread(target=lambda: self.translate_text(msg), daemon=True).start()

    def translate_text(self, text_to_translate):
        translated = ""
        try:
            import urllib.request
            import urllib.parse
            import json as py_json
            
            lang_pair = f"ka|{self.target_lang_code}"
            encoded_text = urllib.parse.quote(text_to_translate)
            url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair={lang_pair}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context(cafile=certifi.where())
            
            with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
                raw_bytes = response.read()
                res_body = raw_bytes.decode('utf-8', errors='replace')
                res_data = py_json.loads(res_body)
                
                if "responseData" in res_data and "translatedText" in res_data["responseData"]:
                    result = res_data["responseData"]["translatedText"].strip()
                    if result and not "MYMEMORY WARNING" in result.upper():
                        translated = result
        except Exception as err:
            print("Translation API error:", err)

        if not translated:
            translated = f"({self.selected_lang_name}): {text_to_translate}"

        self.last_ai_text = translated
        self.chat_history.append(f"Translation ({self.selected_lang_name}): {translated}")
        self.update_ui("\n\n".join(self.chat_history[-6:]))
        self.speak_text(translated)


class LingoLensApp(App):
    def build(self, **kwargs):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        
        Window.bind(on_keyboard=self.on_keyboard)
        return sm

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            if self.root.current != 'main':
                self.root.current = 'main'
                return True
            else:
                App.get_running_app().stop()
                return True
        return False

if __name__ == '__main__':
    LingoLensApp().run()
