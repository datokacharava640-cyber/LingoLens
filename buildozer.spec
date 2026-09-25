[app]

# (str) Title of your application
title = LingoLens AI

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lingolens

# (str) Source code where the main.py live
source.dir = .

# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json,wav,xml

# (list) List of directory to exclude
source.exclude_dirs = tests, bin, venv, .git, .github, Google Colab

# (list) List of exclusions using pattern matching
source.exclude_patterns = Dockerfile, vercel.json, setup.py, *.ipynb, .env, .gitignore

# (str) Application versioning
version = 6.0.1

# (list) Application requirements
requirements = python3,kivy,pillow,requests,urllib3,certifi

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 24

# (str) Android NDK version
android.ndk = 25b

# (int) Android NDK API
android.ndk_api = 24

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (bool) Allow cleartext network traffic (HTTP)
android.uses_cleartext_traffic = true

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) Enable Jetifier
android.enable_jetifier = True

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) Backup option
android.allow_backup = True

# (str) Format used to package the app for release
android.release_artifact = apk

# (bool)
android.optimize_python = False

# (str) Launch mode
android.manifest.launch_mode = singleTask

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 0
