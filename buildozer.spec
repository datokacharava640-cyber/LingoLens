[app]

title = LingoLens AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,so,xml

source.exclude_patterns = api/*, Dockerfile, vercel.json, setup.py, Google Colab

version = 3.6.3

requirements = python3,kivy==2.3.0,plyer,chardet,idna,certifi,pillow,requests

p4a.bootstrap = sdl2
orientation = portrait
fullscreen = 0

android.permissions = INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, VIBRATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk_api = 24

android.ndk = 25b
android.accept_sdk_license = True
android.uses_cleartext_traffic = true

android.enable_androidx = True
android.enable_jetifier = True
android.archs = arm64-v8a
android.allow_backup = True
android.release_artifact = apk
android.optimize_python = True
android.manifest.launch_mode = singleTask

[buildozer]
log_level = 2
warn_on_root = 1
