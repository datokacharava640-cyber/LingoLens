[app]

# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain
package.domain = org.lingolens.app

# (str) Source code directory
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,db,ttf

# (str) Application versioning
version = 4.0.0

# (list) Application requirements
# hostpython3 და sqlite3 დამატებულია, რომ p4a-მ შიდა ბიბლიოთეკები უშეცდომოდ ააწყოს
requirements = python3,kivy==2.2.1,pyjnius,numpy,websocket-client,sqlite3,hostpython3

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, MODIFY_AUDIO_SETTINGS

# (int) Target Android API (31 ყველაზე სტაბილურია P4A-სთვის)
android.api = 31

# (int) Minimum API required
android.minapi = 21

# (int) Android SDK version
android.sdk = 31

# (str) Android NDK version
android.ndk = 25b

# (bool) Use --private data directory
android.private_storage = True

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True

# (list) Android architectures
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

# (int) Log level (2 = Debug)
log_level = 2

# (int) Display warning if run as root
warn_on_root = 1
