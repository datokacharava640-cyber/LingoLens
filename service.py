import time
from time import sleep

# Android Foreground Notification Setup
try:
    from jnius import autoclass
    PythonService = autoclass('org.kivy.android.PythonService')
    service = PythonService.mService

    NotificationBuilder = autoclass('android.app.Notification$Builder')
    NotificationManager = autoclass('android.app.NotificationManager')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    Context = autoclass('android.content.Context')

    channel_id = "lingolens_bg_service"
    channel_name = "LingoLens Live Translator"

    notification_manager = service.getSystemService(Context.NOTIFICATION_SERVICE)
    channel = NotificationChannel(channel_id, channel_name, NotificationManager.IMPORTANCE_LOW)
    notification_manager.createNotificationChannel(channel)

    builder = NotificationBuilder(service, channel_id)
    builder.setContentTitle("LingoLens Active")
    builder.setContentText("Real-Time Speech Processing...")
    builder.setSmallIcon(service.getApplicationInfo().icon)

    notification = builder.build()
    service.startForeground(1001, notification)
except Exception as e:
    print(f"Service Notification Error: {e}")

if __name__ == '__main__':
    while True:
        sleep(1)
