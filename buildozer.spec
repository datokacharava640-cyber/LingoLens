[app]

title = LingoLens AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json,wav,xml,html,md,txt
version = 6.0.8

requirements = python3,kivy,pyjnius,plyer,android,charset_normalizer==3.3.2,certifi

orientation = portrait
fullscreen = 0

# ანდროიდის აბსოლუტურად სრული სისტემური, ჰარვარდული და ფონური ნებართვები
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, CHANGE_WIFI_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE, CALL_PHONE, READ_PHONE_STATE, PROCESS_OUTGOING_CALLS, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, ACCESS_BACKGROUND_LOCATION, BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, VIBRATE, WAKE_LOCK, MODIFY_AUDIO_SETTINGS, READ_CONTACTS, WRITE_CONTACTS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, FOREGROUND_SERVICE, RECEIVE_BOOT_COMPLETED

android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.accept_sdk_license = True
android.uses_cleartext_traffic = true
android.enable_androidx = True
android.enable_jetifier = True
android.archs = arm64-v8a

p4a.python_version = 3.11
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
