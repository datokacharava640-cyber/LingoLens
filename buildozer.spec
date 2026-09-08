[app]

# -----------------------------------------------------------------------------
# აპლიკაციის ძირითადი მონაცემები
# -----------------------------------------------------------------------------
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,onnx
version = 2.0.0

# -----------------------------------------------------------------------------
# დამოკიდებულებები (Requirements)
# -----------------------------------------------------------------------------
# დამატებულია onnxruntime და numpy ლოკალური Offline AI თარგმნისთვის
requirements = python3,kivy,android,pyjnius,plyer,requests,certifi,urllib3,idna,chardet,openssl,numpy,onnxruntime

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

# AndroidX და Jetifier მხარდაჭერა (ბიბლიოთეკების კონფლიქტის თავიდან ასაცილებლად)
android.enable_androidx = True
android.enable_jetifier = True

# არქიტექტურა (მხოლოდ arm64-v8a სტაბილური ბილდისთვის)
android.archs = arm64-v8a
android.allow_backup = True

# FileProvider კამერის უსაფრთხო წვდომისთვის Android 7.0+ (API 24+) ვერსიებზე
android.extra_manifest_xml = <application><provider android:name="androidx.core.content.FileProvider" android:authorities="${applicationId}.fileprovider" android:exported="false" android:grantUriPermissions="true"><meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/file_paths" /></provider></application>

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
