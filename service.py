import time
from time import sleep

def start_foreground_service():
    try:
        from jnius import autoclass

        PythonService = autoclass('org.kivy.android.PythonService')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        Context = autoclass('android.content.Context')
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')

        service = PythonService.mService
        package_name = service.getPackageName()

        channel_id = "lingolens_bg_service"
        channel_name = "LingoLens Live Translator"
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
        builder.setContentText("Real-Time Speech Processing...")
        builder.setSmallIcon(service.getApplicationInfo().icon)
        builder.setContentIntent(pending_intent)
        builder.setOngoing(True)

        notification = builder.build()
        service.startForeground(1001, notification)
        print("Foreground service successfully started.")

    except Exception as e:
        print(f"Service Notification Error: {e}")

if __name__ == '__main__':
    start_foreground_service()
    while True:
        sleep(1)
