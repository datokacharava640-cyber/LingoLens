def request_permissions_on_demand(self, callback_func):
        if platform == "android":
            try:
                from android.permissions import Permission, request_permissions
                perms = [
                    Permission.CAMERA, 
                    Permission.RECORD_AUDIO, 
                    Permission.WRITE_EXTERNAL_STORAGE, 
                    Permission.READ_EXTERNAL_STORAGE
                ]
                def permission_callback(permissions, grant_results):
                    # უზრუნველყოფს, რომ მთავარ ნაკადზე დაბრუნდეს და ისე გაიხსნას ფანჯარა
                    Clock.schedule_once(lambda dt: callback_func(), 0.1)
                
                request_permissions(perms, permission_callback)
                return
            except Exception as e:
                print("Permission request error:", e)
        
        # თუ ანდროიდი არ არის ან შეცდომა მოხდა, პირდაპირ გაუშვას
        Clock.schedule_once(lambda dt: callback_func(), 0.1)
