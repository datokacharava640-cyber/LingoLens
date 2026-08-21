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

# (list) Include all files in project root
source.include_patterns = assets/*, *.ttf, *.png, *.jpg

# (str) Application versioning
version = 1.0.0

# (str) Output format
android.release_artifact = apk

# (list) Application requirements
requirements = python3,cython==0.29.33,kivy==2.3.0,kivymd,materialyoucolor,asynckivy,plyer,pyjnius,requests,urllib3,openssl

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) ALL Android Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_AUDIO, READ_MEDIA_VIDEO, POST_NOTIFICATIONS, MODIFY_AUDIO_SETTINGS, SYSTEM_ALERT_WINDOW, WAKE_LOCK, VIBRATE, FOREGROUND_SERVICE

# (str) Extra XML manifest setup for Android 10+ Camera FileProvider
android.extra_manifest_xml = extra_manifest.xml

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
warn_on_root = 0
