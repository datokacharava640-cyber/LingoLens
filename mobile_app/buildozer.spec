import os

# 1. Colab-ის სისტემური დამოკიდებულებების (Dependencies) ინსტალაცია
print("--- 1/4: სისტემური პაკეტების ინსტალაცია ---")
!sudo apt-get update -y
!sudo apt-get install -y build-essential libsqlite3-dev sqlite3 bzip2 libbz2-dev \
    zlib1g-dev libssl-dev openssl libgdbm-dev libgdbm-compat-dev liblldb-dev \
    libffi-dev libreadline-dev libncursesw5-dev libdb5.3-dev libgdbm-dev \
    sqlite3 libtar-dev libx11-dev libxext-dev libxrender-dev libxext-dev \
    libpng-dev libfreetype6-dev libjpeg-dev libffi-dev libssl-dev libxml2-dev \
    libxslt1-dev zlib1g-dev git openjdk-17-jdk cython3 python3-pip

!pip install --upgrade pip setuptools buildozer

# 2. სამუშაო დირექტორიაში გადასვლა/შექმნა
os.makedirs('/content/mobile_app', exist_ok=True)
%cd /content/mobile_app

# 3. AndroidManifest.tmpl.xml ფაილის შექმნა (Custom Template)
print("--- 2/4: AndroidManifest.tmpl.xml შექმნა ---")
manifest_template = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{{ args.package }}"
    android:versionCode="{{ args.numeric_version }}"
    android:versionName="{{ args.version }}">

    <uses-sdk android:minSdkVersion="{{ args.minapi }}" android:targetSdkVersion="{{ args.api }}" />

    <!-- Permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />

    <application
        android:label="@string/app_name"
        android:icon="@mipmap/icon"
        android:allowBackup="true"
        android:hardwareAccelerated="true">
        
        <activity
            android:name="org.kivy.android.PythonActivity"
            android:label="@string/app_name"
            android:configChanges="orientation|keyboardHidden|screenSize"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

with open('AndroidManifest.tmpl.xml', 'w', encoding='utf-8') as f:
    f.write(manifest_template)

# 4. buildozer.spec ფაილის ჩაწერა
print("--- 3/4: buildozer.spec კონფიგურაცია ---")
spec_content = '''[app]
title = LingoLens Ultra Pro
package.name = lingolens
package.domain = org.lingolens
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json
version = 3.6.0

requirements = python3,kivy,certifi,urllib3,requests,idna,chardet,plyer,pyjnius,edge-tts,asyncio,aiohttp,attrs,multidict,yarl,frozenlist,aiosignal,pvporcupine,pvrecorder

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, CAMERA, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS, VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FOREGROUND_SERVICE, WAKE_LOCK

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True

p4a.fork = kivy
p4a.branch = release-2024.01.21

android.manifest.template = AndroidManifest.tmpl.xml

[buildozer]
log_level = 2
warn_on_root = 1
'''

with open('buildozer.spec', 'w', encoding='utf-8') as f:
    f.write(spec_content)

# 5. Buildozer-ის გაშვება APK-ს დასაგენერირებლად
print("--- 4/4: APK-ის აწყობის დაწყება ---")
!yes | buildozer -v android debug
