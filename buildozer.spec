[app]

# (str) Title of your application
title = LingoLens AI

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lingolens

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,ttf,json,so,xml

# (list) List of directory to exclude
source.exclude_patterns = api/*, Dockerfile, vercel.json, setup.py, Google Colab

# (str) Application versioning
version = 3.6.3

# (list) Application requirements
# hostpython3-ისა და python3-ის ვერსიის მკაცრი დაფიქსირება
requirements = python3==3.11.0,hostpython3==3.11.0,kivy,pyjnius,plyer,chardet,idna,certifi,pillow,requests

# (str) Custom source folders for requirements
p4a.bootstrap = sdl2

# (str) python-for-android branch
p4a.branch = master

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO, VIBRATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 24

# (int) Android NDK version / API level
android.ndk_api = 24

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (bool) Allow cleartext traffic
android.uses_cleartext_traffic = true

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) Enable Jetifier support
android.enable_jetifier = True

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) Allow backup
android.allow_backup = True

# (str) Format to pack the application
android.release_artifact = apk

# (bool) Optimize python bytecode
android.optimize_python = True

# (str) Launch mode
android.manifest.launch_mode = singleTask

[buildozer]
log_level = 2
warn_on_root = 1
