[app]
# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lingolens

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,ttf,json

# (str) Application versioning (method 1)
version = 3.2.1

# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (int) Cythonize modules
cythonize = 1

# (list) Application requirements
requirements = python3,kivy==2.2.1,plyer,requests,urllib3,certifi,idna,charset-normalizer

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FOREGROUND_SERVICE, POST_NOTIFICATIONS

# (list) Features
android.features = android.hardware.camera, android.hardware.camera.autofocus, android.hardware.microphone

# (int) Target Android API
android.api = 31

# (int) Minimum API supported
android.minapi = 21

# (str) Android NDK version
android.ndk = 23b

# (str) Android NDK architecture to build for
android.archs = arm64-v8a

# (bool) Accept Android SDK licenses automatically
android.accept_sdk_license = True

# (str) Python-for-Android branch
p4a.branch = master

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1
