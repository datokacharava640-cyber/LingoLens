from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

# ეტაპობრივი ტესტი: ვამოწმებთ config-ს და ძირითად უტილიტებს
try:
    import config
    print("Config imported successfully")
except Exception as e:
    print("Config import error:", e)

try:
    from utils.translator import translate_text, analyze_image_and_translate
    print("Translator imported successfully")
except Exception as e:
    print("Translator import error:", e)

try:
    from utils.tts_engine import speak_text
    print("TTS imported successfully")
except Exception as e:
    print("TTS import error:", e)


class LingoLensDesktopApp(App):
    def build(self):
        root = FloatLayout()
        btn = Button(text="Imports Working!", size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        root.add_widget(btn)
        return root

if __name__ == "__main__":
    LingoLensDesktopApp().run()
