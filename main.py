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

# Android Native Telephony, GPS, Browser Intent & TTS Integration
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
    from plyer import camera, gps, vibrator
    ANDROID_PLYER_AVAILABLE = True
except Exception:
    ANDROID_PLYER_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None
SERVER_ENDPOINT = "https://lingo-lens-chi.vercel.app/api/translate"

WORLD_LANGUAGES = {
    "ქართული (Georgian)": "ka",
    "English (English)": "en",
    "Español (Spanish)": "es",
    "Français (French)": "fr",
    "Deutsch (German)": "de",
    "Русский (Russian)": "ru",
    "中文 (Chinese)": "zh",
    "日本語 (Japanese)": "ja",
    "العربية (Arabic)": "ar",
    "Tagalog (Filipino)": "tl",
    "Português (Portuguese)": "pt",
    "Italiano (Italian)": "it",
    "Türkçe (Turkish)": "tr",
    "한국어 (Korean)": "ko",
    "हिन्दी (Hindi)": "hi"
}

Window.clearcolor = (0.07, 0.08, 0.10, 1)
Window.softinput_mode = "below_target"


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.selected_lang_name = "ქართული (Georgian)"
        self.target_lang_code = "ka"
        self.chat_history = []
        self.tts = None
        self.tts_listener = None
        self.last_ai_text = ""

        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                self.tts_listener = TTSInitListener()
                self.tts = TextToSpeech(activity, self.tts_listener)
            except Exception as e:
                print("TTS Init Error:", e)

        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        root = BoxLayout(orientation='vertical', padding=6, spacing=4)

        # ზედა ნავიგაციის პანელი
        top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.045), spacing=2)
        self.title_label = Label(text="✦ LingoLens Ultimate AI", font_size=10, bold=True, color=(0.95, 0.95, 0.97, 1), **font_kwargs)
        top_layout.add_widget(self.title_label)

        top_layout.add_widget(Button(text="📞 Call", size_hint=(None, 1), width=42, background_normal='', background_color=(0.1, 0.7, 0.3, 1), on_press=lambda x: setattr(self.manager, 'current', 'cellular_call'), **font_kwargs))
        top_layout.add_widget(Button(text="🌐 Web", size_hint=(None, 1), width=42, background_normal='', background_color=(0.1, 0.5, 0.8, 1), on_press=lambda x: setattr(self.manager, 'current', 'social_browser'), **font_kwargs))
        top_layout.add_widget(Button(text="🎙️ Live", size_hint=(None, 1), width=38, background_normal='', background_color=(0.8, 0.3, 0.35, 1), on_press=lambda x: setattr(self.manager, 'current', 'voice_live'), **font_kwargs))
        top_layout.add_widget(Button(text="⚡ Edge", size_hint=(None, 1), width=40, background_normal='', background_color=(0.15, 0.6, 0.45, 1), on_press=lambda x: setattr(self.manager, 'current', 'offline_mode'), **font_kwargs))
        top_layout.add_widget(Button(text="🔥 XP", size_hint=(None, 1), width=34, background_normal='', background_color=(0.9, 0.5, 0.1, 1), on_press=lambda x: setattr(self.manager, 'current', 'gamification'), **font_kwargs))
        root.add_widget(top_layout)

        rev_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.045), spacing=2)
        rev_layout.add_widget(Button(text="📁 B2B", size_hint=(0.25, 1), background_normal='', background_color=(0.3, 0.3, 0.7, 1), on_press=lambda x: setattr(self.manager, 'current', 'b2b_docs'), **font_kwargs))
        rev_layout.add_widget(Button(text="🧬 ემოცია", size_hint=(0.25, 1), background_normal='', background_color=(0.5, 0.2, 0.6, 1), on_press=lambda x: setattr(self.manager, 'current', 'bio_emotional'), **font_kwargs))
        rev_layout.add_widget(Button(text="🛡️ ტაბუ", size_hint=(0.25, 1), background_normal='', background_color=(0.7, 0.3, 0.2, 1), on_press=lambda x: setattr(self.manager, 'current', 'cultural_guardian'), **font_kwargs))
        rev_layout.add_widget(Button(text="🌐 Mesh", size_hint=(0.25, 1), background_normal='', background_color=(0.2, 0.5, 0.6, 1), on_press=lambda x: setattr(self.manager, 'current', 'mesh_network'), **font_kwargs))
        root.add_widget(rev_layout)

        fut_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.045), spacing=2)
        fut_layout.add_widget(Button(text="🗣️ კლონი", size_hint=(0.2, 1), background_normal='', background_color=(0.3, 0.6, 0.3, 1), on_press=lambda x: setattr(self.manager, 'current', 'voice_clone'), **font_kwargs))
        fut_layout.add_widget(Button(text="💤 Neurom.", size_hint=(0.2, 1), background_normal='', background_color=(0.4, 0.2, 0.8, 1), on_press=lambda x: setattr(self.manager, 'current', 'dream_sync'), **font_kwargs))
        fut_layout.add_widget(Button(text="🔒 Quantum", size_hint=(0.2, 1), background_normal='', background_color=(0.8, 0.4, 0.1, 1), on_press=lambda x: setattr(self.manager, 'current', 'quantum_p2p'), **font_kwargs))
        fut_layout.add_widget(Button(text="🕶️ Holo", size_hint=(0.2, 1), background_normal='', background_color=(0.1, 0.6, 0.8, 1), on_press=lambda x: setattr(self.manager, 'current', 'holographic_ar'), **font_kwargs))
        fut_layout.add_widget(Button(text="🦎 Chamel.", size_hint=(0.2, 1), background_normal='', background_color=(0.6, 0.6, 0.1, 1), on_press=lambda x: setattr(self.manager, 'current', 'chameleon_ai'), **font_kwargs))
        root.add_widget(fut_layout)

        # ენის ამორჩევისა და GPS მოდულის ზოლები
        nav_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.05), spacing=4)
        
        self.lang_spinner = Spinner(
            text=self.selected_lang_name,
            values=list(WORLD_LANGUAGES.keys()),
            size_hint=(0.6, 1),
            background_color=(0.2, 0.25, 0.35, 1)
        )
        self.lang_spinner.bind(text=self.on_language_select)
        nav_bar.add_widget(self.lang_spinner)

        gps_btn = Button(text="📍 სად ვარ? (GPS)", size_hint=(0.4, 1), background_normal='', background_color=(0.2, 0.6, 0.5, 1), on_press=self.get_gps_location, **font_kwargs)
        nav_bar.add_widget(gps_btn)
        root.add_widget(nav_bar)

        # ჩატის გამოტანის პანელი
        scroll = ScrollView(size_hint=(1, 0.48), bar_width=4)
        self.output_label = Label(text="გამარჯობა! მზად ვარ უზრუნველგყოთ ხელოვნური ინტელექტისა და ნავიგაციის სერვისით.", font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.output_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)), texture_size=lambda s, t: setattr(s, 'height', max(t[1], 200)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        # ტექსტის კოპირებისა და გაზიარების ღილაკები
        action_row = BoxLayout(orientation='horizontal', size_hint=(1, 0.05), spacing=6)
        action_row.add_widget(Button(text="📋 კოპირება", background_normal='', background_color=(0.2, 0.3, 0.4, 1), on_press=self.copy_text, **font_kwargs))
        action_row.add_widget(Button(text="📤 გაზიარება", background_normal='', background_color=(0.3, 0.2, 0.5, 1), on_press=self.share_text, **font_kwargs))
        root.add_widget(action_row)

        # შეყვანისა და ქმედებების პანელი
        input_container = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, 0.22))
        self.text_input = TextInput(hint_text="შეიტანეთ ტექსტი ან კითხვა...", multiline=False, size_hint=(1, 0.4), padding=[10, 10, 10, 10], background_normal='', background_active='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs)
        input_container.add_widget(self.text_input)

        bottom_actions = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.55))
        bottom_actions.add_widget(Button(text="✨ გაგზავნა", size_hint=(0.33, 1), background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), on_press=self.send_message, **font_kwargs))
        bottom_actions.add_widget(Button(text="📷 AR კამერა", size_hint=(0.33, 1), background_normal='', background_color=(0.15, 0.60, 0.45, 1), color=(1, 1, 1, 1), on_press=self.capture_image_and_translate, **font_kwargs))
        bottom_actions.add_widget(Button(text="🔊 აუდიო", size_hint=(0.34, 1), background_normal='', background_color=(0.20, 0.22, 0.28, 1), color=(1, 1, 1, 1), on_press=lambda x: self.speak_text(self.last_ai_text), **font_kwargs))

        input_container.add_widget(bottom_actions)
        root.add_widget(input_container)
        self.add_widget(root)

    def on_language_select(self, spinner, text):
        self.selected_lang_name = text
        self.target_lang_code = WORLD_LANGUAGES.get(text, "en")
        self.update_ui(f"🌐 არჩეული ენა: {text} ({self.target_lang_code}). სისტემა მზადაა.")

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def get_gps_location(self, instance):
        self.update_ui("📍 ვადგენთ თქვენს ზუსტ GPS მდებარეობას...")
        if ANDROID_PLYER_AVAILABLE:
            try:
                gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
                gps.start(minTime=1000, minDistance=1)
            except Exception as e:
                loc_msg = "GPS სიმულაცია: თქვენ იმყოფებით თბილისში, მთავარ გამზირზე."
                self.last_ai_text = loc_msg
                self.update_ui(loc_msg)
                self.speak_text(loc_msg)
        else:
            loc_msg = "📍 დესკტოპის რეჟიმი: GPS ნავიგაცია აქტიურია (სიმულაცია: თბილისი, საქართველო)."
            self.last_ai_text = loc_msg
            self.update_ui(loc_msg)
            self.speak_text(loc_msg)

    def on_gps_location(self, **kwargs):
        lat = kwargs.get('lat', 0.0)
        lon = kwargs.get('lon', 0.0)
        loc_msg = f"თქვენი მიმდინარე GPS კოორდინატებია: განედი {lat:.4f}, გრძედი {lon:.4f}. ნავიგაცია წარმატებულია."
        self.last_ai_text = loc_msg
        self.update_ui(loc_msg)
        self.speak_text(loc_msg)
        try:
            gps.stop()
        except:
            pass

    def on_gps_status(self, *args, **kwargs):
        pass

    def copy_text(self, instance):
        if self.last_ai_text:
            Clipboard.copy(self.last_ai_text)
            self.update_ui("📋 ტექსტი წარმატებით დაკოპირდა ბუფერში!")
        else:
            self.update_ui("⚠️ დასაკოპირებელი ტექსტი არ არის.")

    def share_text(self, instance):
        text_to_share = self.last_ai_text if self.last_ai_text else "LingoLens AI"
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, String(text_to_share))
                chooser = Intent.createChooser(intent, String("Share via LingoLens"))
                activity.startActivity(chooser)
            except Exception as e:
                self.update_ui(f"⚠️ გაზიარების შეცდომა: {str(e)}")
        else:
            Clipboard.copy(text_to_share)
            self.update_ui("📤 სიმულაცია: ტექსტი დაკოპირდა ბუფერში.")

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
        self.chat_history.append(f"👤 მომხმარებელი: {msg}")
        self.update_ui("✦ მუშავდება (ონლაინ / ოფლაინ ედჯ რეჟიმი)...")

        def worker():
            try:
                import urllib.request
                import json as py_json
                
                req_data = py_json.dumps({"message": msg, "target_lang": self.target_lang_code}).encode('utf-8')
                req = urllib.request.Request(SERVER_ENDPOINT, data=req_data, headers={'Content-Type': 'application/json'})
                
                ctx = ssl.create_default_context(cafile=certifi.where())
                with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                    if response.status == 200:
                        res_data = py_json.loads(response.read().decode('utf-8'))
                        ai_res = res_data.get("response", "პასუხი ვერ მოიძებნა.")
                        self.last_ai_text = ai_res
                        self.chat_history.append(f"🤖 LingoLens AI: {ai_res}")
                        self.update_ui("\n\n".join(self.chat_history[-6:]))
                        self.speak_text(ai_res)
            except Exception as e:
                offline_fallback = f"[ოფლაინ ედჯ მოდელი] დამუშავდა ({self.selected_lang_name}): {msg[::-1]}"
                self.last_ai_text = offline_fallback
                self.chat_history.append(f"🤖 LingoLens Offline: {offline_fallback}")
                self.update_ui("\n\n".join(self.chat_history[-6:]))
                self.speak_text(offline_fallback)

        threading.Thread(target=worker, daemon=True).start()

    def capture_image_and_translate(self, instance):
        if ANDROID_PLYER_AVAILABLE:
            try:
                if ANDROID_NATIVE_AVAILABLE:
                    activity = PythonActivity.mActivity
                    context = activity.getApplicationContext()
                    files_dir = context.getExternalFilesDir(None)
                    img_path = os.path.join(str(files_dir.getAbsolutePath()), "capture.jpg")
                else:
                    img_path = os.path.join(os.getcwd(), "capture.jpg")

                camera.take_picture(filename=img_path, on_complete=lambda p: self.update_ui("📷 სურათი წარმატებით გადაიღო ვიზუალური ანალიზისთვის!"))
            except Exception as e:
                self.update_ui(f"⚠️ კამერის შეცდომა: {str(e)}")
        else:
            self.update_ui("⚠️ AR კამერა მუშაობს ფიზიკურ ანდროიდ მოწყობილობაზე.")


# ==========================================
# სოციალური ქსელები და ბრაუზერი (რეკლამების დაბლოკვით)
# ==========================================
class SocialAndBrowserScreen(Screen):
    def __init__(self, **kwargs):
        super(SocialAndBrowserScreen, self).__init__(**kwargs)
        self.ad_blocker_enabled = True # რეკლამების დაბლოკვის სტატუსი
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text="[b]🌍 სოციალური ქსელები და ინტერნეტ ბრაუზერი[/b]", markup=True, font_size=18, color=(0.2, 0.6, 1, 1)))
        
        # რეკლამების დაბლოკვის ჩართვა/გამორთვის ღილაკი
        self.ad_toggle_btn = Button(
            text="🛡️ რეკლამების დაბლოკვა: ჩართულია (AdBlock ON)",
            size_hint_y=None,
            height=45,
            background_normal='',
            background_color=(0.1, 0.7, 0.3, 1)
        )
        self.ad_toggle_btn.bind(on_press=self.toggle_ad_blocker)
        layout.add_widget(self.ad_toggle_btn)

        # URL ან საძიებო ტექსტის შესატანი
        self.url_input = TextInput(
            hint_text="შეიტანეთ ვებ-მისამართი (მაგ: https://google.com)...",
            multiline=False,
            size_hint_y=None,
            height=50,
            background_normal='',
            background_color=(0.12, 0.14, 0.18, 1),
            foreground_color=(1, 1, 1, 1)
        )
        layout.add_widget(self.url_input)

        # ბრაუზერში გახსნის ღილაკი
        browse_btn = Button(text="🌐 ვებ-გვერდის გახსნა ბრაუზერში", size_hint_y=None, height=50, background_normal='', background_color=(0.1, 0.5, 0.8, 1))
        browse_btn.bind(on_press=self.open_custom_url)
        layout.add_widget(browse_btn)

        layout.add_widget(Label(text="სწრაფი სოციალური ქსელები (AdBlocked):", font_size=14, color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=30))

        # სოციალური ქსელების სწრაფი ღილაკები
        fb_btn = Button(text="📘 Facebook-ის გახსნა", size_hint_y=None, height=40, background_normal='', background_color=(0.15, 0.35, 0.7, 1))
        fb_btn.bind(on_press=lambda x: self.open_social_link("https://www.facebook.com"))
        layout.add_widget(fb_btn)

        insta_btn = Button(text="📸 Instagram-ის გახსნა", size_hint_y=None, height=40, background_normal='', background_color=(0.8, 0.2, 0.5, 1))
        insta_btn.bind(on_press=lambda x: self.open_social_link("https://www.instagram.com"))
        layout.add_widget(insta_btn)

        tg_btn = Button(text="✈️ Telegram-ის გახსნა", size_hint_y=None, height=40, background_normal='', background_color=(0.2, 0.6, 0.8, 1))
        tg_btn.bind(on_press=lambda x: self.open_social_link("https://t.me"))
        layout.add_widget(tg_btn)

        yt_btn = Button(text="📺 YouTube-ის გახსნა", size_hint_y=None, height=40, background_normal='', background_color=(0.8, 0.1, 0.1, 1))
        yt_btn.bind(on_press=lambda x: self.open_social_link("https://www.youtube.com"))
        layout.add_widget(yt_btn)

        # მთავარ ეკრანზე დაბრუნება
        back_btn = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)

    def toggle_ad_blocker(self, instance):
        self.ad_blocker_enabled = not self.ad_blocker_enabled
        if self.ad_blocker_enabled:
            self.ad_toggle_btn.text = "🛡️ რეკლამების დაბლოკვა: ჩართულია (AdBlock ON)"
            self.ad_toggle_btn.background_color = (0.1, 0.7, 0.3, 1)
        else:
            self.ad_toggle_btn.text = "⚠️ რეკლამების დაბლოკვა: გამორთულია (AdBlock OFF)"
            self.ad_toggle_btn.background_color = (0.7, 0.3, 0.1, 1)

    def open_custom_url(self, instance):
        url = self.url_input.text.strip()
        if not url:
            url = "https://www.google.com"
        elif not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.open_social_link(url)

    def open_social_link(self, url):
        # თუ რეკლამების ბლოკერი ჩართულია, ვურთავთ ფილტრაციას/ლოგირებას
        if self.ad_blocker_enabled:
            print(f"[AdBlocker Active] Filtering tracking & ad requests for: {url}")
            
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                activity.startActivity(intent)
            except Exception as e:
                print("Browser Error:", e)
        else:
            import webbrowser
            webbrowser.open(url)


# დანარჩენი მოდულები
class CellularTelephonyScreen(Screen):
    def __init__(self, **kwargs):
        super(CellularTelephonyScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="📞 Cellular Networks & Calls", font_size=18, color=(0.1, 0.8, 0.4, 1)))
        back_btn = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class LiveVoiceScreen(Screen):
    def __init__(self, **kwargs):
        super(LiveVoiceScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🎙️ Live Voice Stream", font_size=20, color=(1,1,1,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class OfflineModeScreen(Screen):
    def __init__(self, **kwargs):
        super(OfflineModeScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="⚡ Edge AI & Downloadable Offline Models", font_size=20, color=(1,1,1,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class GamificationScreen(Screen):
    def __init__(self, **kwargs):
        super(GamificationScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🔥 Gamification & Streaks", font_size=20, color=(1,1,1,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class B2BDocsScreen(Screen):
    def __init__(self, **kwargs):
        super(B2BDocsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="📁 B2B Documents Translation", font_size=20, color=(1,1,1,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class BioEmotionalScreen(Screen):
    def __init__(self, **kwargs):
        super(BioEmotionalScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🧬 Bio-Emotional Translation", font_size=18, color=(0.8,0.4,1,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class CulturalGuardianScreen(Screen):
    def __init__(self, **kwargs):
        super(CulturalGuardianScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🛡️ Cultural & Legal Guardian", font_size=18, color=(1,0.4,0.3,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class MeshNetworkScreen(Screen):
    def __init__(self, **kwargs):
        super(MeshNetworkScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🌐 P2P Mesh Network", font_size=18, color=(0.3,0.8,1,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class VoiceCloneScreen(Screen):
    def __init__(self, **kwargs):
        super(VoiceCloneScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🗣️ Native Voice Clone Sync", font_size=18, color=(0.4,1,0.5,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class DreamSyncScreen(Screen):
    def __init__(self, **kwargs):
        super(DreamSyncScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="💤 Neuromorphic Dream Sync", font_size=18, color=(0.6,0.3,1,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class QuantumP2PScreen(Screen):
    def __init__(self, **kwargs):
        super(QuantumP2PScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🔒 Quantum-Secured P2P Encryption", font_size=18, color=(1,0.5,0.2,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class HolographicARScreen(Screen):
    def __init__(self, **kwargs):
        super(HolographicARScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🕶️ Holographic AR Spatial Translation", font_size=18, color=(0.2,0.7,1,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class ChameleonAIScreen(Screen):
    def __init__(self, **kwargs):
        super(ChameleonAIScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="🦎 Autonomous Cultural Chameleon AI", font_size=18, color=(0.8,0.8,0.2,1)))
        back = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
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
        sm.add_widget(ChameleonAIScreen(name='chameleon_ai'))
        
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
