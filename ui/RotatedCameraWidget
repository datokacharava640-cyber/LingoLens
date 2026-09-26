import os
import base64
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock

class RotatedCameraWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera_obj = None
        self.is_active = False
        
        # დინამიური როტაციის ცენტრისთვის
        with self.canvas.before:
            PushMatrix()
            self.rot = Rotate(angle=-90, origin=self.center)
        with self.canvas.after:
            PopMatrix()
            
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.rot.origin = self.center

    def start_camera(self):
        # ვასუფთავებთ ძველებს უსაფრთხოდ
        self.clear_widgets()
        try:
            # Resolution შეგვიძლია მივცეთ უფრო თავსებადი, ან ამოვიღოთ რომ ავტომატურად აირჩიოს
            self.camera_obj = Camera(play=True, resolution=(640, 480))
            self.add_widget(self.camera_obj)
            self.is_active = True
        except Exception as e:
            print("კამერის გაშვების შეცდომა:", e)
            self.is_active = False

    def stop_camera(self):
        if self.camera_obj:
            try:
                self.camera_obj.play = False
            except Exception:
                pass
        self.clear_widgets()
        self.is_active = False

    def capture_frame_b64(self, user_dir):
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
