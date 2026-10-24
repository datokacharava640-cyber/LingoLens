[app]

title = LingoLens AI
package.name = lingolens
package.domain = org.lingolens
source.dir = .
icon.filename = %(source.dir)s/icon.png
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json,wav,xml,html,md,txt
source.include_patterns = *.py, *.html, api/*, res/*, *.png, *.ttf, *.md, *.txt
source.exclude_dirs = tests, bin, venv, .git, .github, Google Colab
source.exclude_patterns = Dockerfile, vercel.json, setup.py, *.ipynb, .env, .gitignore

version = 6.0.2

# ამოღებულია ზუსტი ვერსიის შეზღუდვა და გამოყენებულია სტანდარტული python3
requirements = python3,kivy,plyer,pyjnius,setuptools,requests,urllib3,certifi,idna

# ვუთითებთ პითონის იმ ვერსიას, რასაც master ბრენჩი იყენებს (3.14)
p4a.python_version = 3.14

orientation = portrait
fullscreen = 0

android.permissions = CAMERA, RECORD_AUDIO, INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 28c
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
log_level = 2
warn_on_root = 0
