[app]
title = LingoLens Ultra Pro 🇬🇪
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json,xml

icon.filename = %(source.dir)s/icon.png
version = 3.2.1

cythonize = 1

# ბიბლიოთეკები (ვერსიების ნომრების გარეშე, გარდა kivy-სა):
requirements = python3,kivy==2.3.0,plyer,pyjnius,android,requests,urllib3,certifi

orientation = portrait
fullscreen = 0

# ყველა საჭირო ნებართვა LingoLens-ისთვის (კამერა, მიკროფონი, ფაილები, ინტერნეტი):
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MODIFY_AUDIO_SETTINGS, FOREGROUND_SERVICE, POST_NOTIFICATIONS

# აპარატურული ფუნქციები:
android.features = android.hardware.camera, android.hardware.camera.autofocus, android.hardware.microphone

# SDK/NDK და არქიტექტურის პარამეტრები:
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Gradle და ML Kit (OCR ტექსტის ამოცნობისთვის):
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.core:core-ktx:1.12.0
android.accept_sdk_license = True
android.meta_data = com.google.mlkit.vision.DEPENDENCIES=ocr

[buildozer]
log_level = 2
warn_on_root = 1
