[app]

# აპლიკაციის ძირითადი მონაცემები
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,so,xml
version = 2.5.0

# გასწორებული requirements (კონფლიქტური პაკეტების გარეშე)
requirements = python3,kivy==2.3.0,plyer,chardet,idna,requests,urllib3,certifi,pillow

# p4a პარამეტრები
p4a.bootstrap = sdl2

orientation = portrait
fullscreen = 0

# Android ნებართვები
android.permissions = INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, VIBRATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO, POST_NOTIFICATIONS, SYSTEM_ALERT_WINDOW

android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

# HTTP/HTTPS ქსელური კავშირის დაშვა
android.uses_cleartext_traffic = true

# რესურსების საქაღალდე
android.add_resources = res

# Android dependencies
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.appcompat:appcompat:1.6.1, com.google.android.material:material:1.9.0

android.enable_androidx = True
android.enable_jetifier = True

# არქიტექტურა და ოპტიმიზაცია
android.archs = arm64-v8a
android.allow_backup = True
android.release_artifact = apk
android.optimize_python = True

android.manifest.launch_mode = singleTask

[buildozer]
log_level = 2
warn_on_root = 1
