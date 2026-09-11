[app]

title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,so,xml

# მთავარ ფაილად მითითებულია api/index.py
source.filename = api/index.py

# Docker, Vercel და Colab ფაილების იგნორირება
source.exclude_patterns = Dockerfile, vercel.json, setup.py, Google Colab

version = 2.5.0

# აპლიკაციის ბიბლიოთეკები
requirements = python3,kivy,plyer,chardet,idna,certifi,pillow

p4a.bootstrap = sdl2
orientation = portrait
fullscreen = 0

# Android-ის სრული ნებართვები
android.permissions = INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, VIBRATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO, POST_NOTIFICATIONS, SYSTEM_ALERT_WINDOW

android.api = 33
android.minapi = 24
android.ndk_api = 24

android.ndk = 25b
android.accept_sdk_license = True
android.uses_cleartext_traffic = true

# Android Manifest-ის დამატებითი ფაილის მიბმა
android.extra_manifest_xml = extra_manifest.xml

# MLKit და AndroidX დამოკიდებულებები
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.appcompat:appcompat:1.6.1, com.google.android.material:material:1.9.0

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
