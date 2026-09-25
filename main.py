from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

import config
from utils.translator import translate_text, analyze_image_and_translate
from utils.tts_engine import speak_text

# სათითაო ტესტი UI ფაილებისთვის
ui_status = "UI Status: "

try:
    from ui.window_manager import MovableWindow
    ui_status += "Window OK | "
except Exception as e:
    ui_status += "Window ERROR | "
    print("MovableWindow error:", e)

try:
    from ui.dialogue_window import DialogueWidget
    ui_status += "Dialogue OK | "
except Exception as e:
    ui_status += "Dialogue ERROR | "
    print("DialogueWidget error:", e)

try:
    from ui.camera_widget import CameraWidget
    ui_status += "Camera OK"
except Exception as e:
    ui_status += "Camera ERROR"
    print("CameraWidget error:", e)


class LingoLensDesktopApp(App):
    def build(self):
        root = FloatLayout()
        btn = Button(text=ui_status, font_size=12, size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        root.add_widget(btn)
        return root

if __name__ == "__main__":
    LingoLensDesktopApp().run()
