import os
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera  # <-- Kivy camera widget vaparnyasathi
from kivy.utils import platform

try:
    import config
    FONT_NAME = getattr(config, "GEORGIAN_FONT_NAME", getattr(config, "FONT_PATH", "Roboto"))
except ImportError:
    FONT_NAME = "Roboto"

try:
    from utils.translator import analyze_image_and_translate
except ImportError:
    analyze_image_and_translate = None


class RotatedCameraWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(RotatedCameraWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(10)

        self.status_label = Label(
            text="kamera chaloo ahe", 
            font_name=FONT_NAME, 
            size_hint_y=0.1,
            color=(1, 1, 1, 1)
        )
        self.add_widget(self.status_label)

        # Kivy-chi internal camera direct app-madhye dakhavanyasathi
        if platform == 'android':
            self.cam = Camera(play=True, resolution=(-1, -1), size_hint_y=0.7)
        else:
            self.cam = Label(text="[Kamera phakt Android var chalel]", font_name=FONT_NAME, size_hint_y=0.7)
        
        self.add_widget(self.cam)

        capture_btn = Button(
            text="📸 Photo Gheo Ani Translate Karo", 
            font_name=FONT_NAME,
            size_hint_y=0.2,
            background_color=(0.1, 0.6, 0.8, 1)
        )
        capture_btn.bind(on_press=self.capture_image)
        self.add_widget(capture_btn)

    def capture_image(self, instance):
        if platform == 'android' and hasattr(self.cam, 'export_to_png'):
            app = App.get_running_app()
            save_dir = app.user_data_dir if app else "."
            self.filepath = os.path.join(save_dir, "captured_image.jpg")
            
            # Kivy camera frame save karane
            self.cam.export_to_png(self.filepath)
            self.status_label.text = "Photo gheto..."
            Clock.schedule_once(lambda dt: self.process_image(self.filepath), 1)
        else:
            self.status_label.text = "Mock Mode: Test photo vaparat ahe."
            Clock.schedule_once(lambda dt: self.on_translation_result("Test text"), 1)

    def process_image(self, filepath):
        self.status_label.text = "Photo process hot ahe..."

        if analyze_image_and_translate:
            try:
                analyze_image_and_translate(
                    image_path=filepath, 
                    target_language="ka", 
                    callback=self.on_translation_result
                )
            except Exception as ex:
                print("Analyze execution error:", ex)
                self.on_translation_result("Server error.")
        else:
            self.on_translation_result("OCR purna zale.")

    def on_translation_result(self, result_text):
        def update_ui(dt):
            self.status_label.text = "Tayar!"
            res_str = str(result_text) if result_text else "Text olakhla nahi."
            
            content_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
            
            txt_output = TextInput(
                text=res_str, 
                font_name=FONT_NAME, 
                readonly=True, 
                multiline=True
            )
            content_box.add_widget(txt_output)
            
            close_btn = Button(
                text="Band Kara", 
                font_name=FONT_NAME, 
                size_hint_y=0.2,
                background_color=(0.8, 0.2, 0.2, 1)
            )
            
            popup = Popup(
                title="OCR Result", 
                title_font=FONT_NAME,
                content=content_box, 
                size_hint=(0.85, 0.6)
            )
            
            close_btn.bind(on_press=popup.dismiss)
            content_box.add_widget(close_btn)
            
            popup.open()

        Clock.schedule_once(update_ui)
