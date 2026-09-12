[app]

# (str) Title of your application
title = LingoLens AI

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lingolens

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,ttf,json,so,xml

# (list) List of directory to exclude
source.exclude_patterns = api/*,Dockerfile,vercel.json,setup.py

# (str) Application versioning
version = 3.6.5

# (list) Application requirements
requirements = python3,kivy,requests,certifi,urllib3,idna,pillow,plyer,android

# (str) Custom source folders for requirements
p4a.bootstrap = sdl2
p4a.branch = master

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 21

# (int) Android NDK version / API level
android.ndk_api = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (bool) Allow cleartext traffic
android.uses_cleartext_traffic = true

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) Enable Jetifier support
android.enable_jetifier = True

# (list) The Android archs to build for
android.archs = arm64-v8a

# (str) Extra Manifest
android.extra_manifest_xml = extra_manifest.xml

# (str) File paths
android.add_src = res/xml/file_paths.xml

# (bool) Allow backup
android.allow_backup = True

# (str) Format to pack the application
android.release_artifact = apk

# (bool) Optimize python bytecode
android.optimize_python = True

# (str) Launch mode
android.manifest.launch_mode = singleTask

[buildozer]
log_level = 2
warn_on_root = 1
