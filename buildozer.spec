[app]

title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,xml,json,txt,html,md,db
source.include_patterns = res/*
version = 3.3.0

requirements = python3,kivy==2.3.0,android,pyjnius,pillow,requests,urllib3,certifi,openssl

build_as_cython = 0
android.permissions = CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.skip_update = False
android.accept_sdk_license = True
android.archs = arm64-v8a
orientation = portrait
fullscreen = 0
android.enable_androidx = True
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1

[buildozer]
log_level = 2
warn_on_root = 1
