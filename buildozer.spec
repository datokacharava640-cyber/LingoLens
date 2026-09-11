def on_start(self):
        try:
            from kivy.utils import platform
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                
                def callback(permissions, results):
                    if all(results):
                        Clock.schedule_once(lambda dt: self.enable_camera(), 0.5)

                request_permissions([
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.INTERNET,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ], callback)
            else:
                self.enable_camera()
        except Exception as e:
            print(f"[Permission Error]: {e}")

    def enable_camera(self):
        if hasattr(self, 'camera') and self.camera:
            self.camera.play = True
