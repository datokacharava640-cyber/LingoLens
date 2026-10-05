import threading
from kivy.clock import Clock

# ... შენი სხვა კოდი OcrScreen-ში ...

    def run_ocr(self, instance):
        self.ocr_result.text = "მიმდინარეობს სურათის დამუშავება და ტექსტის ამოცნობა..."
        
        # ვუშვებთ ფონურ ნაკადში, რომ აპმა არ გაჭედოს
        threading.Thread(target=self._process_ocr_background).start()

    def _process_ocr_background(self):
        try:
            if OCRService:
                result_text = OCRService.recognize_image("test_image.jpg")
            else:
                result_text = "OCR სერვისი არ არის მიერთებული."
        except Exception as e:
            result_text = f"OCR შეცდომა: {str(e)}"
            
        # UI-ს განახლება მთავარ ნაკადში (Kivy-ს მოთხოვნა)
        Clock.schedule_once(lambda dt: self.update_ocr_ui(result_text), 0)

    def update_ocr_ui(self, result_text):
        self.ocr_result.text = result_text
