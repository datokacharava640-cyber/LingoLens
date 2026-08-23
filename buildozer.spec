[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json

icon.filename = %(source.dir)s/icon.png
version = 3.2.1

cythonize = 1

# Kivy-სა და ქსელური ბიბლიოთეკების მკაცრი დაფიქსირება
requirements = python3,kivy==2.2.1,plyer,requests,urllib3,certifi,idna,charset-normalizer

orientation = portrait
fullscreen = 0

# უფლებები და ფუნქციონალი
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FOREGROUND_SERVICE, POST_NOTIFICATIONS
android.features = android.hardware.camera, android.hardware.camera.autofocus, android.hardware.microphone

# Android SDK/NDK თავსებადი კომბინაცია
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

android.accept_sdk_license = True

# p4a (python-for-android) ვერსიის მკაცრი მითითება
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
