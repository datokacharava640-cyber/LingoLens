[app]
title = LingoLens Live AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .

# source.include_exts-ში მითითებულია ttf, რათა NotoSansGeorgian.ttf ჩაყოლდეს APK-ში
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,json
version = 1.0.0

# დამატებულია pillow (PIL კადრებისთვის) და აუცილებელი ბიბლიოთეკები
requirements = python3,kivy,openssl,android,pyjnius,websocket-client,requests,certifi,pillow

orientation = portrait
fullscreen = 0

# Android 14+ / API 33+ მიკროფონის, ფონური სერვისისა და შეტყობინებების სრული ნებართვები
android.permissions = INTERNET, RECORD_AUDIO, CAMERA, FOREGROUND_SERVICE, FOREGROUND_SERVICE_MICROPHONE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Android API და NDK პარამეტრები (NDK 25b აუცილებელია Python-for-Android კომპილაციისთვის)
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

# არქიტექტურები
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
