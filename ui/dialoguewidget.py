from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.utils import platform
import config
from utils.translator import translate_text

# Android-ისთვის პერმიშენების უსაფრთხო შემოწმება
HAS_ANDROID_PERMISSIONS = False
if platform == "android":
    try:
        from android.permissions import request_permissions, Permission
        HAS_ANDROID_PERMISSIONS = True
    except ImportError:
        pass

# მიკროფონის (Speech-to-Text) უსაფრთხო იმპორტი plyer-იდან
stt = None
if platform == "android":
    try:
        from plyer import stt as plyer_stt
        stt = plyer_stt
    except ImportError:
        pass


class DialogueWidget(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(10), padding=dp(10), **kwargs)
        
        # უსაფრთხო ფონტის განსაზღვრა config-დან
        self.font = getattr(config, "GEORGIAN_FONT_NAME", getattr(config, "FONT_PATH", "Roboto"))
        
        # მხარდაჭერილი ენები config-დან ან სტანდარტული ლექსიკონით
        self.supported_langs = getattr(config, "SUPPORTED_LANGUAGES", {
            "ქართული": "ka",
            "English": "en",
            "Русский": "ru",
            "Español": "es"
        })
        lang_names = list(self.supported_langs.keys())

        # 1. ზედა ნაწილი: პიროვნება A
        top_box = BoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=0.42)
        
        header_a = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(35))
        header_a.add_widget(Label(text="👤 Person A", font_name=self.font, bold=True))
        
        self.sp_a = Spinner(
            text="English" if "English" in lang_names else lang_names[0],
            values=lang_names,
            font_name=self.font
        )
        header_a.add_widget(self.sp_a)
        top_box.add_widget(header_a)

        self.input_a = TextInput(
            hint_text="Type here / Speak...",
            font_name=self.font,
            multiline=True,
            size_hint_y=0.5,
        )
        self.output_a = TextInput(
            hint_text="Translation...",
            font_name=self.font,
            readonly=True,
            multiline=True,
            size_hint_y=0.5,
        )

        top_box.add_widget(self.input_a)
        top_box.add_widget(self.output_a)

        # A ადამიანის ღილაკები
        btn_box_a = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=None, height=dp(45))
        btn_mic_a = Button(text="🎤 Speak", font_name=self.font)
        btn_mic_a.bind(on_press=self.record_audio_a)
        
        btn_translate_a = Button(text="Translate ↓", font_name=self.font, background_color=(0.1, 0.6, 0.8, 1))
        btn_translate_a.bind(on_press=self.translate_a_to_b)
        
        btn_box_a.add_widget(btn_mic_a)
        btn_box_a.add_widget(btn_translate_a)

        # 2. ქვედა ნაწილი: პიროვნება B
        bottom_box = BoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=0.42)
        
        header_b = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(35))
        header_b.add_widget(Label(text="👤 Person B", font_name=self.font, bold=True))
        
        self.sp_b = Spinner(
            text="ქართული" if "ქართული" in lang_names else lang_names[-1],
            values=lang_names,
            font_name=self.font
        )
        header_b.add_widget(self.sp_b)
        bottom_box.add_widget(header_b)

        self.input_b = TextInput(
            hint_text="ჩაწერეთ აქ ან ისაუბრეთ...",
            font_name=self.font,
            multiline=True,
            size_hint_y=0.5,
        )
        self.output_b = TextInput(
            hint_text="თარგმანი...",
            font_name=self.font,
            readonly=True,
            multiline=True,
            size_hint_y=0.5,
        )

        bottom_box.add_widget(self.input_b)
        bottom_box.add_widget(self.output_b)

        # B ადამიანის ღილაკები
        btn_box_b = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=None, height=dp(45))
        btn_mic_b = Button(text="🎤 საუბარი", font_name=self.font)
        btn_mic_b.bind(on_press=self.record_audio_b)
        
        btn_translate_b = Button(text="Translate ↑", font_name=self.font, background_color=(0.1, 0.6, 0.8, 1))
        btn_translate_b.bind(on_press=self.translate_b_to_a)
        
        btn_box_b.add_widget(btn_mic_b)
        btn_box_b.add_widget(btn_translate_b)

        # სტრუქტურის აწყობა
        self.add_widget(top_box)
        self.add_widget(btn_box_a)
        self.add_widget(bottom_box)
        self.add_widget(btn_box_b)

        # მიკროფონის პერმიშენების უსაფრთხო მოთხოვნა
        self.request_mic_permission()

    def request_mic_permission(self):
        if HAS_ANDROID_PERMISSIONS:
            try:
                request_permissions([Permission.RECORD_AUDIO])
            except Exception as e:
                print("Permission Error:", e)

    def translate_a_to_b(self, instance):
        val = self.input_a.text.strip()
        if not val:
            return
        
        src_lang_name = self.sp_a.text
        target_lang_name = self.sp_b.text
        
        src_code = self.supported_langs.get(src_lang_name, "en")
        target_code = self.supported_langs.get(target_lang_name, "ka")
        
        prompt = f"Translate accurately from {src_lang_name} to {target_lang_name}: {val}"
        
        def on_result(res):
            res_text = str(res) if res else "Error"
            Clock.schedule_once(lambda dt: setattr(self.output_b, "text", res_text))

        try:
            translate_text(
                prompt=prompt,
                text=val,
                src_lang=src_code,
                target_lang=target_code,
                callback=on_result,
            )
        except Exception as e:
            print("Translation Error A->B:", e)

    def translate_b_to_a(self, instance):
        val = self.input_b.text.strip()
        if not val:
            return
            
        src_lang_name = self.sp_b.text
        target_lang_name = self.sp_a.text
        
        src_code = self.supported_langs.get(src_lang_name, "ka")
        target_code = self.supported_langs.get(target_lang_name, "en")
        
        prompt = f"Translate accurately from {src_lang_name} to {target_lang_name}: {val}"
        
        def on_result(res):
            res_text = str(res) if res else "Error"
            Clock.schedule_once(lambda dt: setattr(self.output_a, "text", res_text))

        try:
            translate_text(
                prompt=prompt,
                text=val,
                src_lang=src_code,
                target_lang=target_code,
                callback=on_result,
            )
        except Exception as e:
            print("Translation Error B->A:", e)

    def record_audio_a(self, instance):
        if stt:
            try:
                stt.speak = False # დაზღვევა
                stt.start()
            except Exception as e:
                self.input_a.text = f"მიკროფონის შეცდომა: {e}"
        else:
            self.input_a.text = "Speech-to-Text ხელმისაწვდომია მხოლოდ მობილურ აპლიკაციაში."

    def record_audio_b(self, instance):
        if stt:
            try:
                stt.speak = False
                stt.start()
            except Exception as e:
                self.input_b.text = f"მიკროფონის შეცდომა: {e}"
        else:
            self.input_b.text = "მიკროფონი ხელმისაწვდომია მობილურ აპლიკაციაში."
