[app]

title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,ttf

version = 4.0.0
requirements = python3,kivy==2.3.0,pyjnius,numpy,websocket-client

orientation = portrait
fullscreen = 0
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, MODIFY_AUDIO_SETTINGS

android.api = 33
android.minapi = 21
android.ndk = 25b

android.private_storage = True
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
