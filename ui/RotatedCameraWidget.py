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
        
        # ვიზუალური სტრუქტურა: ზემოთ კამერა, ქვემოთ ღილაკი და შედეგების ველი
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
        
        # კამერის გაშვებამდე ვამოწმებთ ანდროიდის ნებართვებს
        Clock.schedule_once(lambda dt: self.check_permissions_and_start(), 0.5)

    def update_canvas(self, *args):
        self.rot.origin = self.center

    def check_permissions_and_start(self):
        # ანდროიდზე კამერის ნებართვის დინამიური მოთხოვნა
        try:
            from android.permissions import request_permissions, Permission
            def callback(permissions, results):
                if all(results):
                    self.start_camera()
                else:
                    self.result_label.text = "კამერის ნებართვა უარყოფილია!"
            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE], callback)
        except Exception:
            # თუ კომპიუტერზეა (Kivy desktop) ან არ არის android მოდული
            self.start_camera()

    def start_camera(self):
        self.camera_container.clear_widgets()
        try:
            # ვცდილობთ ჩავრთოთ კამერა (index=0 ძირითადი კამერისთვის)
            self.camera_obj = Camera(play=True, resolution=(640, 480), index=0)
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

    def trigger_capture_and_translate(self, instance):
        if not self.is_active or not self.camera_obj:
            self.result_label.text = "კამერა არ არის აქტიური!"
            return

        self.result_label.text = "⏳ მიმდინარეობს სურათის დამუშავება და თარგმნა..."
        
        # ვიღებთ აპლიკაციის დირექტორიას ფაილის შესანახად
        from kivy.app import App
        app = App.get_running_app()
        user_dir = app.user_data_dir if app else ""
        
        path = os.path.join(user_dir, "cam_snap.png") if user_dir else "cam_snap.png"
        
        try:
            # ვინახავთ მიმდინარე კადრს სურათის სახით
            if self.camera_obj.texture:
                self.camera_obj.texture.save(path)
            else:
                self.result_label.text = "კამერის ტექსტურა მიუწვდომელია."
                return
                
            if not os.path.exists(path):
                self.result_label.text = "ვერ მოხერხდა კადრის შენახვა."
                return

            # ვამოწმებთ სერვერთან დასაკავშირებელ მოდულს
            from utils.translator import analyze_image_and_translate
            
            def on_translation_result(res):
                def update_ui(dt):
                    if res:
                        self.result_label.text = f"თარგმანი: {res}"
                    else:
                        self.result_label.text = "სერვერიდან პასუხი ვერ მიიღო."
                Clock.schedule_once(update_ui)

            # ვუგზავნით შენახული სურათის ფაილის სრულ მისამართს (path)
            analyze_image_and_translate(path, target_lang="ka", callback=on_translation_result)
            
        except ImportError:
            self.result_label.text = "OCR / სურათის მთარგმნელი მოდული ვერ მოიძებნა."
        except Exception as e:
            self.result_label.text = f"შეცდომა: {str(e)}"

    def on_leave(self):
        self.stop_camera()
