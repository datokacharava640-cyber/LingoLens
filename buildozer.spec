[app]

# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain
package.domain = org.lingolens

# (str) Source code directory
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json

# (str) Application versioning
version = 1.0.0

# (str) Output format
android.release_artifact = apk

# (list) Application requirements - მკაცრად დაფიქსირებული ვერსიები
requirements = python3==3.10.12,kivy==2.3.0,requests==2.31.0,urllib3==2.2.1,certifi==2024.2.2,idna==3.6,charset-normalizer==3.3.2,plyer==2.1.0

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, READ_MEDIA_IMAGES, POST_NOTIFICATIONS, MODIFY_AUDIO_SETTINGS

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) Accept SDK license
android.accept_sdk_license = True

# (str) Architecture to build for
android.archs = arm64-v8a

# (bool) Storage setting
android.private_storage = True

[buildozer]

# (int) Log level
log_level = 2

# (int) Warn if buildozer is run as root
warn_on_root = 1
