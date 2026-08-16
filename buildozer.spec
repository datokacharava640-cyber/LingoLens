[app]

title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens.app
source.dir = .
icon.filename = %(source.dir)s/icon.png
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json
version = 10.0.0

requirements = python3,kivy==2.3.0,requests,urllib3,certifi,idna,charset-normalizer,plyer,android

orientation = portrait
fullscreen = 0
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FLASHLIGHT, POST_NOTIFICATIONS, SYSTEM_ALERT_WINDOW, READ_SMS, RECEIVE_SMS, MODIFY_AUDIO_SETTINGS
android.api = 33
android.minapi = 24
android.ndk = 25b
android.private_storage = True
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 1
warn_on_root = 0
