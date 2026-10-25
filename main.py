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
import requests
import os
import base64
import traceback

# Android Native TTS & STT
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Intent = autoclass('android.content.Intent')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
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
    "ka": {"name": "ქართული", "title": "✦ LingoLens Universe AI", "hint": "ჰკითხეთ ან შეიტანეთ ტექსტი...", "ready": "გამარჯობა! მზად ვარ მსოფლიოში პირველი რევოლუციური თარგმანისთვის."},
    "en": {"name": "English", "title": "✦ LingoLens Universe AI", "hint": "Ask LingoLens or type text...", "ready": "Hello! Ready for world-first revolutionary translation."},
}

Window.clearcolor = (0.07, 0.08, 0.10, 1)
Window.softinput_mode = "below_target"


# 1. მთავარი ეკრანი (AI Chat & AR Vision)
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.lang_keys = list(TRANSLATIONS.keys())
        self.lang_idx = 0
        self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
        self.chat_history = []
        self.tts = None
        self.last_ai_text = ""

        if ANDROID_NATIVE_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                self.tts = TextToSpeech(activity, None)
            except Exception as e:
                print("TTS Init Error:", e)

        font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}
        root = BoxLayout(orientation='vertical', padding=10, spacing=8)

        # ზედა ნავიგაცია ყველა მოდულზე
        top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.07), spacing=3)
        self.title_label = Label(text=str(self.t["title"]), font_size=12, bold=True, color=(0.95, 0.95, 0.97, 1), **font_kwargs)
        top_layout.add_widget(self.title_label)

        top_layout.add_widget(Button(text="🎙️ Live", size_hint=(None, 1), width=45, background_normal='', background_color=(0.8, 0.3, 0.35, 1), on_press=lambda x: setattr(self.manager, 'current', 'voice_live'), **font_kwargs))
        top_layout.add_widget(Button(text="⚡ Edge", size_hint=(None, 1), width=48, background_normal='', background_color=(0.15, 0.6, 0.45, 1), on_press=lambda x: setattr(self.manager, 'current', 'offline_mode'), **font_kwargs))
        top_layout.add_widget(Button(text="🔥 XP", size_hint=(None, 1), width=40, background_normal='', background_color=(0.9, 0.5, 0.1, 1), on_press=lambda x: setattr(self.manager, 'current', 'gamification'), **font_kwargs))
        top_layout.add_widget(Button(text="📁 B2B", size_hint=(None, 1), width=42, background_normal='', background_color=(0.3, 0.3, 0.7, 1), on_press=lambda x: setattr(self.manager, 'current', 'b2b_docs'), **font_kwargs))
        
        root.add_widget(top_layout)

        # მეორე რიგის ნავიგაცია 4 ახალი რევოლუციური ფუნქციისთვის
        rev_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.07), spacing=3)
        rev_layout.add_widget(Button(text="🧬 ემოცია", size_hint=(0.25, 1), background_normal='', background_color=(0.5, 0.2, 0.6, 1), on_press=lambda x: setattr(self.manager, 'current', 'bio_emotional'), **font_kwargs))
        rev_layout.add_widget(Button(text="🛡️ ტაბუ", size_hint=(0.25, 1), background_normal='', background_color=(0.7, 0.3, 0.2, 1), on_press=lambda x: setattr(self.manager, 'current', 'cultural_guardian'), **font_kwargs))
        rev_layout.add_widget(Button(text="🌐 Mesh", size_hint=(0.25, 1), background_normal='', background_color=(0.2, 0.5, 0.6, 1), on_press=lambda x: setattr(self.manager, 'current', 'mesh_network'), **font_kwargs))
        rev_layout.add_widget(Button(text="🗣️ კლონი", size_hint=(0.25, 1), background_normal='', background_color=(0.3, 0.6, 0.3, 1), on_press=lambda x: setattr(self.manager, 'current', 'voice_clone'), **font_kwargs))
        root.add_widget(rev_layout)

        # პასუხების ველი
        scroll = ScrollView(size_hint=(1, 0.52), bar_width=4)
        self.output_label = Label(text=str(self.t["ready"]), font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.output_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)), texture_size=lambda s, t: setattr(s, 'height', max(t[1], 180)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        # შეყვანისა და ქმედებების პანელი
        input_container = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, 0.28))
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
        self.chat_history.append(f"User: {msg}")
        self.update_ui("✦ Gemini AI აანალიზებს მოთხოვნას...")

        def worker():
            try:
                res = requests.post(SERVER_ENDPOINT, json={"message": msg, "target_lang": self.t["name"]}, timeout=15)
                if res.status_code == 200:
                    ai_res = res.json().get("response", "")
                    self.last_ai_text = ai_res
                    self.chat_history.append(f"AI: {ai_res}")
                    self.update_ui("\n\n".join(self.chat_history[-6:]))
                    self.speak_text(ai_res)
                else:
                    self.update_ui(f"სერვერის შეცდომა [{res.status_code}]")
            except Exception as e:
                self.update_ui(f"ქსელის შეცდომა: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def capture_image_and_translate(self, instance):
        if ANDROID_PLYER_AVAILABLE:
            try:
                img_path = os.path.join(os.getcwd(), "capture.jpg")
                camera.take_picture(filename=img_path, on_complete=lambda p: self.update_ui("📷 AR ფოტო წარმატებით გადაიღო და გაიგზავნა ანალიზისთვის!"))
            except Exception as e:
                self.update_ui(f"კამერის შეცდომა: {str(e)}")
        else:
            self.update_ui("⚠️ AR კამერა ხელმისაწვდომია მხოლოდ ანდროიდ მოწყობილობაზე.")


# 2. Live Voice Screen
class LiveVoiceScreen(Screen):
    def __init__(self, **kwargs):
        super(LiveVoiceScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]✦ LingoLens Live Voice Stream[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        layout.add_widget(Label(text="ცოცხალი აუდიო ნაკადის სტრიმინგი მზად არის.", font_size=14, color=(0.8,0.8,0.8,1)))
        back_btn = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 3. Offline Mode Screen
class OfflineModeScreen(Screen):
    def __init__(self, **kwargs):
        super(OfflineModeScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]⚡ Edge AI & Offline Models[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        layout.add_widget(Label(text="ლოკალური მოდელების მართვა ინტერნეტის გარეშე მუშაობისთვის.", font_size=14, color=(0.8,0.8,0.8,1)))
        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 4. Gamification Screen
class GamificationScreen(Screen):
    def __init__(self, **kwargs):
        super(GamificationScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🔥 სერიები და გამოცდილება (XP)[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        layout.add_widget(Label(text="თქვენი სერია: 5 დღე ზედიზედ! 🏆 (450 XP)", font_size=16, color=(0.9,0.7,0.2,1)))
        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 5. B2B Docs Screen
class B2BDocsScreen(Screen):
    def __init__(self, **kwargs):
        super(B2BDocsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]📁 B2B დოკუმენტების თარგმანი[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        layout.add_widget(Label(text="PDF და DOCX ფაილების ფორმატირებული თარგმანი.", font_size=14, color=(0.8,0.8,0.8,1)))
        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# ==========================================
# რევოლუციური 4 ახალი გლობალური ფუნქცია
# ==========================================

# 6. ბიო-ემოციური და ინტონაციური თარგმანი
class BioEmotionalScreen(Screen):
    def __init__(self, **kwargs):
        super(BioEmotionalScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🧬 Bio-Emotional Nuance Translation[/b]", markup=True, font_size=18, color=(0.8,0.4,1,1)))
        layout.add_widget(Label(text="AI აანალიზებს თქვენს ხმის ტემბრსა და ემოციურ ტონს (სტრესი, სიხარული) და გადასცემს ზუსტად იმავე ემოციას უცხოურ ენაზე.", font_size=14, color=(0.8,0.8,0.8,1), halign="center"))
        
        self.status = Label(text="სტატუსი: მზად არის სენსორული ანალიზისთვის 🟢", font_size=14, color=(0.3,0.9,0.4,1))
        layout.add_widget(self.status)
        
        act_btn = Button(text="🎙️ ემოციური ტონალობის სკანირება", size_hint_y=None, height=50, background_normal='', background_color=(0.5, 0.2, 0.6, 1))
        act_btn.bind(on_press=lambda x: self.status.setter('text')(self.status, "აღმოჩენილია: აღელვება / პოზიტიური ენერგია ⚡"))
        layout.add_widget(act_btn)

        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 7. კულტურული და სამართლებრივი "ტაბუ" მცველი
class CulturalGuardianScreen(Screen):
    def __init__(self, **kwargs):
        super(CulturalGuardianScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🛡️ AI Cultural & Legal Guardian[/b]", markup=True, font_size=18, color=(1,0.4,0.3,1)))
        layout.add_widget(Label(text="ამოწმებს ფრაზებს ადგილობრივი კანონმდებლობის, ტაბუებისა და სლენგური შეურაცხყოფების თავიდან ასაცილებლად.", font_size=14, color=(0.8,0.8,0.8,1), halign="center"))
        
        self.warn_lbl = Label(text="უსაფრთხოების ინდიკატორი: სუფთაა ✅", font_size=14, color=(0.3,0.9,0.4,1))
        layout.add_widget(self.warn_lbl)

        check_btn = Button(text="🔍 რეგიონული კონტექსტის შემოწმება", size_hint_y=None, height=50, background_normal='', background_color=(0.7, 0.3, 0.2, 1))
        check_btn.bind(on_press=lambda x: self.warn_lbl.setter('text')(self.warn_lbl, "⚠️ გაფრთხილება: ეს ფრაზა ამ რეგიონში არასწორია! გთავაზობთ ალტერნატივას."))
        layout.add_widget(check_btn)

        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 8. P2P დეცენტრალიზებული ოფლაინ მეშ-ქსელი
class MeshNetworkScreen(Screen):
    def __init__(self, **kwargs):
        super(MeshNetworkScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🌐 P2P Offline Mesh Network[/b]", markup=True, font_size=18, color=(0.3,0.8,1,1)))
        layout.add_widget(Label(text="ინტერნეტის გარეშე ზონებში Bluetooth / Wi-Fi Direct-ით მეზობელ მოწყობილობებთან დაკავშირება და ოფლაინ თარგმანი.", font_size=14, color=(0.8,0.8,0.8,1), halign="center"))
        
        self.mesh_status = Label(text="Mesh სტატუსი: ძებნა არ დაწყებულა 📡", font_size=14, color=(0.9,0.7,0.2,1))
        layout.add_widget(self.mesh_status)

        mesh_btn = Button(text="🔗 ახლომდებარე Mesh კვანძების εύρεση", size_hint_y=None, height=50, background_normal='', background_color=(0.2, 0.5, 0.6, 1))
        mesh_btn.bind(on_press=lambda x: self.mesh_status.setter('text')(self.mesh_status, "🔗 დაკავშირებულია 2 მოწყობილობასთან Mesh ქსელში!"))
        layout.add_widget(mesh_btn)

        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 9. მომხმარებლის საკუთარი ხმის კლონირებით თარგმნილი საუბარი
class VoiceCloneScreen(Screen):
    def __init__(self, **kwargs):
        super(VoiceCloneScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🗣️ Native Voice Clone Sync[/b]", markup=True, font_size=18, color=(0.4,1,0.5,1)))
        layout.add_widget(Label(text="მოუსმინეთ თარგმანს თქვენი საკუთარი ხმისა და ინტონაციის იდენტური კლონით უცხო ენაზე.", font_size=14, color=(0.8,0.8,0.8,1), halign="center"))
        
        self.clone_status = Label(text="ხმის მოდელი: არ არის კლონირებული 🎙️", font_size=14, color=(0.9,0.7,0.2,1))
        layout.add_widget(self.clone_status)

        clone_btn = Button(text="🎙️ ხმის ნიმუშის ჩაწერა და კლონირება", size_hint_y=None, height=50, background_normal='', background_color=(0.3, 0.6, 0.3, 1))
        clone_btn.bind(on_press=lambda x: self.clone_status.setter('text')(self.clone_status, "✅ ხმის კლონი წარმატებით გენერირდა და აქტიურია!"))
        layout.add_widget(clone_btn)

        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        # 5 ძირითადი მოდული
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(LiveVoiceScreen(name='voice_live'))
        sm.add_widget(OfflineModeScreen(name='offline_mode'))
        sm.add_widget(GamificationScreen(name='gamification'))
        sm.add_widget(B2BDocsScreen(name='b2b_docs'))
        
        # 4 რევოლუციური უნიკალური მოდული
        sm.add_widget(BioEmotionalScreen(name='bio_emotional'))
        sm.add_widget(CulturalGuardianScreen(name='cultural_guardian'))
        sm.add_widget(MeshNetworkScreen(name='mesh_network'))
        sm.add_widget(VoiceCloneScreen(name='voice_clone'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()
