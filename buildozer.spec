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

# დამატებულია pyjnius და android ხმოვანი წაკითხვისა და ქსელისთვის
requirements = hostpython3==3.11.0,python3==3.11.0,kivy==2.3.0,pillow,requests,urllib3,certifi,openssl,pyjnius,android

# გამოიყენეთ p4a-ს სტაბილური რელიზი
p4a.branch = v2024.01.21

build_as_cython = 0

# Android ნებართვები (დამატებულია MODIFY_AUDIO_SETTINGS ხმისთვის)
android.permissions = CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MODIFY_AUDIO_SETTINGS

android.api = 33
android.minapi = 24
android.ndk = 25b
android.skip_update = False
android.accept_sdk_license = True
android.archs = arm64-v8a
orientation = portrait
fullscreen = 0
android.enable_androidx = True

# Android dependencies - დამატებულია androidx და tts მხარდაჭერა
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1, androidx.core:core:1.10.1

# Pyjnius-ისთვის Java კლასების წვდომა
android.add_jars = 
android.add_src = 

[buildozer]
log_level = 2
warn_on_root = 1
