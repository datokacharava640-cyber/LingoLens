[app]
# აპლიკაციის დასახელება და დომენი
title = LingoLens Ultra Pro 🇬🇪
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json,xml

# ლოგო და ვერსია
icon.filename = %(source.dir)s/icon.png
version = 3.0.0

# კოდის დაცვა - Python კოდის C-ში კომპილაცია
cythonize = 1

# დამოკიდებულებები (Kivy, Networking & Native Android)
requirements = python3,kivy==2.3.0,plyer,pyjnius,android,requests,urllib3,certifi,cython

# ეკრანის ორიენტაცია
orientation = portrait
fullscreen = 0

# Android-ის სრული ნებართვები (AR, VAD Audio & Storage)
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MODIFY_AUDIO_SETTINGS, FOREGROUND_SERVICE, POST_NOTIFICATIONS

# Hardware Features (კამერა და მიკროფონი AR/VAD რეჟიმისთვის)
android.features = android.hardware.camera, android.hardware.camera.autofocus, android.hardware.microphone

# Target SDK API 34 & NDK
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Google ML Kit Native Dependencies & AndroidX
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.core:core-ktx:1.12.0, com.google.android.gms:play-services-mlkit-text-recognition:19.0.0
android.accept_sdk_license = True

# ML Kit OCR Auto-download მოდული
android.meta_data = com.google.mlkit.vision.DEPENDENCIES=ocr

[buildozer]
log_level = 2
warn_on_root = 1
