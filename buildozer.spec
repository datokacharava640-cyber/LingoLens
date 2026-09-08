[app]

# -----------------------------------------------------------------------------
# აპლიკაციის ძირითადი მონაცემები
# -----------------------------------------------------------------------------
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
version = 10.0.0

# -----------------------------------------------------------------------------
# დამოკიდებულებები (Requirements)
# -----------------------------------------------------------------------------
requirements = hostpython3==3.10.12,python3==3.10.12,kivy,android,pyjnius,plyer,requests,certifi,urllib3,idna,chardet

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
# Android SDK / NDK / Gradle პარამეტრები
# -----------------------------------------------------------------------------
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

# Gradle Dependencies (ML Kit & AndroidX)
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.appcompat:appcompat:1.6.1, com.google.android.material:material:1.9.0

# AndroidX Поддержка
android.enable_androidx = True

# არქიტექტურა
android.archs = arm64-v8a
android.allow_backup = True

# -----------------------------------------------------------------------------
# Android Advanced Options
# -----------------------------------------------------------------------------
android.manifest.launch_mode = singleTask

[buildozer]

# -----------------------------------------------------------------------------
# Buildozer სისტემური პარამეტრები
# -----------------------------------------------------------------------------
log_level = 2
warn_on_root = 1
