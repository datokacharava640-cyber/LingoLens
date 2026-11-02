# (str) Title of your application
title = LingoLens AI

# (str) Package name
package.name = lingolens

# (str) Package domain (needed for android packaging)
package.domain = org

# (list) Source files to include (let it empty to include all files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (list) Application requirements
# ჩაწერეთ მხოლოდ ეს მინიმალური და აუცილებელი ბიბლიოთეკები:
requirements = python3,kivy,plyer,android,pyjnius

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET, CAMERA, RECORD_AUDIO, CALL_PHONE

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 24

# Python version and branch
p4a.python_version = 3.11
p4a.branch = master
