[app]

# აპლიკაციის ძირითადი მონაცემები
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,so,xml
version = 2.5.0

# Kivy 2.2.1 არის ყველაზე სტაბილური ბილდი Cython 0.29.33 + NDK 25b-სთვის
requirements = python3,kivy==2.2.1,plyer,chardet,idna,requests,urllib3,certifi,pillow

# p4a პარამეტრები
p4a.bootstrap = sdl2

orientation = portrait
fullscreen = 0

# Android ნებართვები
android.permissions = INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, VIBRATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO, POST_NOTIFICATIONS, SYSTEM_ALERT_WINDOW

# NDK 25b და API 33 (p4a-ის მოთხოვნის შესაბამისად)
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

# HTTP/HTTPS ქსელური კავშირის დაშვა
android.uses_cleartext_traffic = true

# რესურსების საქაღალდე და მანიფესტის გაფართოება
android.add_resources = res
android.extra_manifest_xml = extra_manifest.xml

# Android dependencies
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.appcompat:appcompat:1.6.1, com.google.android.material:material:1.9.0

android.enable_androidx = True
android.enable_jetifier = True

# არქიტექტურა
android.archs = arm64-v8a
android.allow_backup = True
android.release_artifact = apk
android.optimize_python = True

android.manifest.launch_mode = singleTask

[buildozer]
log_level = 2
warn_on_root = 1
