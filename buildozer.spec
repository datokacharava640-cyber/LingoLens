[app]
title = LingoLens Live AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Cython 0.29.33 აუცილებელია, რომ Cython 3.0-ის კონფლიქტი აირიდოთ
requirements = python3,kivy==2.3.0,cython==0.29.33,urllib3,certifi,idna,charset_normalizer,pyjnius

orientation = portrait
fullscreen = 0

# Python-for-Android-ის განახლებული ბრანჩის გამოყენება
p4a.branch = master

# უფლებები
android.permissions = INTERNET,CAMERA,RECORD_AUDIO,SYSTEM_ALERT_WINDOW,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
