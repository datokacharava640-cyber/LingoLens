[app]

title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens.app
source.dir = .
icon.filename = %(source.dir)s/icon.png
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json
source.include_patterns = assets/*, modules/*, modules/*.py
version = 8.0.0

# ამოღებულია დამატებითი C-კონფლიქტური ბიბლიოთეკები
requirements = python3,kivy==2.3.0,pyjnius,android,plyer,requests,urllib3,charset_normalizer,certifi,idna

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
