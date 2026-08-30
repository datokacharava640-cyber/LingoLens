[app]

# App titles and metadata
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json
version = 3.6.0

# Requirements for Kivy & Plyer (python3 ვერსიის მითითების გარეშე)
requirements = python3,kivy,certifi,urllib3,requests,plyer

# Orientation & Display
orientation = portrait
fullscreen = 0

# Android Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, CAMERA, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS, VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Android API Specs
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Custom Manifest Template Link
android.manifest.template = AndroidManifest.tmpl.xml

[buildozer]
log_level = 2
warn_on_root = 1
