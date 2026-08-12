[app]

# (str) Title of your application
title = LingoLens Live AI

# (str) Package name
package.name = lingolens

# (str) Package domain
package.domain = org.lingolens

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements (Kivy Master - Cython 3 თავსებადი)
requirements = python3,https://github.com/kivy/kivy/archive/master.zip,pyjnius,websocket-client,requests

# (str) Supported orientation
orientation = portrait

# (bool) Fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, RECORD_AUDIO, CAMERA, WAKE_LOCK, POST_NOTIFICATIONS, FOREGROUND_SERVICE

# (list) Android Hardware Features
android.features = android.hardware.camera, android.hardware.microphone

# (bool) Keep screen on
android.wakelock = True

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 24

# (str) Android NDK version
android.ndk = 25b

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True

# (list) Android archs
android.archs = arm64-v8a

# (bool) Enable Android auto backup
android.allow_backup = True

[buildozer]

# (int) Log level
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
