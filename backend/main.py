from plyer import camera

class MainScreen(Screen):
    # ... წინა კოდის გაგრძელება ...

    def open_ar_camera(self):
        """კამერის ჩართვა და ფოტოს გადაღება თარგმნისთვის"""
        if platform == 'android':
            try:
                # ფოტოს შენახვის დროებითი გზა
                import os
                photo_path = os.path.join(App.get_running_app().user_data_dir, "temp_ocr.jpg")
                camera.take_picture(filename=photo_path, on_complete=self.process_camera_image)
            except Exception as e:
                print(f"Camera Error: {e}")
        else:
            self.ids.output_text.text = "[კამერა ხელმისაწვდომია მხოლოდ Android მოწყობილობაზე]"

    def process_camera_image(self, image_path):
        """გადაღებული ფოტოს სერვერზე გაგზავნა OCR / თარგმნისთვის"""
        if not os.path.exists(image_path):
            return

        self.ids.output_text.text = "[მიმდინარეობს ფოტოს დამუშავება...]"
        
        # სერვერზე გაგზავნის ლოგიკა
        url = f"{VERCEL_BASE_URL}/api/ocr_translate"
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                data = {'source_lang': self.source_lang[:2], 'target_lang': self.target_lang[:2]}
                res = requests.post(url, files=files, data=data, timeout=20)
                if res.status_code == 200:
                    result = res.json()
                    translated_text = result.get('translated_text', '')
                    self.ids.output_text.text = translated_text
                else:
                    self.ids.output_text.text = "[ფოტოს თარგმნა ვერ მოხერხდა]"
        except Exception as e:
            self.ids.output_text.text = f"[შეცდომა: {e}]"
