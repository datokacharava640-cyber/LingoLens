[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,json,xml

# ვიზუალური აქტივები
icon.filename = %(source.dir)s/icon.png

version = 1.0.0

# გასწორებული და ოპტიმიზებული ბიბლიოთეკები (ამოღებულია გაჭედვის გამომწვევი პაკეტები)
requirements = python3,kivy==2.3.0,plyer,pyjnius,android

# Python-for-android სტაბილური შტო
p4a.branch = release-2024.01.21

orientation = portrait
fullscreen = 0

# Android Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, SYSTEM_ALERT_WINDOW, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_SMS, RECEIVE_SMS

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Google ML Kit & Android FileProvider
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.core:core-ktx:1.10.1
android.add_resources = res/
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
