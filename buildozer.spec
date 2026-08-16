[app]

# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain (შესწორებულია)
package.domain = org.lingolens

# (str) Source code directory
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json

# (str) Application versioning
version = 1.0.0

# (str) Python for Android branch
p4a.branch = master

# (list) Application requirements
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,idna,charset-normalizer,plyer,pypdf

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) Permissions (ამოღებულია SMS და შეზღუდული უფლებები)
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, FLASHLIGHT, POST_NOTIFICATIONS, MODIFY_AUDIO_SETTINGS

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

# (str) Architecture to build for (დაემატა armeabi-v7a)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Storage setting
android.private_storage = True

[buildozer]

# (int) Log level
log_level = 2

# (int) Warn if buildozer is run as root
warn_on_root = 1
