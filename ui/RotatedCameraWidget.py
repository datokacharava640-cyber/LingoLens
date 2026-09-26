import os
import base64
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock

class RotatedCameraWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.camera_obj = None
        self.is_active = False
        
        # დინამიური როტაციის ცენტრისთვის
        with self.canvas.before:
            PushMatrix()
            self.rot = Rotate(angle=-90, origin=self.center)
        with self.canvas.after:
            PopMatrix()
            
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        
        # ვამზადებთ ვიზუალურ სტრუქტურას: ზემოთ კამერა, ქვემოთ ღილაკი და შედეგების ველი
        self.camera_container = BoxLayout(size_hint=(1, 0.75))
        self.add_widget(self.camera_container)
        
        # შედეგების და სტატუსის ველი
        self.result_label = Label(
            text="აირჩიეთ კადრი და დააჭირეთ გადაღებას", 
            size_hint=(1, 0.15),
            halign='center',
            valign='middle'
        )
        self.result_label.bind(size=self.result_label.setter('text_size'))
        self.add_widget(self.result_label)
        
        # გადაღების ღილაკი
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=5)
        self.capture_btn = Button(text="📸 გადაღება და თარგმნა", on_press=self.trigger_capture_and_translate)
        btn_layout.add_widget(self.capture_btn)
        self.add_widget(btn_layout)
        
        # ავტომატურად გავუშვათ კამერა გახსნისთანავე
        Clock.schedule_once(lambda dt: self.start_camera(), 0.5)

    def update_canvas(self, *args):
        self.rot.origin = self.center

    def start_camera(self):
        self.camera_container.clear_widgets()
        try:
            self.camera_obj = Camera(play=True, resolution=(640, 480))
            self.camera_container.add_widget(self.camera_obj)
            self.is_active = True
        except Exception as e:
            print("კამერის გაშვების შეცდომა:", e)
            self.result_label.text = f"კამერის შეცდომა: {e}"
            self.is_active = False

    def stop_camera(self):
        if self.camera_obj:
            try:
                self.camera_obj.play = False
            except Exception:
                pass
        self.camera_container.clear_widgets()
        self.is_active = False

    def capture_frame_b64(self, user_dir=""):
        if not self.camera_obj or not self.camera_obj.texture:
            return None
        
        try:
            path = os.path.join(user_dir, "cam_snap.png") if user_dir else "cam_snap.png"
            self.camera_obj.texture.save(path)
            
            if os.path.exists(path):
                with open(path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            print("კადრის შენახვის/გადაყვანის შეცდომა:", e)
            
        return None

    def trigger_capture_and_translate(self, instance):
        if not self.is_active or not self.camera_obj:
            self.result_label.text = "კამერა არ არის აქტიური!"
            return

        self.result_label.text = "⏳ მიმდინარეობს სურათის დამუშავება და თარგმნა..."
        
        # ვიღებთ აპლიკაციის ძირითად ინსტანციას user_data_dir-ის მისაღებად
        from kivy.app import App
        app = App.get_running_app()
        user_dir = app.user_data_dir if app else ""
        
        b64_data = self.capture_frame_b64(user_dir)
        if not b64_data:
            self.result_label.text = "ვერ მოხერხდა კადრის შენახვა."
            return

        # ვამოწმებთ არსებობს თუ არა სერვერთან დასაკავშირებელი ფუნქცია
        try:
            from utils.translator import analyze_image_and_translate
            
            def on_translation_result(res):
                def update_ui(dt):
                    if res:
                        self.result_label.text = f"თარგმანი: {res}"
                    else:
                        self.result_label.text = "სერვერიდან პასუხი ვერ მიიღო."
                Clock.schedule_once(update_ui)

            # ვუგზავნით სურათს ბაზისზე გადაყვანილ ფორმატში ანალიზისთვის
            # (გაითვალისწინეთ analyze_image_and_translate ფუნქციის არგუმენტები თქვენი სტრუქტურის მიხედვით)
            analyze_image_and_translate(b64_data, on_translation_result)
            
        except ImportError:
            self.result_label.text = "OCR / სურათის მთარგმნელი მოდული ვერ მოიძებნა."
        except Exception as e:
            self.result_label.text = f"შეცდომა: {str(e)}"

    def on_leave(self):
        # აუცილებლად ვთიშებთ კამერას როცა მომხმარებელი სხვა ეკრანზე გადადის
        self.stop_camera()
