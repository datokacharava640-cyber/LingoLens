[app]
title = LingoLens Ultra Pro 🇬🇪
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json,xml

icon.filename = %(source.dir)s/icon.png
version = 3.2.1

cythonize = 1

# კონკრეტული სტაბილური Python 3.10-ის მითითება p4a-სთვის:
requirements = python3==3.10.11,kivy==2.3.0,plyer,requests,urllib3,certifi

# p4a-ს სტაბილური release ტოტი:
p4a.branch = release-2024.01.21

orientation = portrait
fullscreen = 0

android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FOREGROUND_SERVICE, POST_NOTIFICATIONS
android.features = android.hardware.camera, android.hardware.camera.autofocus, android.hardware.microphone

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
