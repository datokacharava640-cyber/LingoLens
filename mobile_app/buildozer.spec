[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json
version = 3.6.0

requirements = python3,kivy,certifi,urllib3,requests,idna,chardet,plyer,pyjnius

orientation = portrait
fullscreen = 0

# Android 5-დან Android 14+-მდე ყველა საჭირო ნებართვა
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, CAMERA, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS, VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO, POST_NOTIFICATIONS, FOREGROUND_SERVICE, WAKE_LOCK

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_licence = True
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True

p4a.fork = kivy
p4a.branch = release-2024.01.21

android.manifest.template = AndroidManifest.tmpl.xml

[buildozer]
log_level = 2
warn_on_root = 1
