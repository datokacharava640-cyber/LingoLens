[app]
title = LingoLens
package.name = lingolens
package.domain = com.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0.0

requirements = python3,kivy,pyjnius,urllib3,requests

orientation = portrait
fullscreen = 0

android.permissions = CAMERA, RECORD_AUDIO, INTERNET, SYSTEM_ALERT_WINDOW, FOREGROUND_SERVICE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True
