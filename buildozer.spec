[app]

title = LingoLens AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,wav
source.exclude_patterns = api/*,Dockerfile,vercel.json,setup.py

version = 4.0.0

# დააფიქსირეთ p4a-ს ოფიციალური სტაბილური შტო
p4a.fork = kivy
p4a.branch = release-2024.01.21

# ამოღებულია 'android' პაკეტი (მას p4a თავად დაამატებს)
requirements = python3,kivy==2.3.0,requests,pillow,plyer,urllib3,certifi

p4a.bootstrap = sdl2
orientation = portrait
fullscreen = 0

android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_MEDIA_IMAGES

android.api = 33
android.minapi = 24
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
warn_on_root = 0
