[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json
source.include_patterns = assets/*, *.ttf, *.png, *.jpg
version = 1.0.0

# აუცილებელი Python ბიბლიოთეკები (pyjnius დამატებულია Android API-ებთან პირდაპირი წვდომისთვის)
requirements = python3,kivy==2.3.0,requests,pillow,plyer,urllib3,certifi,pyjnius

orientation = portrait
fullscreen = 0

# სრული Android ნებართვები (მცურავი ფანჯარა, ფონური სერვისი, კამერა, აუდიო, ინტერნეტი)
android.permissions = SYSTEM_ALERT_WINDOW, FOREGROUND_SERVICE, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE, POST_NOTIFICATIONS, CAMERA, INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, VIBRATE, MODIFY_AUDIO_SETTINGS, WAKE_LOCK, FLASHLIGHT

android.api = 33
android.minapi = 24
android.ndk = 25b

android.enable_androidx = True
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 0
