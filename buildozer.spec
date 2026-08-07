[app]

# (str) Title of your application
title = LingoLens

# (str) Package name
package.name = lingolens

# (str) Package domain
package.domain = com.lingolens

# (str) Application version
version = 0.1

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,ttf,json

# (list) Application requirements
requirements = python3,kivy==2.3.0,hostpython3,requests,urllib3,chardet,certifi,idna,plyer,pyjnius

# (list) Permissions (ყველა საჭირო ნებართვა რეალური დროის ხმოვანი/ვიზუალური თარგმნისთვის)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,CAMERA,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS,READ_PHONE_STATE,RECEIVE_SMS,READ_SMS,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,POST_NOTIFICATIONS

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

# (int) Log level
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
