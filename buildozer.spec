[app]

# Application information
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json
source.include_patterns = assets/*, *.ttf, *.png, *.jpg
version = 1.0.0
android.release_artifact = apk

# Requirements - Modern & Stable stack
requirements = python3,kivy==2.3.0,kivymd,pillow,plyer,pyjnius,requests,android

# Display & Permissions
orientation = portrait
fullscreen = 0
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, READ_MEDIA_IMAGES

# Target Android API
android.api = 33
android.minapi = 24
android.ndk = 25c
android.enable_androidx = True
android.accept_sdk_license = True

# Architecture
android.archs = arm64-v8a
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 0
