[app]
# აპლიკაციის დასახელება
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json
version = 9.5.0

# requirements
requirements = python3,kivy,certifi,urllib3,requests,idna,chardet,plyer,pyjnius

# ეკრანის ორიენტაცია
orientation = portrait
fullscreen = 0

# Android უფლებები (Permissions)
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, RECORD_AUDIO, BLUETOOTH, BLUETOOTH_CONNECT, BLUETOOTH_ADMIN, MODIFY_AUDIO_SETTINGS, VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO, POST_NOTIFICATIONS, FOREGROUND_SERVICE, WAKE_LOCK, RECEIVE_BOOT_COMPLETED

# Android SDK / NDK პარამეტრები
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_licence = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# აიძულებს p4a-ს გამოიყენოს სტაბილური ტოტი (აკრძალავს Python 3.14-ს)
p4a.branch = release-2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
