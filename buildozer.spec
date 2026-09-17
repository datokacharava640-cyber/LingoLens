[app]

title = LingoLens AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,wav,xml
source.exclude_patterns = api/*,Dockerfile,vercel.json,setup.py

version = 4.0.0

# Pillow-ს მივუთითოთ თავსებადი ვერსია (მაგ. pillow==10.0.0) ან უბრალოდ pillow
requirements = python3,kivy==2.2.1,requests,urllib3,certifi,charset-normalizer,idna,pillow==10.0.0,plyer

p4a.bootstrap = sdl2
orientation = portrait
fullscreen = 0

android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.build_tools_version = 33.0.0

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
warn_on_root = 0
