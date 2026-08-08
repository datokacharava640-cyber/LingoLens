import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform
from kivy.clock import Clock


class LingoLensFullUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        # ქართული შრიფტის შემოწმება
        self.font_path = 'font.ttf' if os.path.exists('font.ttf') else None

        # 1. სათაური
        title_kwargs = {'text': 'LingoLens AI Translation', 'font_size': '20sp', 'bold': True, 'size_hint_y': 0.1}
        if self.font_path:
            title_kwargs['font_name'] = self.font_path
        self.add_widget(Label(**title_kwargs))

        # 2. ტექსტის შეყვანის ველი
        input_kwargs = {
            'hint_text': 'ჩაწერეთ ტექსტი სათარგმნად...',
            'font_size': '15sp',
            'multiline': True,
            'size_hint_y': 0.25
        }
        if self.font_path:
            input_kwargs['font_name'] = self.font_path
        self.input_text = TextInput(**input_kwargs)
        self.add_widget(self.input_text)

        # 3. ღილაკების პანელი (2x2)
        grid = GridLayout(cols=2, spacing=8, size_hint_y=0.3)

        btn_ai_kwargs = {'text': '🧠 AI თარგმანი', 'background_color': (0.1, 0.5, 0.9, 1)}
        if self.font_path:
            btn_ai_kwargs['font_name'] = self.font_path
        btn_ai = Button(**btn_ai_kwargs)
        btn_ai.bind(on_press=self.translate_text)
        grid.add_widget(btn_ai)

        btn_voice_kwargs = {'text': '🎙️ ხმოვანი რეჟიმი', 'background_color': (0.1, 0.7, 0.3, 1)}
        if self.font_path:
            btn_voice_kwargs['font_name'] = self.font_path
        btn_voice = Button(**btn_voice_kwargs)
        btn_voice.bind(on_press=self.voice_action)
        grid.add_widget(btn_voice)

        btn_cam_kwargs = {'text': '📷 კამერა / OCR', 'background_color': (0.9, 0.4, 0.1, 1)}
        if self.font_path:
            btn_cam_kwargs['font_name'] = self.font_path
        btn_cam = Button(**btn_cam_kwargs)
        btn_cam.bind(on_press=self.camera_action)
        grid.add_widget(btn_cam)

        btn_mode_kwargs = {'text': '🪟 Overlay რეჟიმი', 'background_color': (0.6, 0.2, 0.8, 1)}
        if self.font_path:
            btn_mode_kwargs['font_name'] = self.font_path
        btn_mode = Button(**btn_mode_kwargs)
        btn_mode.bind(on_press=self.overlay_action)
        grid.add_widget(btn_mode)

        self.add_widget(grid)

        # 4. შედეგის გამოსატანი ზონა
        res_kwargs = {'text': 'LingoLens მზადაა სამუშაოდ.', 'font_size': '16sp', 'size_hint_y': 0.35}
        if self.font_path:
            res_kwargs['font_name'] = self.font_path
        self.result_label = Label(**res_kwargs)
        self.add_widget(self.result_label)

    def translate_text(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "გთხოვთ შეიყვანოთ ტექსტი!"
            return

        self.result_label.text = "მიმდინარეობს თარგმნა..."

        try:
            import requests
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={text}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                translated = "".join([s[0] for s in res.json()[0] if s[0]])
                self.result_label.text = f"თარგმანი:\n{translated}"
            else:
                self.result_label.text = f"სერვერის ხარვეზი: {res.status_code}"
        except Exception as e:
            self.result_label.text = f"შეცდომა: {e}"

    def voice_action(self, instance):
        self.result_label.text = "🎙️ ხმოვანი რეჟიმი აქტიურია."

    def camera_action(self, instance):
        self.result_label.text = "📷 კამერის რეჟიმი აქტიურია."

    def overlay_action(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')

                activity = PythonActivity.mActivity
                if not Settings.canDrawOverlays(activity):
                    self.result_label.text = "გთხოვთ დაადასტუროთ Overlay ნებართვა..."
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    self.result_label.text = "🪟 Overlay რეჟიმი ჩართულია!"
            except Exception as e:
                self.result_label.text = f"Overlay ხარვეზი: {e}"
        else:
            self.result_label.text = "Overlay რეჟიმი მზადაა."


class LingoLensApp(App):
    def build(self):
        return LingoLensFullAI()

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.safe_request_permissions, 1.5)

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
    LingoLensApp().run()
