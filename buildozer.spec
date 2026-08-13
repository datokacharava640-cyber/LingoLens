[app]

# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lingolens.app

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,db,ttf

# (str) Application versioning
version = 4.0.0

# (list) Application requirements
requirements = python3,kivy==2.3.0,pyjnius,numpy,websocket-client

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, MODIFY_AUDIO_SETTINGS

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use (სტაბილური R25b ვერსია!)
android.ndk = 25b

# (bool) Use --private data directory (True) or --dir public storage (False)
android.private_storage = True

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True

# (list) The Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1
