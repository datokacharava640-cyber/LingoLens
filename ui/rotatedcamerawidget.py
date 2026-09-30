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
        self.show_main_menu()

    def show_main_menu(self):
        self.clear_widgets()
        
        self.status_label = Label(
            text="LingoLens - აირჩიეთ რეჟიმი", 
            font_name=FONT_NAME, 
            size_hint_y=0.2,
            color=(1, 1, 1, 1)
        )
        self.add_widget(self.status_label)

        # ლაივ კამერის ღილაკი
        live_btn = Button(
            text="📸 ლაივ კამერით გადაღება", 
            font_name=FONT_NAME,
            size_hint_y=0.3,
            background_color=(0.1, 0.6, 0.8, 1)
        )
        live_btn.bind(on_press=self.open_live_camera)
        self.add_widget(live_btn)

        # გალერეიდან არჩევის ღილაკი
        gallery_btn = Button(
            text="📁 გალერეიდან არჩევა", 
            font_name=FONT_NAME,
            size_hint_y=0.3,
            background_color=(0.2, 0.7, 0.4, 1)
        )
        gallery_btn.bind(on_press=self.open_gallery)
        self.add_widget(gallery_btn)

    def open_live_camera(self, instance):
        self.clear_widgets()
        
        # უკან მენიუში დასაბრუნებელი ღილაკი
        back_btn = Button(
            text="⬅️ უკან მენიუში", 
            font_name=FONT_NAME,
            size_hint_y=0.1,
            background_color=(0.8, 0.3, 0.3, 1)
        )
        back_btn.bind(on_press=lambda x: self.show_main_menu())
        self.add_widget(back_btn)

        # Kivy შიდა კამერის ვიჯეტი (არ იწვევს შავ ეკრანს და მუშაობს აპის შიგნით)
        if platform == 'android':
            self.cam = Camera(play=True, resolution=(-1, -1), size_hint_y=0.7)
        else:
            self.cam = Label(text="[ლაივ კამერა მუშაობს მხოლოდ ანდროიდზე]", font_name=FONT_NAME, size_hint_y=0.7)
        
        self.add_widget(self.cam)

        # გადაღების ღილაკი ლაივ რეჟიმში
        capture_btn = Button(
            text="🔴 ფოტოს გადაღება", 
            font_name=FONT_NAME,
            size_hint_y=0.2,
            background_color=(0.9, 0.2, 0.2, 1)
        )
        capture_btn.bind(on_press=self.capture_live_image)
        self.add_widget(capture_btn)

    def capture_live_image(self, instance):
        if platform == 'android' and hasattr(self.cam, 'export_to_png'):
            app = App.get_running_app()
            save_dir = app.user_data_dir if app else "."
            self.filepath = os.path.join(save_dir, "captured_image.jpg")
            
            # კამერის კადრის ფაილად შენახვა
            self.cam.export_to_png(self.filepath)
            self.process_image(self.filepath)
        else:
            # კომპიუტერზე ტესტირებისთვის
            self.process_image(None)

    def open_gallery(self, instance):
        if platform == "android":
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")
                
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("image/*")
                activity = PythonActivity.mActivity
                activity.startActivity(intent)
            except Exception as e:
                print("Gallery Error:", e)
        else:
            self.process_image("mock_image.jpg")

    def process_image(self, filepath):
        self.clear_widgets()
        
        loading_label = Label(
            text="სურათი მუშავდება და ითარგმნება...", 
            font_name=FONT_NAME,
            color=(1, 1, 1, 1)
        )
        self.add_widget(loading_label)

        if analyze_image_and_translate and filepath and os.path.exists(filepath):
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
            # სატესტო პასუხი თუ მოდული არ არის ჩართული
            Clock.schedule_once(lambda dt: self.on_translation_result("წარმატებული ტესტური თარგმანი (LingoLens)"), 1)

    def on_translation_result(self, result_text):
        def update_ui(dt):
            self.show_main_menu()
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
                title="LingoLens - თარგმანის შედეგი", 
                title_font=FONT_NAME,
                content=content_box, 
                size_hint=(0.85, 0.6)
            )
            
            close_btn.bind(on_press=popup.dismiss)
            content_box.add_widget(close_btn)
            
            popup.open()

        Clock.schedule_once(update_ui)
