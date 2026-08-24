[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json

icon.filename = %(source.dir)s/icon.png
version = 3.2.1

cythonize = 1

requirements = python3,kivy==2.2.1,plyer,requests,certifi,idna,urllib3,charset-normalizer

orientation = portrait
fullscreen = 0

android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FOREGROUND_SERVICE, POST_NOTIFICATIONS
android.features = android.hardware.camera, android.hardware.camera.autofocus, android.hardware.microphone

android.api = 30
android.minapi = 21
android.ndk = 23b
android.archs = arm64-v8a

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
