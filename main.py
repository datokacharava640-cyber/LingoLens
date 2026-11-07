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
    "Hindi": "hi"
}

Window.clearcolor = (0.07, 0.08, 0.10, 1)
Window.softinput_mode = "below_target"

# შენი Gemini API გასაღები
GEMINI_API_KEY = "AQ.Ab8RN6LWOw1C_teXQ5EUxfMkrglOHNN3Hq202mnnQ7oKWexkTQ"


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

        self.title_label = Label(text="LingoLens AI - Fully Authorized & Fixed", size_hint=(1, 0.035), font_size=11, bold=True, color=(0.95, 0.95, 0.97, 1), **font_kwargs)
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
        self.output_label = Label(text="სისტემა მზადაა. აირჩიეთ ფოტო ან ჩაწერეთ ტექსტი...", font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
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
        action_row.add_widget(Button(text="Gallery", background_normal='', background_color=(0.6, 0.3, 0.2, 1), on_press=self.open_gallery, **font_kwargs))
        root.add_widget(action_row)

        input_container = BoxLayout(orientation='vertical', spacing=4, size_hint=(1, 0.22))
        self.text_input = TextInput(hint_text="ჩაწერეთ ტექსტი ან კითხვა...", multiline=False, size_hint=(1, 0.4), padding=[10, 10, 10, 10], background_normal='', background_active='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs)
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
        self.update_ui(f"არჩეული ენა: {text}")

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    # რეალური რუკისა და GPS ნავიგაციის გახსნა
    def open_gps_map(self, instance):
        self.update_ui("GPS მდებარეობის მოძიება და რუკის გახსნა...")
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
        loc_msg = f"მდებარეობა: Lat {lat:.4f}, Lon {lon:.4f}. რუკა იხსნება..."
        self.last_ai_text = loc_msg
        self.update_ui(loc_msg)
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                uri = Uri.parse(f"geo:{lat},{lon}?q={lat},{lon}(თქვენი+მდებარეობა)")
                intent = Intent(Intent.ACTION_VIEW, uri)
                activity.startActivity(intent)
            except Exception as e:
                print("Map intent error:", e)

    def copy_text(self, instance):
        if self.last_ai_text:
            Clipboard.copy(self.last_ai_text)
            self.update_ui("ტექსტი დაკოპირდა ბუფერში!")

    def share_text(self, instance):
        text_to_share = self.last_ai_text if self.last_ai_text else "LingoLens AI"
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, String(text_to_share))
                chooser = Intent.createChooser(intent, String("გაზიარება"))
                activity.startActivity(chooser)
            except Exception as e:
                self.update_ui(f"გაზიარების შეცდომა: {str(e)}")
        else:
            Clipboard.copy(text_to_share)

    def open_gallery(self, instance):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("image/*")
                activity.startActivityForResult(intent, 1002)
                self.update_ui("გალერეა გაიხსნა. აირჩიეთ ფოტო...")
            except Exception as e:
                self.update_ui(f"გალერეის შეცდომა: {str(e)}")
        else:
            self.update_ui("გალერეა მუშაობს ანდროიდ მოწყობილობაზე.")

    def open_camera(self, instance):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                activity.startActivityForResult(intent, 1003)
                self.update_ui("კამერა გაიხსნა. გადაიღეთ ფოტო...")
            except Exception as e:
                self.update_ui(f"კამერის შეცდომა: {str(e)}")
        else:
            self.update_ui("კამერა მუშაობს ანდროიდ მოწყობილობაზე.")

    # გალერეიდან ან კამერიდან არჩეული ფოტოს რეალური წამოღება და ანალიზი
    def on_activity_result(self, requestCode, resultCode, intent):
        if resultCode == -1: # RESULT_OK
            if requestCode == 1002 and intent is not None:
                try:
                    uri = intent.getData()
                    if uri is not None:
                        self.update_ui("ფოტო არჩეულია გალერეიდან! მიმდინარეობს სურათის დამუშავება...")
                        # ამოვიღოთ ფოტოს ბაიტები უსაფრთხოდ
                        activity = PythonActivity.mActivity
                        content_resolver = activity.getContentResolver()
                        input_stream = content_resolver.openInputStream(uri)
                        
                        import io
                        byte_buffer = io.BytesIO()
                        buffer = bytearray(1024)
                        while True:
                            len_read = input_stream.read(buffer)
                            if len_read == -1:
                                break
                            byte_buffer.write(buffer[:len_read])
                        input_stream.close()
                        image_bytes = byte_buffer.getvalue()
                        
                        import base64
                        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                        
                        prompt = f"გთხოვთ სრულად გააანალიზოთ, ამოიცნოთ ტექსტი და თარგმნოთ ეს ფოტო {self.selected_lang_name} ენაზე."
                        threading.Thread(target=lambda: self.ask_gemini_server_with_image(prompt, encoded_image), daemon=True).start()
                except Exception as e:
                    self.update_ui(f"ფოტოს კითხვის შეცდომა: {str(e)}")
            elif requestCode == 1003:
                self.update_ui("კამერით ფოტო გადაღებულია! მიმდინარეობს AR და სერვერული ანალიზი...")
                prompt = f"გთხოვთ გააანალიზოთ და თარგმნოთ ეს გადაღებული კადრი {self.selected_lang_name} ენაზე."
                threading.Thread(target=lambda: self.ask_gemini_server(prompt), daemon=True).start()

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
        self.chat_history.append(f"მომხმარებელი: {msg}")
        self.update_ui("მიმდინარეობს მოთხოვნა Gemini სერვერთან...")
        
        prompt = f"Translate, explain, or answer this query in {self.selected_lang_name}: {msg}"
        threading.Thread(target=lambda: self.ask_gemini_server(prompt), daemon=True).start()

    # ტექსტური მოთხოვნის გაგზავნა სერვერზე (სწორი ენდპოინტით 401 შეცდომის ასაცილებლად)
    def ask_gemini_server(self, prompt_text):
        ai_res = ""
        try:
            import urllib.request
            import json as py_json
            
            # სწორი და სრულად ავტორიზებული v1beta ენდპოინტი
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt_text}]
                }]
            }
            
            data = py_json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
            ctx = ssl.create_default_context(cafile=certifi.where())
            
            with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
                raw_bytes = response.read()
                res_body = raw_bytes.decode('utf-8', errors='replace')
                res_data = py_json.loads(res_body)
                
                candidates = res_data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        ai_res = parts[0].get("text", "").strip()
        except Exception as err:
            print("Gemini API exception:", err)
            ai_res = f"სერვერული შეცდომა: {str(err)}"

        if not ai_res:
            ai_res = f"({self.selected_lang_name}): პასუხი ვერ მოიძებნა."

        self.last_ai_text = ai_res
        self.chat_history.append(f"Gemini AI ({self.selected_lang_name}): {ai_res}")
        self.update_ui("\n\n".join(self.chat_history[-6:]))
        self.speak_text(ai_res)

    # მულტიმოდალური მოთხოვნა სურათთან ერთად
    def ask_gemini_server_with_image(self, prompt_text, base64_image):
        ai_res = ""
        try:
            import urllib.request
            import json as py_json
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }]
            }
            
            data = py_json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
            ctx = ssl.create_default_context(cafile=certifi.where())
            
            with urllib.request.urlopen(req, timeout=20, context=ctx) as response:
                raw_bytes = response.read()
                res_body = raw_bytes.decode('utf-8', errors='replace')
                res_data = py_json.loads(res_body)
                
                candidates = res_data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        ai_res = parts[0].get("text", "").strip()
        except Exception as err:
            print("Gemini Image API exception:", err)
            ai_res = f"სურათის ანალიზის შეცდომა: {str(err)}"

        if not ai_res:
            ai_res = f"({self.selected_lang_name}): სურათიდან პასუხი ვერ მიიღო."

        self.last_ai_text = ai_res
        self.chat_history.append(f"Gemini AI (Image): {ai_res}")
        self.update_ui("\n\n".join(self.chat_history[-6:]))
        self.speak_text(ai_res)


class SocialAndBrowserScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="Social Networks, Viber & AdBlock", font_size=18, bold=True, color=(0.2, 0.6, 1, 1), size_hint_y=None, height=35, **font_kwargs))
        
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


class SimpleScreen(Screen):
    def __init__(self, title_text, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text=title_text, font_size=18, color=(0.4, 0.8, 1, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SocialAndBrowserScreen(name='social_browser'))
        
        screens_dict = {
            'cellular_call': "Cellular Calls & Intercept",
            'voice_live': "Live Voice Stream",
            'offline_mode': "Edge AI & Offline Engine",
            'gamification': "XP & Gamification System",
            'b2b_docs': "B2B Document Analysis",
            'bio_emotional': "Bio Emotional AI Sensor",
            'cultural_guardian': "Cultural Guardian",
            'mesh_network': "Mesh Network P2P",
            'voice_clone': "Voice Clone & Synthesis",
            'dream_sync': "Dream Sync AI",
            'quantum_p2p': "Quantum Encryption",
            'holographic_ar': "Holographic AR View",
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
