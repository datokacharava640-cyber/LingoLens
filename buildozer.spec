[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json
source.include_patterns = assets/*, *.ttf, *.png, *.jpg
version = 1.0.0
android.release_artifact = apk

# სტაბილური ბიბლიოთეკების სია
requirements = python3,kivy==2.3.0,pillow,plyer,pyjnius,requests,android

orientation = portrait
fullscreen = 0
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, READ_MEDIA_IMAGES

android.api = 33
android.minapi = 24
android.ndk = 25b
android.enable_androidx = True
android.accept_sdk_license = True

android.archs = arm64-v8a
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 0
