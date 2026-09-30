# ==============================================================================
# LingoLens AI - Rotated Camera Widget Module (Fully Completed)
# ==============================================================================

import os
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.utils import platform

# უსაფრთხო კონფიგურაციის და შრიფტის ჩატვირთვა
try:
    import config
    FONT_NAME = getattr(config, "GEORGIAN_FONT_NAME", getattr(config, "FONT_PATH", "Roboto"))
except ImportError:
    FONT_NAME = "Roboto"

# სურათის გადამგზავნი და მთარგმნელი ფუნქციის იმპორტი
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

        # სტატუსის ტექსტი (მაგ: მუშავდება...)
        self.status_label = Label(
            text="", 
            font_name=FONT_NAME, 
            size_hint_y=0.08,
            color=(1, 1, 1, 1)
        )
        self.add_widget(self.status_label)

        # კამერის ინიციალიზაცია პლატფორმის მიხედვით
        if platform == 'android':
            self.init_android_camera()
        else:
            self.init_desktop_camera()

    def init_android_camera(self):
        try:
            self.camera = Camera(play=True, resolution=(-1, -1))
            self.add_widget(self.camera)
            
            # გადაღების ღილაკი
            btn_layout = BoxLayout(size_hint_y=0.15, spacing=dp(10))
            capture_btn = Button(
                text="📸 გადაღება და თარგმნა", 
                font_name=FONT_NAME,
                background_color=(0.1, 0.6, 0.8, 1)
            )
            capture_btn.bind(on_press=self.capture_image)
            btn_layout.add_widget(capture_btn)
            self.add_widget(btn_layout)
            
        except Exception as e:
            print("Android Camera Init Error:", e)
            self.add_widget(Label(text=f"კამერის ჩართვის შეცდომა: {str(e)}", font_name=FONT_NAME))

    def init_desktop_camera(self):
        try:
            self.camera = Camera(play=True, resolution=(-1, -1))
            self.add_widget(self.camera)
            
            capture_btn = Button(
                text="📸 გადაღება და თარგმნა", 
                font_name=FONT_NAME, 
                size_hint_y=0.15,
                background_color=(0.1, 0.6, 0.8, 1)
            )
            capture_btn.bind(on_press=self.capture_image)
            self.add_widget(capture_btn)
        except Exception as e:
            self.add_widget(Label(text="კამერა ვერ მოიძებნა ამ მოწყობილობაზე", font_name=FONT_NAME))

    def capture_image(self, instance):
        if hasattr(self, 'camera') and self.camera:
            try:
                # ვიყენებთ აპლიკაციის უსაფრთხო სამუშაო დირექტორიას (user_data_dir)
                app = App.get_running_app()
                save_dir = app.user_data_dir if app else "."
                filepath = os.path.join(save_dir, "captured_image.jpg")
                
                # Kivy შიდა მეთოდით ვინახავთ სურათს
                self.camera.export_to_png(filepath)
                print("Image captured successfully at:", filepath)
                
                self.status_label.text = "მუშავდება სურათი და ითარგმნება..."

                # სერვერზე გაგზავნა, თუ ფუნქცია ხელმისაწვდომია
                if analyze_image_and_translate:
                    analyze_image_and_translate(
                        image_path=filepath, 
                        target_language="ka", 
                        callback=self.on_translation_result
                    )
                else:
                    # სარეზერვო იმიტაცია, თუ სერვერის მოდული ჯერ ბოლომდე მიბმული არ არის
                    Clock.schedule_once(lambda dt: self.on_translation_result("OCR მოდული დაკავშირებას მოითხოვს (Mock Result)"))

            except Exception as e:
                print("Capture error:", e)
                self.status_label.text = "შეცდომა გადაღებისას!"

    def on_translation_result(self, result_text):
        """სერვერიდან დაბრუნებული თარგმანის დამუშავება და ეკრანზე გამოტანა Popup-ით"""
        def update_ui(dt):
            self.status_label.text = ""
            res_str = str(result_text) if result_text else "ვერ მოხერხდა ტექსტის ამოცნობა."
            
            # ვქმნით პოპაპს ნათარგმნი ტექსტის გამოსატანად
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

        # UI-ს განახლება უსაფრთხოდ მიმდინარე ნაკადიდან (Thread-იდან) Clock-ის გამოყენებით
        Clock.schedule_once(update_ui)
