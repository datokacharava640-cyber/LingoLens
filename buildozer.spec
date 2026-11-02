[app]

title = LingoLens AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json,wav,xml,html,md,txt
version = 6.0.7

requirements = python3,kivy,pyjnius,plyer,android

orientation = portrait
fullscreen = 0

android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, CALL_PHONE, READ_PHONE_STATE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.accept_sdk_license = True
android.uses_cleartext_traffic = true
android.enable_androidx = True
android.enable_jetifier = True
android.archs = arm64-v8a

p4a.python_version = 3.11
p4a.branch = master
p4a.extra_args = --python-version=3.11
[buildozer]
log_level = 2
warn_on_root = 0
