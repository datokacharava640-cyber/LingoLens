import time
from time import sleep

def start_foreground_service():
    wake_lock = None
    try:
        from jnius import autoclass

        PythonService = autoclass('org.kivy.android.PythonService')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        Context = autoclass('android.content.Context')
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')
        PowerManager = autoclass('android.os.PowerManager')
        ServiceInfo = autoclass('android.content.pm.ServiceInfo')

        service = PythonService.mService
        package_name = service.getPackageName()

        # 1. CPU WakeLock - აპლიკაციის დაძინების აღსაკვეთად
        try:
            power_manager = service.getSystemService(Context.POWER_SERVICE)
            wake_lock = power_manager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK, 
                "LingoLens::ServiceWakeLock"
            )
            wake_lock.acquire()
            print("[Service]: WakeLock წარმატებით გააქტიურდა.")
        except Exception as wl_err:
            print(f"[Service]: WakeLock შეცდომა: {wl_err}")

        # 2. Notification Channel-ის შექმნა
        channel_id = "lingolens_bg_service"
        channel_name = "LingoLens Real-Time Translator"
        notification_manager = service.getSystemService(Context.NOTIFICATION_SERVICE)

        channel = NotificationChannel(
            channel_id, 
            channel_name, 
            NotificationManager.IMPORTANCE_LOW
        )
        notification_manager.createNotificationChannel(channel)

        pm = service.getPackageManager()
        launch_intent = pm.getLaunchIntentForPackage(package_name)
        
        if launch_intent:
            launch_intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)

        flag_immutable_update = 0x04000000 | 0x08000000

        pending_intent = PendingIntent.getActivity(
            service, 
            0, 
            launch_intent, 
            flag_immutable_update
        )

        builder = NotificationBuilder(service, channel_id)
        builder.setContentTitle("LingoLens Active")
        builder.setContentText("Listening and translating in background...")
        builder.setSmallIcon(service.getApplicationInfo().icon)
        builder.setContentIntent(pending_intent)
        builder.setOngoing(True)

        notification = builder.build()

        # 3. Android 14+ Compatible startForeground (Microphone Service Type)
        try:
            # FOREGROUND_SERVICE_TYPE_MICROPHONE = 128 (0x80)
            service_type_mic = getattr(ServiceInfo, 'FOREGROUND_SERVICE_TYPE_MICROPHONE', 128)
            service.startForeground(1001, notification, service_type_mic)
        except Exception:
            # Fallback ძველი Android ვერსიებისთვის
            service.startForeground(1001, notification)

        print("[Service]: Foreground service წარმატებით გაეშვა.")

    except Exception as e:
        print(f"[Service]: Foreground Service შეცდომა: {e}")

    return wake_lock

if __name__ == '__main__':
    lock = start_foreground_service()
    
    # 4. Background Keep-Alive & Auto-Reconnect Loop
    try:
        while True:
            # ფონური პროცესის აქტიურობის მონიტორინგი
            sleep(2)
    except KeyboardInterrupt:
        print("[Service]: სერვისი გაჩერდა.")
    finally:
        if lock and lock.isHeld():
            lock.release()
