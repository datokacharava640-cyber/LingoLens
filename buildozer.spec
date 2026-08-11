[app]
title = LingoLens Live AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav
version = 1.0.0

# დაფიქსირებულია python3==3.11.5 Python 3.14-ის ავტომატური გადმოწერის ასარიდებლად
requirements = python3==3.11.5,kivy==2.3.0,android,pyjnius,websocket-client,requests,certifi

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, RECORD_AUDIO, CAMERA, FOREGROUND_SERVICE, FOREGROUND_SERVICE_MICROPHONE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.accept_sdk_license = True

android.archs = arm64-v8a

# p4a-ს სტაბილური რელიზი
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
