[app]

title = LingoLens Live AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,json
version = 1.0.0

# დამოკიდებულებები
requirements = python3,kivy==2.3.0,pyjnius,websocket-client,requests

# p4a-ის სტაბილური ბრენჩი Python 3.11-ისთვის
p4a.branch = release-2024.01.21

orientation = portrait
fullscreen = 0

# Android სისტემური ნებართვები
android.permissions = INTERNET, RECORD_AUDIO, CAMERA, WAKE_LOCK, POST_NOTIFICATIONS, FOREGROUND_SERVICE

# აპარატურული ფუნქციები
android.features = android.hardware.camera, android.hardware.microphone

android.wakelock = True
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
