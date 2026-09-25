from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

# ვამოწმებთ ძირითადებს
import config
from utils.translator import translate_text, analyze_image_and_translate
from utils.tts_engine import speak_text

# ვამოწმებთ UI ფოლდერის იმპორტებს
try:
    from ui.window_manager import MovableWindow
    print("MovableWindow imported successfully")
except Exception as e:
    print("MovableWindow import error:", e)

try:
    from ui.dialogue_window import DialogueWidget
    print("DialogueWidget imported successfully")
except Exception as e:
    print("DialogueWidget import error:", e)

try:
    from ui.camera_widget import CameraWidget
    print("CameraWidget imported successfully")
except Exception as e:
    print("CameraWidget import error:", e)


class LingoLensDesktopApp(App):
    def build(self):
        root = FloatLayout()
        btn = Button(text="All UI Imports OK!", size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        root.add_widget(btn)
        return root

if __name__ == "__main__":
    LingoLensDesktopApp().run()
