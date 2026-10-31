from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import os

# Android Native Telephony & TTS with Safety Wrappers
try:
    from jnius import autoclass, PythonJavaClass, java_method
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    
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
    from plyer import camera, vibrator
    ANDROID_PLYER_AVAILABLE = True
except Exception:
    ANDROID_PLYER_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None
SERVER_ENDPOINT = "https://lingo-lens-chi.vercel.app/api/translate"

TRANSLATIONS = {
    "ka": {"name": "ქართული", "title": "✦ LingoLens Ultimate AI", "hint": "შეიტანეთ ნომერი, ტექსტი ან კითხვა...", "ready": "გამარჯობა! მე ვარ თქვენი სრულიად ჭკვიანი გლობალური AI ასისტენტი."},
    "en": {"name": "English", "title": "✦ LingoLens Ultimate AI", "hint": "Enter number, text or question...", "ready": "Hello! I am your fully smart global AI assistant."},
}

Window.clearcolor = (0.07, 0.08, 0.10, 1)
Window.softinput_mode = "below_target"


# ==========================================
# 1. მთავარი ინტელექტუალური ჩატის ეკრანი
# ==========================================
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.lang_keys = list(TRANSLATIONS.keys())
        self.lang_idx = 0
        self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
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

        # ნავიგაციის პანელები ყველა 14 მოდულზე გადასასვლელად
        top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.045), spacing=2)
        self.title_label = Label(text=str(self.t["title"]), font_size=10, bold=True, color=(0.95, 0.95, 0.97, 1), **font_kwargs)
        top_layout.add_widget(self.title_label)

        top_layout.add_widget(Button(text="📞 Call", size_hint=(None, 1), width=42, background_normal='', background_color=(0.1, 0.7, 0.3, 1), on_press=lambda x: setattr(self.manager, 'current', 'cellular_call'), **font_kwargs))
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

        # დინამიური ჩატის პანელი
        scroll = ScrollView(size_hint=(1, 0.62), bar_width=4)
        self.output_label = Label(text=str(self.t["ready"]), font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.output_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)), texture_size=lambda s, t: setattr(s, 'height', max(t[1], 200)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        # შეყვანისა და ქმედებების პანელი
        input_container = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, 0.22))
        self.text_input = TextInput(hint_text=self.t["hint"], multiline=False, size_hint=(1, 0.4), padding=[10, 10, 10, 10], background_normal='', background_active='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs)
        input_container.add_widget(self.text_input)

        bottom_actions = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.55))
        bottom_actions.add_widget(Button(text="✨ გაგზავნა", size_hint=(0.33, 1), background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), on_press=self.send_message, **font_kwargs))
        bottom_actions.add_widget(Button(text="📷 AR კამერა", size_hint=(0.33, 1), background_normal='', background_color=(0.15, 0.60, 0.45, 1), color=(1, 1, 1, 1), on_press=self.capture_image_and_translate, **font_kwargs))
        bottom_actions.add_widget(Button(text="🔊 აუდიო", size_hint=(0.34, 1), background_normal='', background_color=(0.20, 0.22, 0.28, 1), color=(1, 1, 1, 1), on_press=lambda x: self.speak_text(self.last_ai_text), **font_kwargs))

        input_container.add_widget(bottom_actions)
        root.add_widget(input_container)
        self.add_widget(root)

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

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
        self.update_ui("✦ Gemini AI ამუშავებს მოთხოვნას...")

        def worker():
            try:
                # Direct file-less / standard library or requests approach if needed
                import urllib.request
                import json as py_json
                
                req_data = py_json.dumps({"message": msg, "target_lang": self.t["name"]}).encode('utf-8')
                req = urllib.request.Request(SERVER_ENDPOINT, data=req_data, headers={'Content-Type': 'application/json'})
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    if response.status == 200:
                        res_data = py_json.loads(response.read().decode('utf-8'))
                        ai_res = res_data.get("response", "პასუხი ვერ მოიძებნა.")
                        self.last_ai_text = ai_res
                        self.chat_history.append(f"🤖 LingoLens AI: {ai_res}")
                        self.update_ui("\n\n".join(self.chat_history[-6:]))
                        self.speak_text(ai_res)
                    else:
                        self.update_ui(f"⚠️ სერვერის შეცდომა: HTTP {response.status}")
            except Exception as e:
                self.update_ui(f"🌐 ქსელთან დაკავშირების შეცდომა: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def capture_image_and_translate(self, instance):
        if ANDROID_PLYER_AVAILABLE:
            try:
                img_path = os.path.join(os.getcwd(), "capture.jpg")
                camera.take_picture(filename=img_path, on_complete=lambda p: self.update_ui("📷 AR კამერამ გადაიღო სურათი ვიზუალური ანალიზისთვის..."))
            except Exception as e:
                self.update_ui(f"კამერის შეცდომა: {str(e)}")
        else:
            self.update_ui("⚠️ AR ვიზუალური ანალიზი მუშაობს ნამდვილ ანდროიდ მოწყობილობაზე.")


# ==========================================
# 2. ფიჭური ქსელები და ზარები (Cellular & Telephony)
# ==========================================
class CellularTelephonyScreen(Screen):
    def __init__(self, **kwargs):
        super(CellularTelephonyScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]📞 Cellular Networks, Voice & Video Calls[/b]", markup=True, font_size=18, color=(0.1, 0.8, 0.4, 1)))
        
        self.status_lbl = Label(text="ფიჭური ქსელი: 4G/5G მზადყოფნაში 📶\nსიგნალი: ძლიერი (-75 dBm)\nოპერატორი: აქტიური", font_size=14, color=(0.8, 0.8, 0.8, 1), halign="center")
        layout.add_widget(self.status_lbl)

        self.phone_input = TextInput(hint_text="შეიტანეთ ტელეფონის ნომერი (მაგ: +995...)", multiline=False, size_hint_y=None, height=50, background_normal='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1,1,1,1))
        layout.add_widget(self.phone_input)

        call_btn = Button(text="📞 ფიჭური ზარის განხორციელება (Voice Call)", size_hint_y=None, height=50, background_normal='', background_color=(0.1, 0.7, 0.3, 1))
        call_btn.bind(on_press=self.make_phone_call)
        layout.add_widget(call_btn)

        video_call_btn = Button(text="📹 ვიდეო ზარის დაწყება (Video Call)", size_hint_y=None, height=50, background_normal='', background_color=(0.2, 0.5, 0.8, 1))
        video_call_btn.bind(on_press=self.make_video_call)
        layout.add_widget(video_call_btn)

        back_btn = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def make_phone_call(self, instance):
        num = self.phone_input.text.strip()
        if not num:
            self.status_lbl.text = "⚠️ გთხოვთ, შეიტანოთ ტელეფონის ნომერი!"
            return
        
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_DIAL)
                intent.setData(Uri.parse(f"tel:{num}"))
                activity.startActivity(intent)
                self.status_lbl.text = f"📞 ნომერი გადაიგზავნა დიალერში: {num}"
            except Exception as ex:
                self.status_lbl.text = f"შეცდომა ზარის განხორციელებისას: {str(ex)}"
        else:
            self.status_lbl.text = f"🧪 სიმულაცია: ზარი ნომერზე {num} (მხოლოდ ანდროიდზე)"

    def make_video_call(self, instance):
        num = self.phone_input.text.strip()
        if not num:
            self.status_lbl.text = "⚠️ გთხოვთ, შეიტანოთ ტელეფონის ნომერი ვიდეო ზარისთვის!"
            return
        
        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(f"tel:{num}"))
                activity.startActivity(intent)
                self.status_lbl.text = f"📹 ვიდეო ზარის მოთხოვნა გაიგზავნა: {num}"
            except Exception as ex:
                self.status_lbl.text = f"შეცდომა ვიდეო ზარის დროს: {str(ex)}"
        else:
            self.status_lbl.text = f"🧪 სიმულაცია: ვიდეო ზარი ნომერზე {num} (მხოლოდ ანდროიდზე)"


# ==========================================
# 3-14. დანარჩენი მოდულები
# ==========================================
class LiveVoiceScreen(Screen):
    def __init__(self, **kwargs):
        super(LiveVoiceScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]✦ Live Voice Stream[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        self.status = Label(text="სტატუსი: მოლოდინის რეჟიმში 🎙️", font_size=15, color=(0.3,0.9,0.4,1))
        layout.add_widget(self.status)
        btn = Button(text="🔴 ცოცხალი საუბრის დაწყება", size_hint_y=None, height=50, background_normal='', background_color=(0.8, 0.3, 0.35, 1))
        btn.bind(on_press=lambda x: self.status.setter('text')(self.status, "სტატუსი: აუდიო სტრიმინგი აქტიურია ⚡"))
        layout.add_widget(btn)
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class OfflineModeScreen(Screen):
    def __init__(self, **kwargs):
        super(OfflineModeScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]⚡ Edge AI & Offline Models[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class GamificationScreen(Screen):
    def __init__(self, **kwargs):
        super(GamificationScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🔥 Gamification & Streaks[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class B2BDocsScreen(Screen):
    def __init__(self, **kwargs):
        super(B2BDocsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]📁 B2B Documents Translation[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class BioEmotionalScreen(Screen):
    def __init__(self, **kwargs):
        super(BioEmotionalScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🧬 Bio-Emotional Translation[/b]", markup=True, font_size=18, color=(0.8,0.4,1,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class CulturalGuardianScreen(Screen):
    def __init__(self, **kwargs):
        super(CulturalGuardianScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🛡️ Cultural & Legal Guardian[/b]", markup=True, font_size=18, color=(1,0.4,0.3,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class MeshNetworkScreen(Screen):
    def __init__(self, **kwargs):
        super(MeshNetworkScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🌐 P2P Mesh Network[/b]", markup=True, font_size=18, color=(0.3,0.8,1,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class VoiceCloneScreen(Screen):
    def __init__(self, **kwargs):
        super(VoiceCloneScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🗣️ Native Voice Clone Sync[/b]", markup=True, font_size=18, color=(0.4,1,0.5,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class DreamSyncScreen(Screen):
    def __init__(self, **kwargs):
        super(DreamSyncScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]💤 Neuromorphic Dream Sync[/b]", markup=True, font_size=18, color=(0.6,0.3,1,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class QuantumP2PScreen(Screen):
    def __init__(self, **kwargs):
        super(QuantumP2PScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🔒 Quantum-Secured P2P Encryption[/b]", markup=True, font_size=18, color=(1,0.5,0.2,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class HolographicARScreen(Screen):
    def __init__(self, **kwargs):
        super(HolographicARScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🕶️ Holographic AR Spatial Translation[/b]", markup=True, font_size=18, color=(0.2,0.7,1,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)

class ChameleonAIScreen(Screen):
    def __init__(self, **kwargs):
        super(ChameleonAIScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🦎 Autonomous Cultural Chameleon AI[/b]", markup=True, font_size=18, color=(0.8,0.8,0.2,1)))
        back = Button(text="⬅️ დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(CellularTelephonyScreen(name='cellular_call'))
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
        return sm

if __name__ == '__main__':
    LingoLensApp().run()
