import os
import json
import threading
import urllib.request
import urllib.parse
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock


class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        self.font_path = 'font.ttf' if os.path.exists('font.ttf') else None

        # 1. სათაური
        lbl_kwargs = {'text': 'LingoLens AI Translation', 'font_size': '20sp', 'bold': True, 'size_hint_y': 0.12}
        if self.font_path:
            lbl_kwargs['font_name'] = self.font_path
        self.add_widget(Label(**lbl_kwargs))

        # 2. ტექსტის შეყვანა
        inp_kwargs = {'hint_text': 'ჩაწერეთ ტექსტი სათარგმნად...', 'font_size': '16sp', 'multiline': True, 'size_hint_y': 0.3}
        if self.font_path:
            inp_kwargs['font_name'] = self.font_path
        self.input_text = TextInput(**inp_kwargs)
        self.add_widget(self.input_text)

        # 3. ღილაკები
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.25)

        btn_ai_kwargs = {'text': '🧠 AI თარგმნა', 'background_color': (0.1, 0.5, 0.9, 1)}
        if self.font_path:
            btn_ai_kwargs['font_name'] = self.font_path
        btn_ai = Button(**btn_ai_kwargs)
        btn_ai.bind(on_press=self.start_translation)
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
        res_kwargs = {'text': 'LingoLens მზადაა სამუშაოდ.', 'font_size': '16sp', 'size_hint_y': 0.33}
        if self.font_path:
            res_kwargs['font_name'] = self.font_path
        self.result_label = Label(**res_kwargs)
        self.add_widget(self.result_label)

    def start_translation(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "გთხოვთ შეიყვანოთ ტექსტი!"
            return

        self.result_label.text = "მიმდინარეობს თარგმნა..."
        # ფონურ ნაკადში გაშვება, რომ UI არ გაიჭედოს
        threading.Thread(target=self._fetch_translation, args=(text,), daemon=True).start()

    def _fetch_translation(self, text):
        try:
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={encoded_text}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                translated = "".join([s[0] for s in data[0] if s[0]])
                Clock.schedule_once(lambda dt: self._update_result(f"თარგმანი:\n{translated}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_result(f"ხარვეზი: {e}"))

    def _update_result(self, text):
        self.result_label.text = text

    def voice_action(self, instance):
        self.result_label.text = "🎙️ ხმოვანი რეჟიმი აქტიურია."

    def camera_action(self, instance):
        self.result_label.text = "📷 კამერის რეჟიმი აქტიურია."

    def overlay_action(self, instance):
        self.result_label.text = "🪟 Overlay რეჟიმი აქტიურია."


class LingoLensApp(App):
    def build(self):
        return LingoLensUI()


if __name__ == '__main__':
    LingoLensApp().run()
