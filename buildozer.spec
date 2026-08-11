[app]

# (str) Title of your application
title = LingoLens Live AI

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lingolens

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (included ttf for fonts, json, wav)
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# pyjnius, websocket-client, openssl აუცილებელია Realtime WebSocket-ისთვის
requirements = python3,kivy,openssl,android,pyjnius,websocket-client,requests,certifi,pillow

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, RECORD_AUDIO, CAMERA, FOREGROUND_SERVICE, FOREGROUND_SERVICE_MICROPHONE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (bool) If true, then keep the screen on during app runtime
android.wakelock = True

# (int) Target Android API, should be 33 for modern Android devices
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True

# (list) The Android archs to build for (arm64-v8a არის სწრაფი და თავსებადი ყველა თანამედროვე ტელეფონთან)
android.archs = arm64-v8a

# (bool) Enable Android auto backup
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 1
