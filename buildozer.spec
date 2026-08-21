[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json,xml

# ვიზუალური აქტივები (ლოგო და Splash Screen)
icon.filename = %(source.dir)s/icon.png

version = 1.0.0

# დაფიქსირებული requirements
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,plyer,pyjnius,android

orientation = portrait
fullscreen = 0

# Android Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, SYSTEM_ALERT_WINDOW, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

# Google ML Kit & Android FileProvider
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.core:core-ktx:1.10.1
android.add_src = res/
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
