import os
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.utils import platform

try:
    from plyer import camera
except ImportError:
    camera = None

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
        self.spacing = dp(20)
        self.padding = dp(20)

        self.status_label = Label(
            text="დააჭირეთ ღილაკს კამერის გასახსნელად", 
            font_name=FONT_NAME, 
            size_hint_y=0.2,
            color=(1, 1, 1, 1)
        )
        self.add_widget(self.status_label)

        capture_btn = Button(
            text="📸 კამერის გახსნა და გადაღება", 
            font_name=FONT_NAME,
            size_hint_y=0.3,
            background_color=(0.1, 0.6, 0.8, 1)
        )
        capture_btn.bind(on_press=self.open_camera)
        self.add_widget(capture_btn)

    def open_camera(self, instance):
        if platform == 'android':
            if camera:
                try:
                    app = App.get_running_app()
                    save_dir = app.user_data_dir if app else "."
                    self.filepath = os.path.join(save_dir, "captured_image.jpg")
                    
                    if os.path.exists(self.filepath):
                        os.remove(self.filepath)

                    self.status_label.text = "კამერა ირთვება..."
                    camera.take_picture(filename=self.filepath, on_complete=self.camera_callback)
                except Exception as e:
                    print("Plyer Camera Error:", e)
                    self.status_label.text = f"შეცდომა კამერის გაშვებისას: {str(e)}"
            else:
                self.status_label.text = "plyer ბიბლიოთეკა არ არის ხელმისაწვდომი!"
        else:
            self.status_label.text = "კამერა მუშაობს მხოლოდ ანდროიდ მოწყობილობაზე. (Mock Mode)"
            Clock.schedule_once(lambda dt: self.on_translation_result("სატესტო ტექსტი კომპიუტერიდან"), 1)

    def camera_callback(self, filepath):
        target_path = filepath if (filepath and os.path.exists(filepath)) else getattr(self, 'filepath', None)
        
        if target_path and os.path.exists(target_path):
            Clock.schedule_once(lambda dt: self.process_image(target_path))
        else:
            Clock.schedule_once(lambda dt: setattr(self.status_label, "text", "გადაღება ვერ მოხერხდა ან გაუქმდა."))

    def process_image(self, filepath):
        self.status_label.text = "სურათი მუშავდება და ითარგმნება..."

        if analyze_image_and_translate:
            try:
                analyze_image_and_translate(
                    image_path=filepath, 
                    target_language="ka", 
                    callback=self.on_translation_result
                )
            except Exception as ex:
                print("Analyze execution error:", ex)
                self.on_translation_result("სერვერზე გაგზავნის შეცდომა.")
        else:
            self.on_translation_result("OCR წარმატებით დასრულდა (მოდული არ არის)")

    def on_translation_result(self, result_text):
        def update_ui(dt):
            self.status_label.text = "მზადაა!"
            res_str = str(result_text) if result_text else "ვერ მოხერხდა ტექსტის ამოცნობა."
            
            content_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
            
            txt_output = TextInput(
                text=res_str, 
                font_name=FONT_NAME, 
                readonly=True, 
                multiline=True
            )
            content_box.add_widget(txt_output)
            
            close_btn = Button(
                text="დახურვა", 
                font_name=FONT_NAME, 
                size_hint_y=0.2,
                background_color=(0.8, 0.2, 0.2, 1)
            )
            
            popup = Popup(
                title="OCR თარგმანის შედეგი", 
                title_font=FONT_NAME,
                content=content_box, 
                size_hint=(0.85, 0.6)
            )
            
            close_btn.bind(on_press=popup.dismiss)
            content_box.add_widget(close_btn)
            
            popup.open()

        Clock.schedule_once(update_ui)
