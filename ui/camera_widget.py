import os
import base64
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.graphics import PushMatrix, PopMatrix, Rotate

class RotatedCameraWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera_obj = None
        self.is_active = False

    def start_camera(self):
        self.clear_widgets()
        self.camera_obj = Camera(play=True, resolution=(640, 480))
        
        # კამერის 90 გრადუსით გასწორება მობილურისთვის
        with self.canvas.before:
            PushMatrix()
            Rotate(angle=-90, origin=self.center)
        with self.canvas.after:
            PopMatrix()

        self.add_widget(self.camera_obj)
        self.is_active = True

    def stop_camera(self):
        if self.camera_obj:
            self.camera_obj.play = False
        self.clear_widgets()
        self.is_active = False

    def capture_frame_b64(self, user_dir):
        if not self.camera_obj or not self.camera_obj.texture:
            return None
        
        path = os.path.join(user_dir, "cam_snap.png") if user_dir else "cam_snap.png"
        self.camera_obj.texture.save(path)
        
        try:
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception:
            return None
