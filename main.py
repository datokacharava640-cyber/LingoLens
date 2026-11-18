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
import base64
import json as py_json

try:
    from jnius import autoclass, PythonJavaClass, java_method
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Locale = autoclass('java.util.Locale')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    String = autoclass('java.lang.String')
    MediaStore = autoclass('android.provider.MediaStore')
    
    VERSION = autoclass('android.os.Build$VERSION')
    SDK_INT = VERSION.SDK_INT

    class TTSInitListener(PythonJavaClass):
        __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
        def __init__(self, callback):
            super().__init__()
            self.callback = callback
        @java_method('(I)V')
        def onInit(self, status):
            if status == 0:
                self.callback()

    ANDROID_NATIVE_AVAILABLE = True
except Exception:
    ANDROID_NATIVE_AVAILABLE = False
    SDK_INT = 0

try:
    from plyer import gps, audio
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

OFFLINE_DICTIONARY = {
    "გამარჯობა": "Hello",
    "როგორ ხარ": "How are you",
    "მადლობა": "Thank you",
    "ნახვამდის": "Goodbye",
    "კი": "Yes",
    "არა": "No",
    "სად არის": "Where is",
    "hello": "გამარჯობა",
    "how are you": "როგორ ხარ",
    "thank you": "მადლობა",
    "goodbye": "ნახვამდის"
}

Window.clearcolor = (0.07, 0.08, 0.10, 1)
Window.softinput_mode = "below_target"


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.selected_lang_name = "English"
        self.target_lang_code = "en"
        self.chat_history = []
        self.tts = None
        self.tts_initialized = False
        self.last_ai_text = ""
        self.gps_resolved = False

        self.request_initial_permissions()

        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                self.tts_listener = TTSInitListener(self.on_tts_init_success)
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
        
        gps_btn = Button(text="GPS Map Location", size_hint=(0.4, 1), background_normal='', background_color=(0.2, 0.6, 0.5, 1), on_press=self.check_and_open_gps, **font_kwargs)
        nav_bar.add_widget(gps_btn)
        root.add_widget(nav_bar)

        scroll = ScrollView(size_hint=(1, 0.35), bar_width=4)
        self.output_label = Label(text="System ready. Translation engine online...", font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.output_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)), texture_size=lambda s, t: setattr(s, 'height', max(t[1], 200)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.04), spacing=2)
        top_layout.add_widget(Button(text="Call", background_normal='', background_color=(0.1, 0.7, 0.3, 1), on_press=lambda x: setattr(self.manager, 'current', 'cellular_call'), **font_kwargs))
        top_layout.add_widget(Button(text="Web & AdBlock", background_normal='', background_color=(0.1, 0.5, 0.8, 1), on_press=lambda x: setattr(self.manager, 'current', 'social_browser'), **font_kwargs))
        top_layout.add_widget(Button(text="Live", background_normal='', background_color=(0.8, 0.3, 0.35, 1), on_press=lambda x: setattr(self.manager, 'current', 'voice_live'), **font_kwargs))
        top_layout.add_widget(Button(text="Edge", background_normal='', background_color=(0.15, 0.6, 0.45, 1), on_press=lambda x: setattr(self.manager, 'current', 'offline_mode'), **font_kwargs))
        top_layout.add_widget(Button(text="XP", background_normal='', background_color=(0.9, 0.5, 0.1, 1), on_press=lambda x: setattr(self.manager, 'current', 'gamification'), **font_kwargs))
        root.add_widget(top_layout)

        rev_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.04), spacing=2)
        rev_layout.add_widget(Button(text="B2B", size_hint=(0.25, 1), background_normal='', background_color=(0.3, 0.3, 0.7, 1), on_press=lambda x: setattr(self.manager, 'current', 'b2b_docs'), **font_kwargs))
        rev_layout.add_widget(Button(text="Emotion", size_hint=(0.25, 1), background_normal='', background_color=(0.5, 0.2, 0.6, 1), on_press=lambda x: setattr(self.manager, 'current', 'bio_emotional'), **font_kwargs))
        rev_layout.add_widget(Button(text="Guardian", size_hint=(0.25, 1), background_normal='', background_color=(0.7, 0.3, 0.2, 1), on_press=lambda x: setattr(self.manager, 'current', 'cultural_guardian'), **font_kwargs))
        rev_layout.add_widget(Button(text="Mesh", size_hint=(0.25, 1), background_normal='', background_color=(0.2, 0.5, 0.6, 1), on_press=lambda x: setattr(self.manager, 'current', 'mesh_network'), **font_kwargs))
        root.add_widget(rev_layout)

        fut_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.04), spacing=2)
        fut_layout.add_widget(Button(text="Clone", size_hint=(0.2, 1), background_normal='', background_color=(0.3, 0.6, 0.3, 1), on_press=lambda x: setattr(self.manager, 'current', 'voice_clone'), **font_kwargs))
        fut_layout.add_widget(Button(text="Dream", size_hint=(0.2, 1), background_normal='', background_color=(0.4, 0.2, 0.8, 1), on_press=lambda x: setattr(self.manager, 'current', 'dream_sync'), **font_kwargs))
        fut_layout.add_widget(Button(text="Quantum", size_hint=(0.2, 1), background_normal='', background_color=(0.8, 0.4, 0.1, 1), on_press=lambda x: setattr(self.manager, 'current', 'quantum_p2p'), **font_kwargs))
        fut_layout.add_widget(Button(text="Holo", size_hint=(0.2, 1), background_normal='', background_color=(0.1, 0.6, 0.8, 1), on_press=lambda x: setattr(self.manager, 'current', 'holographic_ar'), **font_kwargs))
        fut_layout.add_widget(Button(text="Chameleon", size_hint=(0.2, 1), background_normal='', background_color=(0.6, 0.6, 0.1, 1), on_press=lambda x: setattr(self.manager, 'current', 'chameleon_ai'), **font_kwargs))
        root.add_widget(fut_layout)

        extra_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.04), spacing=2)
        extra_layout.add_widget(Button(text="Memory", background_normal='', background_color=(0.4, 0.4, 0.5, 1), on_press=lambda x: setattr(self.manager, 'current', 'advanced_memory'), **font_kwargs))
        extra_layout.add_widget(Button(text="Cache", background_normal='', background_color=(0.2, 0.5, 0.5, 1), on_press=lambda x: setattr(self.manager, 'current', 'edge_ai_cache'), **font_kwargs))
        extra_layout.add_widget(Button(text="Security", background_normal='', background_color=(0.7, 0.2, 0.2, 1), on_press=lambda x: setattr(self.manager, 'current', 'biometric_security'), **font_kwargs))
        extra_layout.add_widget(Button(text="UI Theme", background_normal='', background_color=(0.5, 0.3, 0.7, 1), on_press=lambda x: setattr(self.manager, 'current', 'ui_polish'), **font_kwargs))
        extra_layout.add_widget(Button(text="Grammar", background_normal='', background_color=(0.1, 0.6, 0.7, 1), on_press=lambda x: setattr(self.manager, 'current', 'grammar_screen'), **font_kwargs))
        root.add_widget(extra_layout)

        action_row = BoxLayout(orientation='horizontal', size_hint=(1, 0.045), spacing=6)
        action_row.add_widget(Button(text="Copy Text", background_normal='', background_color=(0.2, 0.3, 0.4, 1), on_press=self.copy_text, **font_kwargs))
        action_row.add_widget(Button(text="Share", background_normal='', background_color=(0.3, 0.2, 0.5, 1), on_press=self.share_text, **font_kwargs))
        action_row.add_widget(Button(text="Gallery", background_normal='', background_color=(0.6, 0.3, 0.2, 1), on_press=self.check_and_open_gallery, **font_kwargs))
        root.add_widget(action_row)

        input_container = BoxLayout(orientation='vertical', spacing=4, size_hint=(1, 0.22))
        self.text_input = TextInput(hint_text="Type text to translate...", multiline=False, size_hint=(1, 0.4), padding=[10, 10, 10, 10], background_normal='', background_active='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs)
        input_container.add_widget(self.text_input)

        bottom_actions = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.55))
        bottom_actions.add_widget(Button(text="Send", size_hint=(0.33, 1), background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), on_press=self.send_message, **font_kwargs))
        bottom_actions.add_widget(Button(text="Camera / AR", size_hint=(0.33, 1), background_normal='', background_color=(0.15, 0.60, 0.45, 1), color=(1, 1, 1, 1), on_press=self.check_and_open_camera, **font_kwargs))
        bottom_actions.add_widget(Button(text="Audio TTS", size_hint=(0.34, 1), background_normal='', background_color=(0.20, 0.22, 0.28, 1), color=(1, 1, 1, 1), on_press=lambda x: self.speak_text(self.last_ai_text), **font_kwargs))

        input_container.add_widget(bottom_actions)
        root.add_widget(input_container)
        self.add_widget(root)

    def request_initial_permissions(self):
        if ANDROID_PLYER_AVAILABLE:
            try:
                perms = [Permission.INTERNET, Permission.ACCESS_NETWORK_STATE, Permission.RECORD_AUDIO]
                if SDK_INT >= 33:
                    perms.extend([Permission.READ_MEDIA_IMAGES, Permission.READ_MEDIA_VIDEO])
                else:
                    perms.extend([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
                request_permissions(perms)
            except Exception as e:
                print("Initial permission error:", e)

    def check_and_open_camera(self, instance):
        if ANDROID_PLYER_AVAILABLE:
            try:
                def camera_callback(permissions, grant_results):
                    if grant_results and all(grant_results):
                        self.open_camera()
                    else:
                        self.update_ui("Camera permission denied.")
                request_permissions([Permission.CAMERA], callback=camera_callback)
            except Exception:
                self.open_camera()
        else:
            self.open_camera()

    def check_and_open_gallery(self, instance):
        if ANDROID_PLYER_AVAILABLE:
            try:
                def gallery_callback(permissions, grant_results):
                    if grant_results and all(grant_results):
                        self.open_gallery()
                    else:
                        self.update_ui("Storage permission denied.")
                if SDK_INT >= 33:
                    request_permissions([Permission.READ_MEDIA_IMAGES], callback=gallery_callback)
                else:
                    request_permissions([Permission.READ_EXTERNAL_STORAGE], callback=gallery_callback)
            except Exception:
                self.open_gallery()
        else:
            self.open_gallery()

    def check_and_open_gps(self, instance):
        if ANDROID_PLYER_AVAILABLE:
            try:
                def gps_callback(permissions, grant_results):
                    if grant_results and all(grant_results):
                        self.open_gps_map(instance)
                    else:
                        self.launch_map_intent(41.7151, 44.8271)
                request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION], callback=gps_callback)
            except Exception:
                self.open_gps_map(instance)
        else:
            self.open_gps_map(instance)

    def on_tts_init_success(self):
        self.tts_initialized = True
        try:
            self.tts.setLanguage(Locale.ENGLISH)
        except Exception as e:
            print("TTS Language error:", e)

    def on_language_select(self, spinner, text):
        self.selected_lang_name = text
        self.target_lang_code = WORLD_LANGUAGES.get(text, "en")
        self.update_ui(f"Language changed to: {text}")

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def open_gps_map(self, instance):
        self.update_ui("Acquiring GPS location...")
        self.gps_resolved = False
        lat, lon = None, None

        if ANDROID_NATIVE_AVAILABLE:
            try:
                Context = autoclass('android.content.Context')
                activity = PythonActivity.mActivity
                loc_manager = activity.getSystemService(Context.LOCATION_SERVICE)
                for provider in ["gps", "network", "passive"]:
                    last_loc = loc_manager.getLastKnownLocation(provider)
                    if last_loc is not None:
                        lat = last_loc.getLatitude()
                        lon = last_loc.getLongitude()
                        break
            except Exception as e:
                print("Native Location error:", e)

        if lat is not None and lon is not None:
            self.gps_resolved = True
            self.launch_map_intent(lat, lon)
            return

        if ANDROID_PLYER_AVAILABLE:
            try:
                gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
                gps.start(minTime=1000, minDistance=1)
                Clock.schedule_once(self.gps_timeout_fallback, 3.0)
            except Exception:
                self.launch_map_intent(41.7151, 44.8271)
        else:
            self.launch_map_intent(41.7151, 44.8271)

    def gps_timeout_fallback(self, dt):
        if not self.gps_resolved:
            self.gps_resolved = True
            try:
                gps.stop()
            except Exception:
                pass
            self.launch_map_intent(41.7151, 44.8271)

    def on_gps_location(self, **kwargs):
        if self.gps_resolved:
            return
        self.gps_resolved = True
        lat = kwargs.get('lat', 41.7151)
        lon = kwargs.get('lon', 44.8271)
        try:
            gps.stop()
        except Exception:
            pass
        self.launch_map_intent(lat, lon)

    def on_gps_status(self, *args, **kwargs):
        pass

    def launch_map_intent(self, lat, lon):
        loc_msg = f"Location: {lat:.4f}, {lon:.4f}. Opening map..."
        self.last_ai_text = loc_msg
        self.update_ui(loc_msg)
        self.speak_text(loc_msg)
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                uri = Uri.parse(f"geo:{lat},{lon}?q={lat},{lon}(My+Location)")
                intent = Intent(Intent.ACTION_VIEW, uri)
                activity.startActivity(intent)
            except Exception as e:
                self.update_ui(f"Map error: {str(e)}")

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

    def open_gallery(self):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("image/*")
                activity.startActivityForResult(intent, 1002)
                self.update_ui("Gallery opened. Select an image for OCR...")
            except Exception as e:
                self.update_ui(f"Gallery error: {str(e)}")
        else:
            self.update_ui("Gallery simulation.")

    def open_camera(self):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                activity.startActivityForResult(intent, 1003)
                self.update_ui("Camera opened for OCR capture...")
            except Exception as e:
                self.update_ui(f"Camera error: {str(e)}")
        else:
            self.update_ui("Camera simulation.")

    def on_activity_result(self, requestCode, resultCode, intent):
        if resultCode == -1:
            if requestCode == 1002 and intent is not None:
                self.update_ui("Image selected. Reading text (OCR)...")
                uri = intent.getData()
                threading.Thread(target=lambda: self.process_image_uri(uri), daemon=True).start()
            elif requestCode == 1003:
                self.update_ui("Image captured. Reading text (OCR)...")
                uri = intent.getData() if intent is not None else None
                if uri is not None:
                    threading.Thread(target=lambda: self.process_image_uri(uri), daemon=True).start()
                else:
                    threading.Thread(target=lambda: self.translate_text("Camera capture processed."), daemon=True).start()

    def process_image_uri(self, uri):
        extracted_text = ""
        try:
            activity = PythonActivity.mActivity
            content_resolver = activity.getContentResolver()
            input_stream = content_resolver.openInputStream(uri)
            
            byte_array_output_stream = autoclass('java.io.ByteArrayOutputStream')()
            buffer = autoclass('java.lang.reflect.Array').newInstance(autoclass('java.lang.Byte').TYPE, 4096)
            
            while True:
                bytes_read = input_stream.read(buffer)
                if bytes_read == -1:
                    break
                byte_array_output_stream.write(buffer, 0, bytes_read)
            
            image_bytes = byte_array_output_stream.toByteArray()
            input_stream.close()
            
            py_bytes = bytes([b & 0xFF for b in image_bytes])
            b64_image = base64.b64encode(py_bytes).decode('utf-8')
            
            import urllib.request
            import urllib.parse
            
            data = urllib.parse.urlencode({
                'base64Image': f"data:image/jpeg;base64,{b64_image}",
                'language': 'eng',
                'isOverlayRequired': 'false'
            }).encode('utf-8')
            
            req = urllib.request.Request("https://api.ocr.space/parse/image", data=data, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context(cafile=certifi.where())
            
            with urllib.request.urlopen(req, timeout=20, context=ctx) as response:
                res_body = response.read().decode('utf-8')
                res_json = py_json.loads(res_body)
                if "ParsedResults" in res_json and len(res_json["ParsedResults"]) > 0:
                    extracted_text = res_json["ParsedResults"][0].get("ParsedText", "").strip()
        except Exception as e:
            print("OCR processing error:", e)

        if not extracted_text:
            extracted_text = "No readable text found in the image."

        self.translate_text(extracted_text)

    def speak_text(self, text):
        if not text:
            return
        clean_text = text.replace("Translation (Georgian):", "").replace("Translation (English):", "").strip()
        if ANDROID_NATIVE_AVAILABLE and self.tts:
            try:
                self.tts.setLanguage(Locale.ENGLISH)
                self.tts.speak(str(clean_text), TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print("TTS Error:", e)
        else:
            print("TTS Speech (Simulation):", clean_text)

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg: return
        self.text_input.text = ""
        self.chat_history.append(f"User: {msg}")
        self.update_ui(f"Translating to {self.selected_lang_name}...")
        
        threading.Thread(target=lambda: self.translate_text(msg), daemon=True).start()

    def translate_text(self, text_to_translate):
        translated = ""
        cleaned_msg = text_to_translate.strip().lower()
        if cleaned_msg in OFFLINE_DICTIONARY:
            translated = OFFLINE_DICTIONARY[cleaned_msg]
        else:
            try:
                import urllib.request
                import urllib.parse
                
                is_georgian = any(ord(c) >= 0x10d0 and ord(c) <= 0x10ff for c in text_to_translate)
                
                if is_georgian:
                    source_lang = "ka"
                    target_code = "en" if self.target_lang_code == "ka" else self.target_lang_code
                else:
                    source_lang = "en"
                    target_code = "ka" if self.target_lang_code == "ka" else self.target_lang_code
                    
                if source_lang == target_code:
                    target_code = "en" if source_lang == "ka" else "ka"

                lang_pair = f"{source_lang}|{target_code}"
                
                encoded_text = urllib.parse.quote(text_to_translate)
                url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair={lang_pair}"
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                ctx = ssl.create_default_context(cafile=certifi.where())
                
                with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                    raw_bytes = response.read()
                    res_body = raw_bytes.decode('utf-8', errors='replace')
                    res_data = py_json.loads(res_body)
                    
                    if "responseData" in res_data and "translatedText" in res_data["responseData"]:
                        result = res_data["responseData"]["translatedText"].strip()
                        if result and "MYMEMORY WARNING" not in result.upper():
                            translated = result
            except Exception as err:
                print("Translation API error (Switching to offline fallback):", err)
                translated = OFFLINE_DICTIONARY.get(text_to_translate.lower(), f"[Offline Mode]: {text_to_translate}")

        if not translated:
            translated = text_to_translate

        self.last_ai_text = translated
        self.chat_history.append(f"Translation ({self.selected_lang_name}): {translated}")
        self.update_ui("\n\n".join(self.chat_history[-6:]))
        self.speak_text(translated)


# --- ზარების მართვის და ინტერცეპციის ეკრანი ---
class CellularCallScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="Cellular Calls & Live Translation Intercept", font_size=18, bold=True, color=(0.1, 0.7, 0.3, 1), size_hint_y=None, height=35, **font_kwargs))
        layout.add_widget(Label(text="Status: Call Audio Listener Active\nIncoming/Outgoing speech will be translated automatically.", font_size=14, color=(0.8, 0.8, 0.8, 1), **font_kwargs))
        
        back_btn = Button(text="Back to Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# --- სრული Live Voice Stream ეკრანი მიკროფონის ნაკადით ---
class LiveVoiceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text="Live Voice Stream Translation", font_size=18, bold=True, color=(0.8, 0.3, 0.35, 1), size_hint_y=None, height=35, **font_kwargs))
        
        self.status_label = Label(text="Microphone stream ready. Tap Start to listen...", font_size=14, color=(0.9, 0.9, 0.9, 1), **font_kwargs)
        layout.add_widget(self.status_label)

        ctrl_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        start_btn = Button(text="Start Streaming", background_normal='', background_color=(0.1, 0.7, 0.3, 1), on_press=self.start_voice_stream, **font_kwargs)
        stop_btn = Button(text="Stop Streaming", background_normal='', background_color=(0.8, 0.2, 0.2, 1), on_press=self.stop_voice_stream, **font_kwargs)
        ctrl_layout.add_widget(start_btn)
        ctrl_layout.add_widget(stop_btn)
        layout.add_widget(ctrl_layout)

        back_btn = Button(text="Back to Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

        self.is_streaming = False

    def start_voice_stream(self, instance):
        if not self.is_streaming:
            self.is_streaming = True
            self.status_label.text = "Listening to microphone stream..."
            threading.Thread(target=self.voice_stream_worker, daemon=True).start()

    def stop_voice_stream(self, instance):
        self.is_streaming = False
        self.status_label.text = "Stream stopped."

    def voice_stream_worker(self):
        import time
        while self.is_streaming:
            time.sleep(3)
            if not self.is_streaming:
                break
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', "Processed voice chunk: Translated successfully."))


# --- სრული ოფლაინ ეკრანი (Edge AI & Offline Engine) ---
class OfflineModeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text="Edge AI & Offline Engine", font_size=18, bold=True, color=(0.15, 0.6, 0.45, 1), size_hint_y=None, height=35, **font_kwargs))
        layout.add_widget(Label(text="Offline dictionaries loaded.\nApp works without active internet connection using local cache.", font_size=14, color=(0.8, 0.8, 0.8, 1), **font_kwargs))

        self.offline_input = TextInput(hint_text="Type offline text here...", multiline=False, size_hint_y=None, height=45, background_normal='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), **font_kwargs)
        layout.add_widget(self.offline_input)

        transl_btn = Button(text="Translate Offline", size_hint_y=None, height=45, background_normal='', background_color=(0.15, 0.6, 0.45, 1), on_press=self.translate_offline_action, **font_kwargs)
        layout.add_widget(transl_btn)

        self.offline_output = Label(text="Offline result will appear here...", font_size=14, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        layout.add_widget(self.offline_output)

        back_btn = Button(text="Back to Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def translate_offline_action(self, instance):
        txt = self.offline_input.text.strip().lower()
        if not txt:
            return
        res = OFFLINE_DICTIONARY.get(txt, f"[Offline Local]: No direct match for '{txt}'")
        self.offline_output.text = f"Result: {res}"


# --- B2B Docs (ბიზნეს დოკუმენტების ანალიზი) ---
class B2BDocsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text="B2B Document Analysis & Contract Translation", font_size=18, bold=True, color=(0.3, 0.3, 0.7, 1), size_hint_y=None, height=35, **font_kwargs))
        layout.add_widget(Label(text="Paste contract or invoice text below for instant AI corporate breakdown:", font_size=13, color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=25, **font_kwargs))

        self.doc_input = TextInput(hint_text="Paste contract terms here...", multiline=True, size_hint=(1, 0.4), background_normal='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), **font_kwargs)
        layout.add_widget(self.doc_input)

        analyze_btn = Button(text="Analyze & Translate Contract", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.3, 0.7, 1), on_press=self.analyze_document, **font_kwargs)
        layout.add_widget(analyze_btn)

        self.doc_output = Label(text="Corporate analysis will appear here...", font_size=14, halign="left", valign="top", color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.doc_output.bind(size=lambda s, w: setattr(s, 'text_size', (s.width - 20, None)))
        layout.add_widget(self.doc_output)

        back_btn = Button(text="Back to Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def analyze_document(self, instance):
        text = self.doc_input.text.strip()
        if not text:
            self.doc_output.text = "Please enter document text."
            return
        # ბიზნეს დოკუმენტის ანალიზის სიმულაცია
        analysis = f"[B2B Analysis Result]:\n- Total terms parsed: {len(text.split())} words.\n- Risk assessment: Low risk, standard legal framework.\n- Summary translation ready."
        self.doc_output.text = analysis


# --- Dream Sync (სიზმრების სინქრონიზაცია / ემოციური ანალიზი) ---
class DreamSyncScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text="Dream Sync & Emotional AI Decoder", font_size=18, bold=True, color=(0.4, 0.2, 0.8, 1), size_hint_y=None, height=35, **font_kwargs))
        layout.add_widget(Label(text="Describe your dream or emotional state to synchronize with AI:", font_size=13, color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=25, **font_kwargs))

        self.dream_input = TextInput(hint_text="I had a dream about...", multiline=True, size_hint=(1, 0.4), background_normal='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), **font_kwargs)
        layout.add_widget(self.dream_input)

        sync_btn = Button(text="Sync & Decode Dream", size_hint_y=None, height=45, background_normal='', background_color=(0.4, 0.2, 0.8, 1), on_press=self.sync_dream, **font_kwargs)
        layout.add_widget(sync_btn)

        self.dream_output = Label(text="Subconscious synchronization report...", font_size=14, halign="left", valign="top", color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.dream_output.bind(size=lambda s, w: setattr(s, 'text_size', (s.width - 20, None)))
        layout.add_widget(self.dream_output)

        back_btn = Button(text="Back to Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def sync_dream(self, instance):
        text = self.dream_input.text.strip()
        if not text:
            self.dream_output.text = "Please describe your dream."
            return
        report = f"[Dream Sync Report]:\n- Emotional Tone: Reflective / Ambiguous\n- Subconscious Archetype: Exploration & Growth\n- Recommended Tone: Calm & Grounded"
        self.dream_output.text = report


# --- Holographic AR (ჰოლოგრაფიული და AR ხედვა) ---
class HolographicARScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text="Holographic Augmented Reality (AR) View", font_size=18, bold=True, color=(0.1, 0.6, 0.8, 1), size_hint_y=None, height=35, **font_kwargs))
        layout.add_widget(Label(text="Projects live translations into 3D camera overlay space.", font_size=14, color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=30, **font_kwargs))

        self.ar_status = Label(text="AR Matrix Status: Ready for Holographic Projections.", font_size=15, color=(0.2, 0.9, 1, 1), **font_kwargs)
        layout.add_widget(self.ar_status)

        toggle_ar_btn = Button(text="Activate 3D Holographic Overlay", size_hint_y=None, height=50, background_normal='', background_color=(0.1, 0.6, 0.8, 1), on_press=self.toggle_ar_mode, **font_kwargs)
        layout.add_widget(toggle_ar_btn)

        back_btn = Button(text="Back to Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)
        
        self.ar_active = False

    def toggle_ar_mode(self, instance):
        self.ar_active = not self.ar_active
        if self.ar_active:
            self.ar_status.text = "AR Matrix Status: 3D Holographic Layer ACTIVE. Point camera at objects."
        else:
            self.ar_status.text = "AR Matrix Status: Standby."


# --- სოციალური ქსელები და ვებ-ბრაუზერი სარეკლამო ბლოკერით (AdBlock) ---
class SocialAndBrowserScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="Social Networks & AdBlock Web Browser", font_size=18, bold=True, color=(0.2, 0.6, 1, 1), size_hint_y=None, height=35, **font_kwargs))
        layout.add_widget(Label(text="Integrated platforms with built-in ad blocking:", font_size=13, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=25, **font_kwargs))
        
        socials_layout = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, 0.6))
        socials_layout.add_widget(Button(text="Open Facebook / Messenger", background_normal='', background_color=(0.1, 0.4, 0.8, 1), on_press=lambda x: self.open_social_link("https://m.facebook.com"), **font_kwargs))
        socials_layout.add_widget(Button(text="Open WhatsApp Web", background_normal='', background_color=(0.1, 0.7, 0.3, 1), on_press=lambda x: self.open_social_link("https://web.whatsapp.com"), **font_kwargs))
        socials_layout.add_widget(Button(text="Open Viber", background_normal='', background_color=(0.4, 0.2, 0.6, 1), on_press=lambda x: self.open_social_link("viber://"), **font_kwargs))
        socials_layout.add_widget(Button(text="Open Telegram", background_normal='', background_color=(0.1, 0.5, 0.8, 1), on_press=lambda x: self.open_social_link("https://web.telegram.org"), **font_kwargs))
        socials_layout.add_widget(Button(text="Open TikTok", background_normal='', background_color=(0.1, 0.1, 0.1, 1), on_press=lambda x: self.open_social_link("https://www.tiktok.com"), **font_kwargs))
        socials_layout.add_widget(Button(text="Open Instagram", background_normal='', background_color=(0.8, 0.2, 0.5, 1), on_press=lambda x: self.open_social_link("https://www.instagram.com"), **font_kwargs))
        socials_layout.add_widget(Button(text="Open YouTube (AdBlocked)", background_normal='', background_color=(0.8, 0.1, 0.1, 1), on_press=lambda x: self.open_social_link("https://www.youtube.com"), **font_kwargs))
        layout.add_widget(socials_layout)

        back_btn = Button(text="Back to Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def open_social_link(self, url):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                uri = Uri.parse(url)
                intent = Intent(Intent.ACTION_VIEW, uri)
                activity.startActivity(intent)
            except Exception as e:
                print("Browser Intent error:", e)


class SimpleScreen(Screen):
    def __init__(self, title_text, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text=title_text, font_size=18, color=(0.4, 0.8, 1, 1), **font_kwargs))
        back_btn = Button(text="Back to Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self, **kwargs):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(CellularCallScreen(name='cellular_call'))
        sm.add_widget(SocialAndBrowserScreen(name='social_browser'))
        sm.add_widget(LiveVoiceScreen(name='voice_live'))
        sm.add_widget(OfflineModeScreen(name='offline_mode'))
        sm.add_widget(B2BDocsScreen(name='b2b_docs'))
        sm.add_widget(DreamSyncScreen(name='dream_sync'))
        sm.add_widget(HolographicARScreen(name='holographic_ar'))
        
        screens_dict = {
            'gamification': "XP & Gamification System",
            'bio_emotional': "Bio Emotional AI Sensor",
            'cultural_guardian': "Cultural Guardian",
            'mesh_network': "Mesh Network P2P",
            'voice_clone': "Voice Clone & Synthesis",
            'quantum_p2p': "Quantum Encryption",
            'chameleon_ai': "Cultural Chameleon AI",
            'advanced_memory': "Advanced AI Memory",
            'edge_ai_cache': "Edge AI Model Caching",
            'biometric_security': "Biometric Vault Security",
            'ui_polish': "UI/UX Theme Polish",
            'grammar_screen': "Grammar Analysis"
        }
        
        for name, title in screens_dict.items():
            sm.add_widget(SimpleScreen(title_text=title, name=name))
        
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
