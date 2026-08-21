[app]
title = LingoLens
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0.0

# დატოვებულია მხოლოდ ბაზისური მოთხოვნები:
requirements = python3,kivy

orientation = portrait
fullscreen = 0
android.permissions = INTERNET

android.api = 33
android.minapi = 24
android.ndk = 25.2.9519653
android.sdk_path = /usr/local/lib/android/sdk
android.ndk_path = /usr/local/lib/android/sdk/ndk/25.2.9519653

android.enable_androidx = True
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 0
