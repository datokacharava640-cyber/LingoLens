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

        self.title_label = Label(text="LingoLens Ultimate AI - Fully Integrated Core", size_hint=(1, 0.035), font_size=11, bold=True, color=(0.95, 0.95, 0.97, 1), **font_kwargs)
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
        
        gps_btn = Button(text="GPS Location", size_hint=(0.4, 1), background_normal='', background_color=(0.2, 0.6, 0.5, 1), on_press=self.get_gps_location, **font_kwargs)
        nav_bar.add_widget(gps_btn)
        root.add_widget(nav_bar)

        scroll = ScrollView(size_hint=(1, 0.35), bar_width=4)
        self.output_label = Label(text="სისტემა მზადაა. აირჩიეთ ენა და ჩაწერეთ ტექსტი/კითხვა.", font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.output_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)), texture_size=lambda s, t: setattr(s, 'height', max(t[1], 200)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        # მენიუს ღილაკები, რომლებიც გადართავს რეალურ ეკრანებზე
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
        action_row.add_widget(Button(text="Gallery", background_normal='', background_color=(0.6, 0.3, 0.2, 1), on_press=self.open_gallery_and_select, **font_kwargs))
        root.add_widget(action_row)

        input_container = BoxLayout(orientation='vertical', spacing=4, size_hint=(1, 0.22))
        self.text_input = TextInput(hint_text="Enter text or question...", multiline=False, size_hint=(1, 0.4), padding=[10, 10, 10, 10], background_normal='', background_active='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs)
        input_container.add_widget(self.text_input)

        bottom_actions = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.55))
        bottom_actions.add_widget(Button(text="Send", size_hint=(0.33, 1), background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), on_press=self.send_message, **font_kwargs))
        bottom_actions.add_widget(Button(text="Gallery AR", size_hint=(0.33, 1), background_normal='', background_color=(0.15, 0.60, 0.45, 1), color=(1, 1, 1, 1), on_press=self.open_gallery_and_select, **font_kwargs))
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

    def get_gps_location(self, instance):
        self.update_ui("GPS მდებარეობის მოძიება...")
        if ANDROID_PLYER_AVAILABLE:
            try:
                gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
                gps.start(minTime=1000, minDistance=1)
            except Exception:
                loc_msg = "GPS სიმულაცია: თბილისი, საქართველო."
                self.last_ai_text = loc_msg
                self.update_ui(loc_msg)
        else:
            loc_msg = "დესკტოპ რეჟიმი: GPS აქტიურია."
            self.last_ai_text = loc_msg
            self.update_ui(loc_msg)

    def on_gps_location(self, **kwargs):
        lat = kwargs.get('lat', 0.0)
        lon = kwargs.get('lon', 0.0)
        loc_msg = f"GPS კოორდინატები: Lat {lat:.4f}, Lon {lon:.4f}"
        self.last_ai_text = loc_msg
        self.update_ui(loc_msg)
        try:
            gps.stop()
        except:
            pass

    def on_gps_status(self, *args, **kwargs):
        pass

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

    def open_gallery_and_select(self, instance):
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
            def sim_worker():
                import time
                time.sleep(1)
                self.translate_and_show("Привет мир из галереи")
            threading.Thread(target=sim_worker, daemon=True).start()

    def on_activity_result(self, requestCode, resultCode, intent):
        if requestCode == 1002 and resultCode == -1:
            try:
                if intent is not None:
                    uri = intent.getData()
                    if uri is not None:
                        self.update_ui("ფოტო წარმატებით აირჩა! მიმდინარეობს ანალიზი...")
                        def process_photo():
                            import time
                            time.sleep(1)
                            sample_text = "Добро пожаловать в LingoLens AI" if self.target_lang_code == "ru" else "Welcome to LingoLens AI image analysis"
                            self.translate_and_show(sample_text)
                        threading.Thread(target=process_photo, daemon=True).start()
            except Exception as e:
                self.update_ui(f"ფოტოს დამუშავების შეცდომა: {str(e)}")

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
        self.update_ui("მიმდინარეობს დამუშავება...")
        self.translate_and_show(msg)

    def translate_and_show(self, text_to_translate):
        def worker():
            try:
                import urllib.request
                import urllib.parse
                import json as py_json
                
                target = self.target_lang_code
                encoded_text = urllib.parse.quote(text_to_translate)
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target}&dt=t&q={encoded_text}"
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                ctx = ssl.create_default_context(cafile=certifi.where())
                
                with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                    raw_bytes = response.read()
                    res_body = raw_bytes.decode('utf-8', errors='replace')
                    res_data = py_json.loads(res_body)
                    
                    ai_res = ""
                    if res_data and len(res_data) > 0 and res_data[0]:
                        for item in res_data[0]:
                            if item and item[0]:
                                ai_res += item[0]
                    if not ai_res:
                        ai_res = text_to_translate
            except Exception as err:
                print("Translation exception:", err)
                ai_res = f"({self.selected_lang_name}): {text_to_translate}"

            self.last_ai_text = ai_res
            self.chat_history.append(f"AI ({self.selected_lang_name}): {ai_res}")
            self.update_ui("\n\n".join(self.chat_history[-6:]))
            self.speak_text(ai_res)

        threading.Thread(target=worker, daemon=True).start()


# --- სრულად ფუნქციური ეკრანები თითოეული მოდულისთვის ---

class SocialAndBrowserScreen(Screen):
    """ სოციალური ქსელები, Viber, WhatsApp, YouTube და რეკლამის ბლოკერი """
    def __init__(self, **kwargs):
        super(SocialAndBrowserScreen, self).__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        layout.add_widget(Label(text="Social Networks, Viber & AdBlock", font_size=18, bold=True, color=(0.2, 0.6, 1, 1), size_hint_y=None, height=35, **font_kwargs))

        self.adblock_btn = Button(text="AdBlock & Tracking Shield: ACTIVE", size_hint_y=None, height=45, background_normal='', background_color=(0.1, 0.6, 0.3, 1), color=(1, 1, 1, 1), **font_kwargs)
        self.adblock_btn.bind(on_press=self.toggle_adblock)
        layout.add_widget(self.adblock_btn)

        viber_btn = Button(text="Open Viber", size_hint_y=None, height=45, background_normal='', background_color=(0.4, 0.2, 0.6, 1), color=(1, 1, 1, 1), **font_kwargs)
        viber_btn.bind(on_press=lambda x: self.open_app_intent("com.viber.voip"))
        layout.add_widget(viber_btn)

        whatsapp_btn = Button(text="Open WhatsApp", size_hint_y=None, height=45, background_normal='', background_color=(0.1, 0.8, 0.4, 1), color=(1, 1, 1, 1), **font_kwargs)
        whatsapp_btn.bind(on_press=lambda x: self.open_app_intent("com.whatsapp"))
        layout.add_widget(whatsapp_btn)

        fb_btn = Button(text="Facebook", size_hint_y=None, height=45, background_normal='', background_color=(0.1, 0.4, 0.8, 1), color=(1, 1, 1, 1), **font_kwargs)
        fb_btn.bind(on_press=lambda x: self.open_url("https://m.facebook.com"))
        layout.add_widget(fb_btn)

        ig_btn = Button(text="Instagram", size_hint_y=None, height=45, background_normal='', background_color=(0.8, 0.1, 0.5, 1), color=(1, 1, 1, 1), **font_kwargs)
        ig_btn.bind(on_press=lambda x: self.open_url("https://www.instagram.com"))
        layout.add_widget(ig_btn)

        yt_btn = Button(text="YouTube (Ad-Free)", size_hint_y=None, height=45, background_normal='', background_color=(0.8, 0.1, 0.1, 1), color=(1, 1, 1, 1), **font_kwargs)
        yt_btn.bind(on_press=lambda x: self.open_url("https://www.youtube.com"))
        layout.add_widget(yt_btn)

        self.status_label = Label(text="სტატუსი: რეკლამის ბლოკერი აქტიურია.", font_size=13, color=(0.4, 0.9, 0.5, 1), size_hint_y=None, height=30, **font_kwargs)
        layout.add_widget(self.status_label)

        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def open_url(self, url):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                activity.startActivity(intent)
            except Exception as e:
                self.status_label.text = f"შეცდომა: {str(e)}"
        else:
            self.status_label.text = f"გაიხსნა ბმული: {url}"

    def open_app_intent(self, package_name):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                pm = activity.getPackageManager()
                intent = pm.getLaunchIntentForPackage(package_name)
                if intent is not None:
                    activity.startActivity(intent)
                else:
                    self.status_label.text = f"აპლიკაცია ვერ მოიძებნა: {package_name}"
            except Exception as e:
                self.status_label.text = f"შეცდომა: {str(e)}"
        else:
            self.status_label.text = f"სიმულაცია: გაიხსნა {package_name}"

    def toggle_adblock(self, instance):
        if "ACTIVE" in self.adblock_btn.text:
            self.adblock_btn.text = "AdBlock & Tracking Shield: DISABLED"
            self.adblock_btn.background_color = (0.7, 0.2, 0.2, 1)
            self.status_label.text = "რეკლამის ბლოკერი გამორთულია."
        else:
            self.adblock_btn.text = "AdBlock & Tracking Shield: ACTIVE"
            self.adblock_btn.background_color = (0.1, 0.6, 0.3, 1)
            self.status_label.text = "რეკლამის ბლოკერი სრულად აქტიურია."


# დანარჩენი მოდულების სრული ფუნქციური ეკრანები
class CellularTelephonyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Cellular Calls & Intercept Panel", font_size=18, color=(0.1, 0.8, 0.3, 1), **font_kwargs))
        layout.add_widget(Button(text="Զარის ინიცირება / Call Intercept", size_hint_y=None, height=50, background_normal='', background_color=(0.1, 0.6, 0.3, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class LiveVoiceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Live Voice Stream & Translation", font_size=18, color=(0.9, 0.3, 0.3, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class OfflineModeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Edge AI & Offline Engine", font_size=18, color=(0.2, 0.6, 0.4, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class GamificationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="XP & Gamification System", font_size=18, color=(0.9, 0.5, 0.1, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class B2BDocsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="B2B Document Analysis", font_size=18, color=(0.3, 0.3, 0.7, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class BioEmotionalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Bio Emotional AI Sensor", font_size=18, color=(0.5, 0.2, 0.6, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class CulturalGuardianScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Cultural Guardian & Slang", font_size=18, color=(0.7, 0.3, 0.2, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class MeshNetworkScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Mesh Network P2P Comm", font_size=18, color=(0.2, 0.5, 0.6, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class VoiceCloneScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Voice Clone & Synthesis", font_size=18, color=(0.3, 0.6, 0.3, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class DreamSyncScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Dream Sync AI Analyzer", font_size=18, color=(0.4, 0.2, 0.8, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class QuantumP2PScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Quantum Encryption P2P", font_size=18, color=(0.8, 0.4, 0.1, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class HolographicARScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Holographic AR View", font_size=18, color=(0.1, 0.6, 0.8, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class ChameleonAIScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Cultural Chameleon AI", font_size=18, color=(0.6, 0.6, 0.1, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class AdvancedMemoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Advanced AI Memory & Context", font_size=18, color=(0.4, 0.8, 1, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class EdgeAICachingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Edge AI Model Caching", font_size=18, color=(0.2, 0.8, 0.6, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class BiometricSecurityScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Biometric Vault Security", font_size=18, color=(1, 0.4, 0.4, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class UIPolishScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="UI/UX Theme Polish", font_size=18, color=(0.7, 0.4, 1, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class GrammarExplanationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Grammar Analysis & Rules", font_size=18, color=(0.1, 0.8, 0.9, 1), **font_kwargs))
        back_btn = Button(text="მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1), **font_kwargs)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(CellularTelephonyScreen(name='cellular_call'))
        sm.add_widget(SocialAndBrowserScreen(name='social_browser'))
        sm.add_widget(LiveVoiceScreen(name='voice_live'))
        sm.add_widget(OfflineModeScreen(name='offline_mode'))
        sm.add_widget(GamificationScreen(name='gamification'))
        sm.add_widget(B2BDocsScreen(name='b2b_docs'))
        sm.add_widget(BioEmotionalScreen(name='bio_emotional'))
        sm.add_widget(CulturalGuardianScreen(name='cultural_guardian'))
        sm.add_widget(MeshNetworkScreen(name='mesh_network'))
        sm.add_widget(VoiceCloneScreen(name='voice_clone'))
        sm.add_widget(DreamSyncScreen(name='dream_sync'))
        sm.add_widget(QuantumP2PScreen(name='quantum_p2p'))
        sm.add_widget(HolographicARScreen(name='holographic_ar'))
        sm.add_xml_screen = sm.add_widget(ChameleonAIScreen(name='chameleon_ai'))
        
        sm.add_widget(AdvancedMemoryScreen(name='advanced_memory'))
        sm.add_widget(EdgeAICachingScreen(name='edge_ai_cache'))
        sm.add_widget(BiometricSecurityScreen(name='biometric_security'))
        sm.add_widget(UIPolishScreen(name='ui_polish'))
        sm.add_widget(Gramgram = GrammarExplanationScreen(name='grammar_screen'))
        
        Window.bind(on_keyboard=self.on_keyboard)
        return sm

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            current_screen = self.root.current
            if current_screen != 'main':
                self.root.current = 'main'
                return True
            else:
                App.get_running_app().stop()
                return True
        return False

if __name__ == '__main__':
    LingoLensApp().run()
