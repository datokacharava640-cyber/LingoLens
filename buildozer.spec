[app]

# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android packaging)
package.domain = com.lingolens.app

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
# დაემატა xml, json, txt, html და md (VERCEL_SERVER_URL-ისა და მანიფესტის ფაილებისთვის)
source.include_exts = py,png,jpg,kv,atlas,ttf,xml,json,txt,html,md

# (str) Application version
version = 3.2.1

# (list) Application requirements
requirements = python3,kivy==2.3.0,android,pyjnius,opencv,requests,urllib3,certifi,openssl,hostpython3

# (list) Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, MODIFY_AUDIO_SETTINGS

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 21

# (str) Android NDK version (დაკომენტარებულია, რომ Buildozer-მა ავტომატურად აირჩიოს თავსებადი ვერსია)
# android.ndk = 25b

# (bool) If True, then skip building an APK
android.skip_update = False

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (list) The Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (str) Orientation (landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Extra XML manifest rules
# დაემატა თქვენი extra_manifest.xml-ის ინტეგრაციისთვის
android.extra_manifest_xml = extra_manifest.xml

# (list) List of Java classes to add to the compilation
android.add_activities = org.kivy.android.PythonActivity

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) Custom Java dependencies
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = ignore, 1 = warn, 2 = error)
warn_on_root = 1
