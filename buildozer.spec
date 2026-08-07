[app]

# (str) Title of your application
title = LingoLens

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android/ios packaging)
package.domain = com.lingolens

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (include font.ttf)
source.include_exts = py,png,jpg,kv,atlas,ttf,json

# (list) Application requirements
requirements = python3,kivy==2.3.0,hostpython3,requests,urllib3,chardet,certifi,idna,plyer,pyjnius

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,CAMERA,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS,READ_PHONE_STATE,RECEIVE_SMS,READ_SMS,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,SYSTEM_ALERT_WINDOW

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 21

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (str) Orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = error, 1 = warning)
warn_on_root = 1
