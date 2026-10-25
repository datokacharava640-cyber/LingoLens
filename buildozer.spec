[app]

title = LingoLens AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
icon.filename = %(source.dir)s/icon.png
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json,wav,xml,html,md,txt
# source.include_patterns დროებით დაკომენტარებულია მანიფესტთან კონფლიქტის თავიდან ასაცილებლად
source.exclude_dirs = tests, bin, venv, .git, .github, Google Colab
source.exclude_patterns = Dockerfile, vercel.json, setup.py, *.ipynb, .env, .gitignore

version = 6.0.5

requirements = python3,kivy,plyer,pyjnius,setuptools,requests,urllib3,certifi,idna

# ვუთითებთ პითონის ზუსტ ვერსიას და p4a-ს სტაბილურ თეგს (პრეფიქსის გარეშე)
p4a.python_version = 3.10

orientation = portrait
fullscreen = 0

# სრული პერმისიები: კამერა, მიკროფონი, ინტერნეტი, ქსელი, მეხსიერება და ფიჭური ზარები/ტელეფონია
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, CALL_PHONE, READ_PHONE_STATE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.accept_sdk_license = True
android.uses_cleartext_traffic = true
android.enable_androidx = True
android.enable_jetifier = True
android.archs = arm64-v8a
android.allow_backup = True
android.release_artifact = apk
android.optimize_python = False
android.manifest.launch_mode = singleTask

[buildozer]
log_level = 5
warn_on_root = 0
