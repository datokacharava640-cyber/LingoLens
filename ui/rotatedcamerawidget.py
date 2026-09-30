import os
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
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
        self.spacing = dp(15)
        self.padding = dp(15)

        # სტატუსის ტექსტი
        self.status_label = Label(
            text="კამერის ჩართვა...", 
            font_name=FONT_NAME, 
            size_hint_y=0.1,
            color=(1, 1, 1, 1)
        )
        self.add_widget(self.status_label)

        # ვქმნით Kivy-ს ჩაშენებულ კამერას, რომ უსაფრთხოდ გამოჩნდეს ეკრანზე
        try:
            self.cam = Camera(resolution=(640, 480), play=True)
            self.add_widget(self.cam)
        except Exception as e:
            print("Camera Widget Error:", e)
            self.status_label.text = f"კამერის შეცდომა: {e}"
            self.cam = None

        # გადაღების ღილაკი
        capture_btn = Button(
            text="📸 ფოტოს გადაღება", 
            font_name=FONT_NAME,
            size_hint_y=0.15,
            background_color=(0.1, 0.6, 0.8, 1)
        )
        capture_btn.bind(on_press=self.capture_image)
        self.add_widget(capture_btn)

        # ნებართვების მოთხოვნა
        self.request_permissions()

    def request_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA, 
                    Permission.WRITE_EXTERNAL_STORAGE, 
                    Permission.READ_EXTERNAL_STORAGE
                ])
                self.status_label.text = "დააჭირეთ გადაღების ღილაკს"
            except Exception as e:
                print("Permission Error:", e)
                self.status_label.text = "ნებართვის შეცდომა"
        else:
            self.status_label.text = "კომპიუტერის რეჟიმი (Mock Camera)"

    def capture_image(self, instance):
        if platform == 'android' and self.cam:
            try:
                app = App.get_running_app()
                save_dir = app.user_data_dir if app else "."
                self.filepath = os.path.join(save_dir, "captured_image.jpg")
                
                # ვიღებთ კამერის მიმდინარე კადრს და ვინახავთ ფაილად
                self.cam.export_to_png(self.filepath)
                self.status_label.text = "სურათი გადაღებულია, მუშავდება..."
                print("Captured to:", self.filepath)
                
                Clock.schedule_once(lambda dt: self.process_image(self.filepath), 0.5)
            except Exception as e:
                print("Capture Error:", e)
                self.status_label.text = f"გადაღების შეცდომა: {e}"
        else:
            # კომპიუტერზე ტესტირებისთვის
            self.status_label.text = "სატესტო სურათი დამუშავდა"
            Clock.schedule_once(lambda dt: self.on_translation_result("სატესტო ტექსტი კამერიდან"), 1)

    def process_image(self, filepath):
        if filepath and os.path.exists(filepath):
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
                self.on_translation_result("OCR მოდული წარმატებით დაუკავშირდა (Mock Result)")
        else:
            self.status_label.text = "ფაილი ვერ მოიძებნა."

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
