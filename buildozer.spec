[app]
title = LingoLens Ultra Pro 🇬🇪
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json,xml

icon.filename = %(source.dir)s/icon.png
version = 1.0.0

requirements = python3,kivy==2.3.0,plyer,pyjnius,android,requests,urllib3,certifi

p4a.branch = release-2024.01.21

orientation = portrait
fullscreen = 0

# Android-ის სრული ნებართვები
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MODIFY_AUDIO_SETTINGS, FOREGROUND_SERVICE, POST_NOTIFICATIONS

# Hardware Features
android.features = android.hardware.camera, android.hardware.camera.autofocus, android.hardware.microphone

# Target SDK API 34 (Google Play-ს აუცილებელი მოთხოვნა 2026 წლისთვის)
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Google ML Kit & Dynamic OCR models
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.core:core-ktx:1.10.1, com.google.android.gms:play-services-mlkit-text-recognition:19.0.0
android.accept_sdk_license = True
android.meta_data = com.google.mlkit.vision.DEPENDENCIES = ocr

[buildozer]
log_level = 2
warn_on_root = 1
