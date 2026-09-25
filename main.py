from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

import config
from utils.translator import translate_text, analyze_image_and_translate
from utils.tts_engine import speak_text

try:
    from ui.window_manager import MovableWindow
    status_text = "MovableWindow: OK"
except Exception as e:
    status_text = f"MovableWindow: ERROR"
    print("Error:", e)

class LingoLensDesktopApp(App):
    def build(self):
        root = FloatLayout()
        btn = Button(text=status_text, size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        root.add_widget(btn)
        return root

if __name__ == "__main__":
    LingoLensDesktopApp().run()
