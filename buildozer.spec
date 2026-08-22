[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json,xml

icon.filename = %(source.dir)s/icon.png
version = 1.0.0

requirements = python3,kivy==2.3.0,plyer,pyjnius,android

p4a.branch = release-2024.01.21

orientation = portrait
fullscreen = 0

# სრული Android ნებართვები
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MODIFY_AUDIO_SETTINGS

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Google ML Kit Text Recognition
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.core:core-ktx:1.10.1
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
