[app]
title = LingoLens Live AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav
version = 1.0.0

# Kivy მითითებულია ვერსიის გარეშე, რათა p4a-მ თავისი უშეცდომო რეცეპტი გამოიყენოს
requirements = python3,kivy,android,pyjnius,websocket-client,requests,urllib3,certifi

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, RECORD_AUDIO, CAMERA, FOREGROUND_SERVICE, FOREGROUND_SERVICE_MICROPHONE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.accept_sdk_license = True

android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
