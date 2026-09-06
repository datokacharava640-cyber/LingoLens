import os
import threading
import requests
from plyer import camera
from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform

# Android ნებართვების მოთხოვნა (მხოლოდ Android-ზე)
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])


class MainScreen(Screen):
    # ... წინა კოდის გაგრძელება ...

    def open_ar_camera(self):
        """კამერის ჩართვა და ფოტოს გადაღება თარგმნისთვის"""
        if platform == 'android':
            try:
                app = App.get_running_app()
                photo_path = os.path.join(app.user_data_dir, "temp_ocr.jpg")
                camera.take_picture(filename=photo_path, on_complete=self.process_camera_image)
            except Exception as e:
                print(f"Camera Error: {e}")
                self.ids.output_text.text = f"[კამერის შეცდომა: {e}]"
        else:
            self.ids.output_text.text = "[კამერა ხელმისაწვდომია მხოლოდ Android მოწყობილობაზე]"

    def process_camera_image(self, image_path):
        """გადაღებული ფოტოს დამუშავება ცალკე ნაკადში (Async Thread)"""
        if not os.path.exists(image_path):
            return

        # UI-ს უსაფრთხო განახლება მთავარ ნაკადში
        Clock.schedule_once(lambda dt: setattr(self.ids.output_text, 'text', "[მიმდინარეობს ფოტოს დამუშავება...]"), 0)

        # სერვერზე გაგზავნის ფონური ლოგიკა
        def _upload_and_translate():
            url = f"{VERCEL_BASE_URL}/api/ocr_translate"
            try:
                with open(image_path, 'rb') as f:
                    files = {'file': f}
                    data = {
                        'source_lang': self.source_lang[:2],
                        'target_lang': self.target_lang[:2]
                    }
                    res = requests.post(url, files=files, data=data, timeout=25)

                if res.status_code == 200:
                    result = res.json()
                    translated_text = result.get('translated_text', '')
                    original_text = result.get('original_text', '')

                    # UI-ს განახლება და ისტორიაში შენახვა
                    Clock.schedule_once(lambda dt: self._update_ocr_ui(original_text, translated_text), 0)
                else:
                    Clock.schedule_once(lambda dt: setattr(self.ids.output_text, 'text', "[ფოტოს თარგმნა ვერ მოხერხდა]"), 0)

            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(self.ids.output_text, 'text', f"[შეცდომა: {e}]"), 0)

        threading.Thread(target=_upload_and_translate, daemon=True).start()

    def _update_ocr_ui(self, original_text, translated_text):
        if original_text:
            self.ids.input_text.text = original_text
        self.ids.output_text.text = translated_text
        
        # ბაზაში შენახვა
        db.add_history(self.source_lang, self.target_lang, original_text, translated_text)
