[app]
title = LingoLens
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0
android.permissions = INTERNET

android.api = 33
android.minapi = 24
android.ndk = 25b

android.enable_androidx = True
android.accept_sdk_license = True
android.archs = arm64-v8a

# p4a-ს აქტიური შტო გასწორებული ბმულებით:
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 0
