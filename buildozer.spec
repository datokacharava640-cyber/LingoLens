[app]
title = LingoLens
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

requirements = python3==3.10.12,kivy==2.3.0,openssl,requests,urllib3,certifi,idna,charset_normalizer

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,CAMERA,RECORD_AUDIO
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
