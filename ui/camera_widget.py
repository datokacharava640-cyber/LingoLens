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
        
        # კამერის დატრიალება -90 გრადუსით სწორი პოზიციისთვის
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
