[app]

title = LingoLens AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,so,xml
source.exclude_patterns = api/*,Dockerfile,vercel.json,setup.py

version = 4.0.0

# python3-ის ნაცვლად მითითებულია 3.11.0 ვერსია
requirements = python3==3.11.0,kivy,requests,pillow,plyer,android,urllib3,certifi

p4a.bootstrap = sdl2
orientation = portrait
fullscreen = 0

android.permissions = CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,READ_MEDIA_IMAGES
android.api = 33
android.minapi = 24
android.ndk_api = 24
android.ndk = 25b

android.accept_sdk_license = True
android.uses_cleartext_traffic = true
android.enable_androidx = True
android.enable_jetifier = True
android.archs = arm64-v8a

# android.extra_manifest_xml = extra_manifest.xml

android.allow_backup = True
android.release_artifact = apk
android.optimize_python = True
android.manifest.launch_mode = singleTask

[buildozer]
log_level = 2
warn_on_root = 1
