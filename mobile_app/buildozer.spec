[app]
# აპლიკაციის დასახელება
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json
version = 9.5.0

# requirements - გასუფთავებულია hostpython3 და pyjnius-ისგან
requirements = python3,kivy==2.3.0,certifi,urllib3,requests,idna,chardet,plyer

# ეკრანის ორიენტაცია
orientation = portrait
fullscreen = 0

# Android უფლებები (Permissions)
android.permissions = INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Android SDK / NDK პარამეტრები
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# p4a სტაბილური ტოტი
p4a.branch = release-2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
