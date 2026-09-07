[app]

# -----------------------------------------------------------------------------
# აპლიკაციის ძირითადი მონაცემები
# -----------------------------------------------------------------------------
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json
version = 10.0.0

# -----------------------------------------------------------------------------
# დამოკიდებულებები (Requirements)
# დამატებულია pyjnius (აუცილებელია Android-ის ნატიური API-ებისთვის: STT, TTS, Permissions)
# -----------------------------------------------------------------------------
requirements = python3,kivy==2.3.0,android,pyjnius,requests,certifi,urllib3,idna,chardet,plyer

# -----------------------------------------------------------------------------
# ეკრანის პარამეტრები
# -----------------------------------------------------------------------------
orientation = portrait
fullscreen = 0

# -----------------------------------------------------------------------------
# Android უფლებები (Permissions)
# -----------------------------------------------------------------------------
android.permissions = INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, VIBRATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO, POST_NOTIFICATIONS

# -----------------------------------------------------------------------------
# Android SDK / NDK პარამეტრები
# -----------------------------------------------------------------------------
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

# არქიტექტურა (64-bit და 32-bit მოწყობილობებისთვის)
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Python for Android სტაბილური ტოტი
p4a.branch = release-2024.01.21

# -----------------------------------------------------------------------------
# Android Advanced Options
# -----------------------------------------------------------------------------
android.manifest.launch_mode = singleTask

[buildozer]

log_level = 2
warn_on_root = 1
