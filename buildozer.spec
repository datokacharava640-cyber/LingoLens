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
source.include_exts = py,png,jpg,kv,ttf,json,xml

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# Cython-ის და Kivy-ს ზუსტი ვერსიები GitHub Actions-ისთვის
requirements = python3,kivy==2.3.0,kivymd,requests,plyer,pyjnius,android

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, SYSTEM_ALERT_WINDOW, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 24

# (str) Android NDK version to use (25b საუკეთესოა Kivy 2.3.0-ისთვის)
android.ndk = 25b

# (list) The Android archs to build for
android.archs = arm64-v8a

# (list) Gradle dependencies for ML Kit and Core Android
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0, androidx.core:core-ktx:1.10.1

# (list) Custom XML/Resource folders (FileProvider-ისთვის)
android.add_src = res/

# (bool) Auto-accept Android SDK/NDK licenses
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 1
