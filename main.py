import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button


class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        # შრიფტის შემოწმება
        self.font_path = 'font.ttf' if os.path.exists('font.ttf') else None

        # 1. სათაური
        title_kwargs = {'text': 'LingoLens AI Platform', 'font_size': '22sp', 'bold': True, 'size_hint_y': 0.15}
        if self.font_path:
            title_kwargs['font_name'] = self.font_path
        self.add_widget(Label(**title_kwargs))

        # 2. ტექსტის შეყვანა
        input_kwargs = {'hint_text': 'ჩაწერეთ ტექსტი...', 'font_size': '16sp', 'multiline': True, 'size_hint_y': 0.3}
        if self.font_path:
            input_kwargs['font_name'] = self.font_path
        self.input_text = TextInput(**input_kwargs)
        self.add_widget(self.input_text)

        # 3. ღილაკების პანელი
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.25)

        btn_ai_kwargs = {'text': '🧠 Smart AI', 'background_color': (0.1, 0.5, 0.9, 1)}
        if self.font_path:
            btn_ai_kwargs['font_name'] = self.font_path
        btn_ai = Button(**btn_ai_kwargs)
        btn_ai.bind(on_press=self.translate_action)
        grid.add_widget(btn_ai)

        btn_voice_kwargs = {'text': '🎙️ Voice', 'background_color': (0.1, 0.7, 0.3, 1)}
        if self.font_path:
            btn_voice_kwargs['font_name'] = self.font_path
        btn_voice = Button(**btn_voice_kwargs)
        grid.add_widget(btn_voice)

        btn_cam_kwargs = {'text': '📷 Camera', 'background_color': (0.9, 0.4, 0.1, 1)}
        if self.font_path:
            btn_cam_kwargs['font_name'] = self.font_path
        btn_cam = Button(**btn_cam_kwargs)
        grid.add_widget(btn_cam)

        btn_mode_kwargs = {'text': '🪟 Overlay', 'background_color': (0.6, 0.2, 0.8, 1)}
        if self.font_path:
            btn_mode_kwargs['font_name'] = self.font_path
        btn_mode = Button(**btn_mode_kwargs)
        grid.add_widget(btn_mode)

        self.add_widget(grid)

        # 4. შედეგის ზონა
        res_kwargs = {'text': 'LingoLens წარმატებით ჩაიტვირთა!', 'font_size': '16sp', 'size_hint_y': 0.3}
        if self.font_path:
            res_kwargs['font_name'] = self.font_path
        self.result_label = Label(**res_kwargs)
        self.add_widget(self.result_label)

    def translate_action(self, instance):
        text = self.input_text.text.strip()
        if text:
            self.result_label.text = f"ტექსტი მიღებულია: {text}"
        else:
            self.result_label.text = "გთხოვთ ჩაწეროთ ტექსტი!"


class LingoLensApp(App):
    def build(self):
        return LingoLensUI()


if __name__ == '__main__':
    LingoLensApp().run()
