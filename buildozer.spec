[app]

# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain
package.domain = org.lingolens.app

# (str) Source code directory
source.dir = .

# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,db,ttf,json

# (list) Include patterns
source.include_patterns = assets/*, modules/*, modules/*.py

# (str) Application versioning
version = 8.0.0

# (list) Application requirements
requirements = python3,kivy==2.3.0,pyjnius,android,plyer,requests,urllib3,charset_normalizer,certifi,idna,PyPDF2,python-docx

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FLASHLIGHT, POST_NOTIFICATIONS, SYSTEM_ALERT_WINDOW

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 24

# (str) Android NDK version
android.ndk = 25b

# (bool) Use --private data directory
android.private_storage = True

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True

# (list) Android architectures
android.archs = arm64-v8a

[buildozer]

# (int) Log level (2 = Debug)
log_level = 2

# (int) Display warning if run as root
warn_on_root = 0
