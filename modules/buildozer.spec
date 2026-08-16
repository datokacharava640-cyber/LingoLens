[app]

# (str) Title of your application
title = LingoLens Ultra Pro

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android packaging)
package.domain = org.lingolens.app

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (include Georgian fonts, py, kv files)
source.include_exts = py,png,jpg,kv,atlas,ttf,otf

# (list) Application requirements
# requests, urllib3, charset_normalizer, idna, certifi essential for Gemini API & SQLite
requirements = python3,kivy==2.3.0,requests,urllib3,charset_normalizer,idna,certifi,pypdf,plyer,android,pyopenssl

# (str) Custom source folders for requirements
source.include_patterns = assets/*,modules/*,*.ttf

# (str) Application versioning
version = 1.0.0

# (list) Permissions
android.permissions = INTERNET,CAMERA,RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,SYSTEM_ALERT_WINDOW,POST_NOTIFICATIONS,FOREGROUND_SERVICE

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (int) Android SDK version
android.sdk = 33

# (str) Android NDK version
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android orientation (portrait, landscape or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) List of service to declare
# android.services = OverlayService:service.py

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1
