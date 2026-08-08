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

        # 1. სათაური (ინგლისურად, რომ არასდროს გაკვადრატდეს)
        self.add_widget(Label(
            text='LingoLens AI Translation',
            font_size='22sp',
            bold=True,
            size_hint_y=0.12
        ))

        # 2. ტექსტის შეყვანა
        self.input_text = TextInput(
            hint_text='Type text to translate here...',
            font_size='16sp',
            multiline=True,
            size_hint_y=0.3
        )
        self.add_widget(self.input_text)

        # 3. ღილაკების პანელი
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.25)

        btn_ai = Button(text='🧠 AI Translate', background_color=(0.1, 0.5, 0.9, 1))
        btn_ai.bind(on_press=self.start_translation)
        grid.add_widget(btn_ai)

        btn_voice = Button(text='🎙️ Voice Mode', background_color=(0.1, 0.7, 0.3, 1))
        btn_voice.bind(on_press=self.voice_action)
        grid.add_widget(btn_voice)

        btn_cam = Button(text='📷 Camera / OCR', background_color=(0.9, 0.4, 0.1, 1))
        btn_cam.bind(on_press=self.camera_action)
        grid.add_widget(btn_cam)

        btn_mode = Button(text='🪟 Overlay Mode', background_color=(0.6, 0.2, 0.8, 1))
        btn_mode.bind(on_press=self.overlay_action)
        grid.add_widget(btn_mode)

        self.add_widget(grid)

        # 4. შედეგი
        self.result_label = Label(
            text='LingoLens is ready to work.',
            font_size='16sp',
            size_hint_y=0.33
        )
        self.add_widget(self.result_label)

    def start_translation(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "Please enter some text!"
            return

        self.result_label.text = "Translating..."
        threading.Thread(target=self._fetch_translation, args=(text,), daemon=True).start()

    def _fetch_translation(self, text):
        try:
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={encoded_text}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                translated = "".join([s[0] for s in data[0] if s[0]])
                Clock.schedule_once(lambda dt: self._update_result(f"Translation:\n{translated}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_result(f"Error: {e}"))

    def _update_result(self, text):
        self.result_label.text = text

    def voice_action(self, instance):
        self.result_label.text = "Voice mode active."

    def camera_action(self, instance):
        self.result_label.text = "Camera mode active."

    def overlay_action(self, instance):
        self.result_label.text = "Overlay mode active."


class LingoLensApp(App):
    def build(self):
        return LingoLensUI()


if __name__ == '__main__':
    LingoLensApp().run()
