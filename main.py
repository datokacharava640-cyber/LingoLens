import traceback
import sys

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

class LingoLensApp(App):
    def build(self):
        self.title = 'LingoLens'
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        title_label = Label(
            text='LingoLens Test',
            font_size='20sp',
            size_hint_y=None,
            height=50
        )
        main_layout.add_widget(title_label)
        
        self.input_text = TextInput(
            hint_text='Enter text here...',
            multiline=True,
            size_hint_y=0.4,
            font_size='16sp'
        )
        main_layout.add_widget(self.input_text)
        
        btn = Button(
            text='Test Button',
            size_hint_y=None,
            height=50
        )
        btn.bind(on_press=self.on_btn_click)
        main_layout.add_widget(btn)
        
        scroll = ScrollView(size_hint_y=0.4)
        self.result_label = Label(
            text='App Status: OK',
            font_size='14sp',
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        self.result_label.bind(texture_size=self._update_label_size)
        scroll.add_widget(self.result_label)
        main_layout.add_widget(scroll)
        
        return main_layout

    def _update_label_size(self, instance, value):
        instance.height = max(value[1], 200)
        instance.text_size = (instance.width, None)

    def on_btn_click(self, instance):
        self.result_label.text = "Button clicked! Everything works."

if __name__ == '__main__':
    try:
        LingoLensApp().run()
    except Exception as e:
        # თუ აპლიკაცია ფატალურ შეცდომას დაუშვებს, დაბეჭდავს ტექსტს
        print("CRASH DETECTED:")
        print(traceback.format_exc())
