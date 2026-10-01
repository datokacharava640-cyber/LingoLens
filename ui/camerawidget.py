import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.clock import Clock
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass
    from android import mActivity
    
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    MediaStore = autoclass('android.provider.MediaStore')
    File = autoclass('java.io.File')
    FileProvider = autoclass('androidx.core.content.FileProvider')
    String = autoclass('java.lang.String')
    
    # უფლებების მოთხოვნა
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

class CameraWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.app = App.get_running_app()
        self.font = getattr(self.app, "GEORGIAN_FONT_NAME", "Roboto")
        self.img_path = ""

        # UI ელემენტები
        self.btn_capture = Button(text="კამერის გახსნა / Take Photo", font_name=self.font, size_hint=(1, 0.2))
        self.btn_capture.bind(on_press=self.open_camera)
        self.add_widget(self.btn_capture)

    def open_camera(self, instance):
        if platform == 'android':
            try:
                activity = PythonActivity.mActivity
                context = activity.getApplicationContext()
                
                # ვქმნით დროებით ფაილს გადაღებული სოტოსთვის
                output_dir = context.getExternalFilesDir(None)
                current_time = str(int(Clock.get_time() * 1000))
                self.img_path = os.path.join(output_dir.getAbsolutePath(), f"lingolens_{current_time}.jpg")
                
                file_obj = File(self.img_path)
                
                # FileProvider-ის გამოყენება უსაფრთხოებისთვის
                package_name = context.getPackageName()
                authority = f"{package_name}.fileprovider"
                uri = FileProvider.getUriForFile(context, authority, file_obj)
                
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                
                activity.startActivityForResult(intent, 1001)
            except Exception as e:
                print("Camera Open Error:", e)
        else:
            print("Camera is supported on Android platform.")

    def on_activity_result(self, requestCode, resultCode, intent):
        if requestCode == 1001:
            if os.path.exists(self.img_path):
                print("Photo captured successfully at:", self.img_path)
                # აქ შეგიძლიათ გადასცეთ self.img_path ფოტო OCR დამუშავების ფუნქციას
                if hasattr(self.app, "process_image"):
                    self.app.process_image(self.img_path)
