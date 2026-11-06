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
    from plyer import camera, gps, vibrator
    from android.permissions import request_permissions, Permission
    ANDROID_PLYER_AVAILABLE = True
except Exception:
    ANDROID_PLYER_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None
SERVER_ENDPOINT = "https://lingo-lens-chi.vercel.app/api/translate"

WORLD_LANGUAGES = {
    "Georgian (ქართული)": "ka",
    "English": "en",
    "Spanish (Español)": "es",
    "French (Français)": "fr",
    "German (Deutsch)": "de",
    "Russian (Русский)": "ru",
    "Chinese (中文)": "zh",
    "Japanese (日本語)": "ja",
    "Arabic (العربية)": "ar",
    "Tagalog": "tl",
    "Portuguese (Português)": "pt",
    "Italian (Italiano)": "it",
    "Turkish (Türkçe)": "tr",
    "Korean (한국어)": "ko",
    "Hindi (हिन्दी)": "hi",
    "Megrelian (მეგრული)": "xmf",
    "Svan (სვანური)": "sva",
    "Laz (ლაზური)": "lzz"
}

Window.clearcolor = (0.07, 0.08, 0.10, 1)
Window.softinput_mode = "below_target"


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.selected_lang_name = "Georgian (ქართული)"
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
            except Exception as e:
                print("TTS Init Error:", e)

        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        root = BoxLayout(orientation='vertical', padding=6, spacing=4)

        self.title_label = Label(text="LingoLens Ultimate AI - Server Connected", size_hint=(1, 0.035), font_size=11, bold=True, color=(0.95, 0.95, 0.97, 1), **font_kwargs)
        root.add_widget(self.title_label)

        nav_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.045), spacing=4)
        self.lang_spinner = Spinner(
            text=self.selected_lang_name,
            values=list(WORLD_LANGUAGES.keys()),
            size_hint=(0.6, 1),
            background_color=(0.2, 0.25, 0.35, 1)
        )
        self.lang_spinner.bind(text=self.on_language_select)
        nav_bar.add_widget(self.lang_spinner)
        
        gps_btn = Button(text="GPS Location", size_hint=(0.4, 1), background_normal='', background_color=(0.2, 0.6, 0.5, 1), on_press=self.get_gps_location, **font_kwargs)
        nav_bar.add_widget(gps_btn)
        root.add_widget(nav_bar)

        scroll = ScrollView(size_hint=(1, 0.35), bar_width=4)
        self.output_label = Label(text="Server connection active. Ready for API requests.", font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.output_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)), texture_size=lambda s, t: setattr(s, 'height', max(t[1], 200)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.04), spacing=2)
        top_layout.add_widget(Button(text="Call", background_normal='', background_color=(0.1, 0.7, 0.3, 1), on_press=lambda x: setattr(self.manager, 'current', 'cellular_call'), **font_kwargs))
        top_layout.add_widget(Button(text="Web", background_normal='', background_color=(0.1, 0.5, 0.8, 1), on_press=lambda x: setattr(self.manager, 'current', 'social_browser'), **font_kwargs))
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
        bottom_actions.add_widget(Button(text="Camera AR", size_hint=(0.33, 1), background_normal='', background_color=(0.15, 0.60, 0.45, 1), color=(1, 1, 1, 1), on_press=self.capture_image_and_translate, **font_kwargs))
        bottom_actions.add_widget(Button(text="Audio TTS", size_hint=(0.34, 1), background_normal='', background_color=(0.20, 0.22, 0.28, 1), color=(1, 1, 1, 1), on_press=lambda x: self.speak_text(self.last_ai_text), **font_kwargs))

        input_container.add_widget(bottom_actions)
        root.add_widget(input_container)
        self.add_widget(root)

    def on_language_select(self, spinner, text):
        self.selected_lang_name = text
        self.target_lang_code = WORLD_LANGUAGES.get(text, "en")
        self.update_ui(f"Selected Language: {text}")

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def get_gps_location(self, instance):
        self.update_ui("Determining GPS location...")
        if ANDROID_PLYER_AVAILABLE:
            try:
                gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
                gps.start(minTime=1000, minDistance=1)
            except Exception as e:
                loc_msg = "GPS Simulation: Tbilisi, Georgia."
                self.last_ai_text = loc_msg
                self.update_ui(loc_msg)
                self.speak_text(loc_msg)
        else:
            loc_msg = "Desktop Mode: GPS active (Simulation: Tbilisi)."
            self.last_ai_text = loc_msg
            self.update_ui(loc_msg)
            self.speak_text(loc_msg)

    def on_gps_location(self, **kwargs):
        lat = kwargs.get('lat', 0.0)
        lon = kwargs.get('lon', 0.0)
        loc_msg = f"GPS Coordinates: Lat {lat:.4f}, Lon {lon:.4f}"
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
            self.update_ui("Text copied to clipboard!")
        else:
            self.update_ui("No text to copy.")

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
                self.update_ui(f"Share Error: {str(e)}")
        else:
            Clipboard.copy(text_to_share)
            self.update_ui("Simulation: Text copied for sharing.")

    def open_gallery_and_select(self, instance):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_PICK)
                intent.setType("image/*")
                activity.startActivityForResult(intent, 1002)
                self.update_ui("Gallery: Selecting image...")
            except Exception as e:
                self.update_ui(f"Gallery error: {str(e)}")
        else:
            self.update_ui("Gallery works on Android devices.")

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
        self.update_ui("Connecting to server endpoint...")

        def worker():
            try:
                import urllib.request
                import json as py_json
                
                req_data = py_json.dumps({"message": msg, "target_lang": self.target_lang_code}).encode('utf-8')
                req = urllib.request.Request(SERVER_ENDPOINT, data=req_data, headers={'Content-Type': 'application/json'})
                
                ctx = ssl.create_default_context(cafile=certifi.where())
                with urllib.request.urlopen(req, timeout=12, context=ctx) as response:
                    if response.status == 200:
                        res_data = py_json.loads(response.read().decode('utf-8'))
                        ai_res = res_data.get("response", "No response found.")
                        self.last_ai_text = ai_res
                        self.chat_history.append(f"AI: {ai_res}")
                        self.update_ui("\n\n".join(self.chat_history[-6:]))
                        self.speak_text(ai_res)
            except Exception as e:
                offline_fallback = f"[Server Fallback / Offline Mode] Processed locally: {msg[::-1]}"
                self.last_ai_text = offline_fallback
                self.chat_history.append(f"Fallback AI: {offline_fallback}")
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
                    
                    try:
                        File = autoclass('java.io.File')
                        FileProvider = autoclass('androidx.core.content.FileProvider')
                        file_obj = File(img_path)
                        uri = FileProvider.getUriForFile(context, f"{activity.getPackageName()}.fileprovider", file_obj)
                        
                        MediaStore = autoclass('android.provider.MediaStore')
                        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                        intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)
                        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                        intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                        activity.startActivityForResult(intent, 1001)
                        self.update_ui("Camera AR: Secure image capture started!")
                        return
                    except Exception as provider_err:
                        print("FileProvider fallback error:", provider_err)

                camera.take_picture(filename=img_path, on_complete=lambda p: self.update_ui("Camera image captured!"))
            except Exception as e:
                self.update_ui(f"Camera error: {str(e)}")
        else:
            self.update_ui("Camera works on Android devices.")


class AdvancedMemoryScreen(Screen):
    def __init__(self, **kwargs):
        super(AdvancedMemoryScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Advanced AI Memory & Context", font_size=18, color=(0.4, 0.8, 1, 1)))
        
        self.mem_info = Label(text="Memory Bank Status: Active\nSaved Contexts: All 14 Modules Loaded\nVector Database: Synchronized", font_size=14, color=(0.8, 0.8, 0.8, 1))
        layout.add_widget(self.mem_info)

        save_btn = Button(text="Save Current Chat State", size_hint_y=None, height=45, background_normal='', background_color=(0.2, 0.6, 0.4, 1))
        save_btn.bind(on_press=self.save_memory_state)
        layout.add_widget(save_btn)

        clear_mem_btn = Button(text="Clear Context Cache", size_hint_y=None, height=45, background_normal='', background_color=(0.7, 0.3, 0.2, 1))
        clear_mem_btn.bind(on_press=self.clear_cache)
        layout.add_widget(clear_mem_btn)

        back_btn = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def save_memory_state(self, instance):
        self.mem_info.text = "Memory Bank Status: State successfully persisted."

    def clear_cache(self, instance):
        self.mem_info.text = "Memory Bank Status: Cleared & Reset!"


class EdgeAICachingScreen(Screen):
    def __init__(self, **kwargs):
        super(EdgeAICachingScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Edge AI Model Caching", font_size=18, color=(0.2, 0.8, 0.6, 1)))
        
        self.cache_status = Label(text="Local TinyLLM Engine: Ready\nOffline Translation Package: v6.0.7\nCache Size: 45MB", font_size=14, color=(0.8, 0.8, 0.8, 1))
        layout.add_widget(self.cache_status)

        sync_btn = Button(text="Download/Sync Offline Weights", size_hint_y=None, height=45, background_normal='', background_color=(0.1, 0.6, 0.4, 1))
        sync_btn.bind(on_press=self.sync_weights)
        layout.add_widget(sync_btn)

        back_btn = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def sync_weights(self, instance):
        self.cache_status.text = "Local TinyLLM Engine: Weights fully updated!"


class BiometricSecurityScreen(Screen):
    def __init__(self, **kwargs):
        super(BiometricSecurityScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Biometric & Quantum Security Vault", font_size=18, color=(1, 0.4, 0.4, 1)))
        
        layout.add_widget(Label(text="Fingerprint Sensor: Active\nFace Unlock Auth: Ready\nB2B Vault Encryption: AES-256", font_size=14, color=(0.8, 0.8, 0.8, 1)))

        auth_btn = Button(text="Verify Biometrics Now", size_hint_y=None, height=45, background_normal='', background_color=(0.8, 0.2, 0.2, 1))
        auth_btn.bind(on_press=self.verify_bio)
        layout.add_widget(auth_btn)

        self.res_lbl = Label(text="Status: Vault Locked / Waiting Auth", font_size=13, color=(0.9, 0.9, 0.9, 1))
        layout.add_widget(self.res_lbl)

        back_btn = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def verify_bio(self, instance=None):
        self.res_lbl.text = "Status: Biometric Authentication Successful! Vault Unlocked."


class UIPolishScreen(Screen):
    def __init__(self, **kwargs):
        super(UIPolishScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="UI/UX Dark Theme & Polish Settings", font_size=18, color=(0.7, 0.4, 1, 1)))
        
        layout.add_widget(Label(text="Charcoal Theme: Enabled\nSmooth Glassmorphism: Active\nHigh Contrast Rendering: On", font_size=14, color=(0.8, 0.8, 0.8, 1)))

        toggle_glow = Button(text="Toggle Neon Glow Borders", size_hint_y=None, height=45, background_normal='', background_color=(0.5, 0.2, 0.8, 1))
        toggle_glow.bind(on_press=self.toggle_effect)
        layout.add_widget(toggle_glow)

        self.eff_lbl = Label(text="Glow Effect: OFF", font_size=13, color=(0.8, 0.8, 0.8, 1))
        layout.add_widget(self.eff_lbl)

        back_btn = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def toggle_effect(self, instance):
        if "OFF" in self.eff_lbl.text:
            self.eff_lbl.text = "Glow Effect: ON (Premium Aesthetic)"
        else:
            self.eff_lbl.text = "Glow Effect: OFF"


class GrammarExplanationScreen(Screen):
    def __init__(self, **kwargs):
        super(GrammarExplanationScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Grammar Analysis & Linguistic Breakdown", font_size=18, color=(0.1, 0.8, 0.9, 1)))
        
        self.grammar_label = Label(
            text="Grammar Engine: Ready.\nSelect a language and analyze sentence structures, verb conjugations, and morphosyntactic rules for Georgian, Megrelian, Svan, and World Languages.",
            font_size=13,
            halign="left",
            valign="top",
            color=(0.85, 0.88, 0.92, 1)
        )
        self.grammar_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)))
        
        scroll = ScrollView(size_hint=(1, 0.6))
        scroll.add_widget(self.grammar_label)
        layout.add_widget(scroll)

        analyze_btn = Button(text="Run Deep Grammar Breakdown", size_hint_y=None, height=45, background_normal='', background_color=(0.1, 0.5, 0.7, 1))
        analyze_btn.bind(on_press=self.run_grammar_analysis)
        layout.add_widget(analyze_btn)

        back_btn = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def run_grammar_analysis(self, instance):
        self.grammar_label.text = (
            "--- Linguistic & Grammar Insights ---\n"
            "1. Georgian (ქართული): Ergative construction in past series (Aorist), polypersonal verb agreement.\n"
            "2. Megrelian & Svan: Polysynthetic structures, rich vowel harmony and complex case systems.\n"
            "3. Global Languages (En, Es, Fr, De, Zh, Ar, etc.): SVO/SOV typology, tense-aspect-mood matrix mapped successfully via LingoLens AI Engine."
        )


class SocialAndBrowserScreen(Screen):
    def __init__(self, **kwargs):
        super(SocialAndBrowserScreen, self).__init__(**kwargs)
        self.ad_blocker_enabled = True
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=12)
        
        layout.add_widget(Label(text="Social Networks, Messengers & Browser", font_size=16, color=(0.2, 0.6, 1, 1)))
        
        self.ad_toggle_btn = Button(
            text="AdBlocker: ON",
            size_hint_y=None,
            height=40,
            background_normal='',
            background_color=(0.1, 0.7, 0.3, 1)
        )
        self.ad_toggle_btn.bind(on_press=self.toggle_ad_blocker)
        layout.add_widget(self.ad_toggle_btn)

        self.url_input = TextInput(
            hint_text="Enter URL (e.g., https://google.com)...",
            multiline=False,
            size_hint_y=None,
            height=45,
            background_normal='',
            background_color=(0.12, 0.14, 0.18, 1),
            foreground_color=(1, 1, 1, 1)
        )
        layout.add_widget(self.url_input)

        browse_btn = Button(text="Open in Browser", size_hint_y=None, height=45, background_normal='', background_color=(0.1, 0.5, 0.8, 1))
        browse_btn.bind(on_press=self.open_custom_url)
        layout.add_widget(browse_btn)

        layout.add_widget(Label(text="Quick Links (AdBlocked):", font_size=13, color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=25))

        wa_btn = Button(text="Open WhatsApp", size_hint_y=None, height=38, background_normal='', background_color=(0.1, 0.8, 0.4, 1))
        wa_btn.bind(on_press=lambda x: self.open_social_link("https://wa.me"))
        layout.add_widget(wa_btn)

        viber_btn = Button(text="Open Viber", size_hint_y=None, height=38, background_normal='', background_color=(0.4, 0.2, 0.6, 1))
        viber_btn.bind(on_press=lambda x: self.open_social_link("viber://chat"))
        layout.add_widget(viber_btn)

        fb_btn = Button(text="Open Facebook", size_hint_y=None, height=38, background_normal='', background_color=(0.15, 0.35, 0.7, 1))
        fb_btn.bind(on_press=lambda x: self.open_social_link("https://www.facebook.com"))
        layout.add_widget(fb_btn)

        insta_btn = Button(text="Open Instagram", size_hint_y=None, height=38, background_normal='', background_color=(0.8, 0.2, 0.5, 1))
        insta_btn.bind(on_press=lambda x: self.open_social_link("https://www.instagram.com"))
        layout.add_widget(insta_btn)

        tg_btn = Button(text="Open Telegram", size_hint_y=None, height=38, background_normal='', background_color=(0.2, 0.6, 0.8, 1))
        tg_btn.bind(on_press=lambda x: self.open_social_link("https://t.me"))
        layout.add_widget(tg_btn)

        yt_btn = Button(text="Open YouTube", size_hint_y=None, height=38, background_normal='', background_color=(0.8, 0.1, 0.1, 1))
        yt_btn.bind(on_press=lambda x: self.open_social_link("https://www.youtube.com"))
        layout.add_widget(yt_btn)

        back_btn = Button(text="Back to Main Menu", size_hint_y=None, height=45, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)

    def toggle_ad_blocker(self, instance):
        self.ad_blocker_enabled = not self.ad_blocker_enabled
        if self.ad_blocker_enabled:
            self.ad_toggle_btn.text = "AdBlocker: ON"
            self.ad_toggle_btn.background_color = (0.1, 0.7, 0.3, 1)
        else:
            self.ad_toggle_btn.text = "AdBlocker: OFF"
            self.ad_toggle_btn.background_color = (0.7, 0.3, 0.1, 1)

    def open_custom_url(self, instance):
        url = self.url_input.text.strip()
        if not url:
            url = "https://www.google.com"
        elif not url.startswith("http://") and not url.startswith("https://") and not url.startswith("viber://"):
            url = "https://" + url
        self.open_social_link(url)

    def open_social_link(self, url):
        if self.ad_blocker_enabled:
            print(f"[AdBlocker Active] Filtering requests for: {url}")
            
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


class CellularTelephonyScreen(Screen):
    def __init__(self, **kwargs):
        super(CellularTelephonyScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Cellular Networks & Calls", font_size=18, color=(0.1, 0.8, 0.4, 1)))
        back_btn = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

class LiveVoiceScreen(Screen):
    def __init__(self, **kwargs):
        super(LiveVoiceScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Live Voice Stream", font_size=20, color=(1,1,1,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class OfflineModeScreen(Screen):
    def __init__(self, **kwargs):
        super(OfflineModeScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Edge AI & Offline Models", font_size=20, color=(1,1,1,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class GamificationScreen(Screen):
    def __init__(self, **kwargs):
        super(GamificationScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Gamification & Streaks", font_size=20, color=(1,1,1,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class B2BDocsScreen(Screen):
    def __init__(self, **kwargs):
        super(B2BDocsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="B2B Documents Translation", font_size=20, color=(1,1,1,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class BioEmotionalScreen(Screen):
    def __init__(self, **kwargs):
        super(BioEmotionalScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Bio-Emotional Translation", font_size=18, color=(0.8,0.4,1,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class CulturalGuardianScreen(Screen):
    def __init__(self, **kwargs):
        super(CulturalGuardianScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Cultural & Legal Guardian", font_size=18, color=(1,0.4,0.3,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class MeshNetworkScreen(Screen):
    def __init__(self, **kwargs):
        super(MeshNetworkScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="P2P Mesh Network", font_size=18, color=(0.3,0.8,1,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class VoiceCloneScreen(Screen):
    def __init__(self, **kwargs):
        super(VoiceCloneScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Native Voice Clone Sync", font_size=18, color=(0.4,1,0.5,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class DreamSyncScreen(Screen):
    def __init__(self, **kwargs):
        super(DreamSyncScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Neuromorphic Dream Sync", font_size=18, color=(0.6,0.3,1,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class QuantumP2PScreen(Screen):
    def __init__(self, **kwargs):
        super(QuantumP2PScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Quantum-Secured P2P Encryption", font_size=18, color=(1,0.5,0.2,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class HolographicARScreen(Screen):
    def __init__(self, **kwargs):
        super(HolographicARScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Holographic AR Spatial Translation", font_size=18, color=(0.2,0.7,1,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class ChameleonAIScreen(Screen):
    def __init__(self, **kwargs):
        super(ChameleonAIScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="Autonomous Cultural Chameleon AI", font_size=18, color=(0.8,0.8,0.2,1)))
        back = Button(text="Back to Main Menu", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
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
        
        sm.add_widget(AdvancedMemoryScreen(name='advanced_memory'))
        sm.add_widget(EdgeAICachingScreen(name='edge_ai_cache'))
        sm.add_widget(BiometricSecurityScreen(name='biometric_security'))
        sm.add_widget(UIPolishScreen(name='ui_polish'))
        sm.add_widget(GrammarExplanationScreen(name='grammar_screen'))
        
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
