[app]

title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,gif,xml,json,txt,html,md,db
source.include_patterns = res/*
version = 3.3.0

# აპლიკაციის ლოგო
icon.filename = %(source.dir)s/icon.png

# დამოკიდებულებები (დამატებულია python-for-android-ის სტაბილური ვერსია)
requirements = python3,kivy==2.3.0,pillow,urllib3==1.26.15,certifi,requests,pyjnius,android,python-for-android==2024.1.9

build_as_cython = 0

# Android-ის უფლებები
android.permissions = CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MODIFY_AUDIO_SETTINGS

# Android SDK და NDK კონფიგურაცია
android.api = 33
android.minapi = 24
android.ndk = 25b
android.skip_update = False
android.accept_sdk_license = True
android.archs = arm64-v8a
orientation = portrait
fullscreen = 0
android.enable_androidx = True

# Gradle დამოკიდებულებები
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1, androidx.core:core:1.10.1

[buildozer]
log_level = 2
warn_on_root = 1
