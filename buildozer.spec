[app]

# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android packaging)
package.domain = org.lingolens

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,ttf,xml,json,txt,html,md,db

# (list) Inclusion patterns for files
source.include_patterns = res/*

# (str) Application version
version = 3.3.0

# (list) Application requirements
requirements = python3,kivy==2.3.0,android,pyjnius,pillow,requests,urllib3,certifi,openssl

# (bool) Build code as Cython (1 = True, 0 = False)
build_as_cython = 0

# (list) Permissions
android.permissions = CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MODIFY_AUDIO_SETTINGS

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 24

# (str) Android NDK version
android.ndk = 25b

# (bool) If True, then skip building an APK
android.skip_update = False

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (list) The Android architectures to build for
android.archs = arm64-v8a

# (str) Orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) Custom Java dependencies
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1

[buildozer]

# (int) Log level
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
