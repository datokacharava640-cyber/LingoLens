import os
import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform
from kivy.clock import Clock


class LingoLensFullAI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        # უსაფრთხო შრიფტი
        self.font_path = 'font.ttf' if os.path.exists('font.ttf') else None

        # სათაური
        self.title_label = Label(
            text='LingoLens AI Platform',
            font_size='20sp',
            bold=True,
            size_hint_y=0.1
        )
        if self.font_path:
            self.title_label.font_name = self.font_path
        self.add_widget(self.title_label)

        # ტექსტის შეყვანა
        self.input_text = TextInput(
            hint_text='ჩაწერეთ ტექსტი...',
            font_size='16sp',
            multiline=True,
            size_hint_y=0.25
        )
        if self.font_path:
            self.input_text.font_name = self.font_path
        self.add_widget(self.input_text)

        # 4 მთავარი ღილაკი
        grid = GridLayout(cols=2, spacing=8, size_hint_y=0.3)

        btn_ai = Button(text='🧠 Smart AI Translate', background_color=(0.1, 0.5, 0.9, 1))
        if self.font_path:
            btn_ai.font_name = self.font_path
        btn_ai.bind(on_press=self.run_smart_ai_translation)
        grid.add_widget(btn_ai)

        btn_voice = Button(text='🎙️ Real-Time Voice', background_color=(0.1, 0.7, 0.3, 1))
        if self.font_path:
            btn_voice.font_name = self.font_path
        btn_voice.bind(on_press=self.run_voice_stream)
        grid.add_widget(btn_voice)

        btn_cam = Button(text='📷 Camera OCR', background_color=(0.9, 0.4, 0.1, 1))
        if self.font_path:
            btn_cam.font_name = self.font_path
        btn_cam.bind(on_press=self.run_camera_ocr)
        grid.add_widget(btn_cam)

        btn_overlay = Button(text='🪟 Overlay Mode', background_color=(0.6, 0.2, 0.8, 1))
        if self.font_path:
            btn_overlay.font_name = self.font_path
        btn_overlay.bind(on_press=self.toggle_overlay_permission)
        grid.add_widget(btn_overlay)

        self.add_widget(grid)

        # შედეგის გამოსატანი ზონა
        self.result_label = Label(
            text='LingoLens მზადაა.',
            font_size='16sp',
            size_hint_y=0.35
        )
        if self.font_path:
            self.result_label.font_name = self.font_path
        self.add_widget(self.result_label)

    def run_smart_ai_translation(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = 'გთხოვთ შეიყვანოთ ტექსტი!'
            return

        self.result_label.text = 'AI ითარგმნება...'
        
        try:
            import requests
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={text}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                translated = "".join([sentence[0] for sentence in response.json()[0] if sentence[0]])
                self.result_label.text = f"თარგმანი:\n{translated}"
            else:
                self.result_label.text = f'სერვერის შეცდომა: {response.status_code}'
        except Exception as e:
            self.result_label.text = f'ინტერნეტის ხარვეზი: {e}'

    def run_voice_stream(self, instance):
        self.result_label.text = '🎙️ ხმოვანი რეჟიმი აქტიურია.'

    def run_camera_ocr(self, instance):
        self.result_label.text = '📷 კამერის რეჟიმი აქტიურია.'

    def toggle_overlay_permission(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                
                activity = PythonActivity.mActivity
                if not Settings.canDrawOverlays(activity):
                    self.result_label.text = 'გთხოვთ დაადასტუროთ Overlay ნებართვა...'
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    self.result_label.text = '🪟 Overlay Mode ჩართულია!'
            except Exception as e:
                self.result_label.text = f"Overlay ხარვეზი: {e}"
        else:
            self.result_label.text = 'Overlay რეჟიმი მზადაა.'


class LingoLensApp(App):
    def build(self):
        try:
            return LingoLensFullAI()
        except Exception as e:
            box = BoxLayout(orientation='vertical', padding=20)
            err_label = Label(text=f"ჩატვირთვის შეცდომა:\n{e}\n\n{traceback.format_exc()}")
            box.add_widget(err_label)
            return box

    def on_start(self):
        # UI-ს გამოჩენიდან 1 წამში უსაფრთხოდ ითხოვს ნებართვებს
        if platform == 'android':
            Clock.schedule_once(self.safe_request_permissions, 1.0)

    def safe_request_permissions(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.CAMERA,
                Permission.RECORD_AUDIO
            ])
        except Exception as e:
            print(f"Permissions Error: {e}")


if __name__ == '__main__':
    try:
        LingoLensApp().run()
    except Exception as e:
        print(f"Fatal App Crash: {e}")
