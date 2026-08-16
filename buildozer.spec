[app]

title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens.app
source.dir = .
icon.filename = %(source.dir)s/icon.png
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json
version = 10.0.0

# python-for-android-ის master ტოტი Cython 3-ის მხარდაჭერით
p4a.branch = master

requirements = python3,kivy==2.3.0,pyjnius,android,plyer,requests,urllib3,certifi,idna,charset-normalizer,pypdf,openssl

orientation = portrait
fullscreen = 0
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FLASHLIGHT, POST_NOTIFICATIONS, SYSTEM_ALERT_WINDOW
android.api = 33
android.minapi = 24
android.ndk = 25b
android.private_storage = True
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 0
