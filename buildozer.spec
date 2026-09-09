[app]

# -----------------------------------------------------------------------------
# აპლიკაციის ძირითადი მონაცემები
# -----------------------------------------------------------------------------
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,so,xml
version = 2.0.0

# -----------------------------------------------------------------------------
# დამოკიდებულებები (Requirements)
# -----------------------------------------------------------------------------
requirements = python3,kivy,android,pyjnius,plyer,requests,certifi,urllib3,idna,chardet,openssl

# -----------------------------------------------------------------------------
# p4a სტაბილური ვერსიის მითითება
# -----------------------------------------------------------------------------
p4a.branch = v2024.01.21

# -----------------------------------------------------------------------------
# ეკრანის პარამეტრები
# -----------------------------------------------------------------------------
orientation = portrait
fullscreen = 0

# -----------------------------------------------------------------------------
# Android უფლებები (Permissions)
# -----------------------------------------------------------------------------
android.permissions = INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, VIBRATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO, POST_NOTIFICATIONS, SYSTEM_ALERT_WINDOW

# -----------------------------------------------------------------------------
# Android SDK / NDK / Gradle პარამეტრები
# -----------------------------------------------------------------------------
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

# Gradle Dependencies (Google ML Kit & AndroidX)
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.appcompat:appcompat:1.6.1, com.google.android.material:material:1.9.0

# AndroidX მხარდაჭერა
android.enable_androidx = True
android.enable_jetifier = True

# არქიტექტურა და არტიფაქტი
android.archs = arm64-v8a
android.allow_backup = True
android.release_artifact = aab
android.optimize_python = True

# FileProvider ფაილის მისამართი
android.extra_manifest_xml = extra_manifest.xml

# Advanced Options
android.manifest.launch_mode = singleTask

[buildozer]
log_level = 2
warn_on_root = 1
