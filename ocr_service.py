import os
import threading
from kivy.clock import Clock
from translate_image import send_image_to_server_for_ocr

class OCRService:
    @staticmethod
    def recognize_image(image_path, callback=None):
        """
        სურათიდან ტექსტის ამოცნობის და თარგმნის სერვისი.
        მუშაობს ფონურ ნაკადში, რათა არ გაყინოს Kivy UI.
        """
        def background_task():
            try:
                if not os.path.exists(image_path):
                    result = {"success": False, "error": f"სურათი ვერ მოიძებნა: {image_path}"}
                else:
                    # ვიძახებთ სერვერულ ფუნქციას, რომელიც აგზავნის ფოტოს Hetzner სერვერზე
                    result = send_image_to_server_for_ocr(image_path)
            except Exception as e:
                result = {"success": False, "error": f"OCR შეცდომა: {str(e)}"}

            # შედეგს ვუბრუნებთ მთავარ UI ნაკადს უსაფრთხოდ
            if callback:
                Clock.schedule_once(lambda dt: callback(result), 0)

        # ფონური თრედის გაშვება აპლიკაციის დასაბლოკად
        threading.Thread(target=background_task, daemon=True).start()
