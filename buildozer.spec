[app]

# (str) Title of your application
title = LingoLens Live AI

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lingolens

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements (მხოლოდ ის, რაც რეალურად სჭირდება პროექტს)
requirements = python3,kivy,android,pyjnius,websocket-client

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions (სტაბილური ნებართვები Android 13/API 33-ისთვის)
android.permissions = INTERNET, RECORD_AUDIO, CAMERA, WAKE_LOCK, POST_NOTIFICATIONS, FOREGROUND_SERVICE

# (list) Android Hardware Features
android.features = android.hardware.camera, android.hardware.microphone

# (bool) If true, then keep the screen on during app runtime
android.wakelock = True

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) Enable Android auto backup
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
