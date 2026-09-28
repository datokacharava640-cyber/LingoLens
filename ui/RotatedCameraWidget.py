import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.utils import platform

class RotatedCameraWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(RotatedCameraWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10

        # საწყისი შეტყობინება ან კამერა
        if platform == 'android':
            self.init_android_camera()
        else:
            self.init_desktop_camera()

    def init_android_camera(self):
        try:
            from jnius import autoclass
            # ვამოწმებთ ანდროიდის კამერის ხელმისაწვდომობას
            self.camera = Camera(play=True, resolution=(-1, -1))
            self.add_widget(self.camera)
            
            # გადაღების ღილაკი
            btn_layout = BoxLayout(size_hint_y=0.15, spacing=10)
            capture_btn = Button(text="📸 გადაღება")
            capture_btn.bind(on_press=self.capture_image)
            btn_layout.add_widget(capture_btn)
            self.add_widget(btn_layout)
            
        except Exception as e:
            print("Android Camera Init Error:", e)
            self.add_widget(Label(text=f"კამერის ჩართვის შეცდომა: {str(e)}"))

    def init_desktop_camera(self):
        try:
            self.camera = Camera(play=True, resolution=(-1, -1))
            self.add_widget(self.camera)
            
            capture_btn = Button(text="📸 გადაღება", size_hint_y=0.15)
            capture_btn.bind(on_press=self.capture_image)
            self.add_widget(capture_btn)
        except Exception as e:
            self.add_widget(Label(text="კამერა ვერ მოიძებნა ამ მოწყობილობაზე"))

    def capture_image(self, instance):
        if hasattr(self, 'camera') and self.camera:
            try:
                # ვინახავთ გადაღებულ სურათს დროებით ფაილად
                filepath = os.path.join(".", "captured_image.png")
                self.camera.export_to_png(filepath)
                print("Image captured successfully at:", filepath)
                
                # აქ შეგიძლია დაამატო სურათის გაგზავნა OCR / თარგმანისთვის
                if self.parent and hasattr(self.parent, 'parent'):
                    # თუ გსურს მთავარ ეკრანზე დაბრუნება ან ტექსტის ამოცნობა
                    pass
            except Exception as e:
                print("Capture error:", e)
