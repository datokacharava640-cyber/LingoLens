[app]

# აპლიკაციის დასახელება
title = LingoLens Ultra Pro

# პაკეტის სახელი (მხოლოდ პატარა ინგლისური ასოები)
package.name = lingolens

# დომენი (შეეგიძლია დატოვო org.test ან შეცვალო)
package.domain = org.test

# ფაილების დირექტორია (სადაც main.py იმყოფება)
source.dir = .

# გაფართოებები, რომლებიც უნდა ჩაერთოს APK-ში
source.include_exts = py,png,jpg,kv,atlas,json,ttf

# აპლიკაციის ვერსია
version = 1.0.0

# დამოკიდებულებები (Python ბიბლიოთეკები)
requirements = python3,kivy==2.3.0,pillow,requests,urllib3,certifi

# ეკრანის ორიენტაცია (portrait, landscape, ან all)
orientation = portrait

# სრული ეკრანი (1 = დიახ, 0 = არა)
fullscreen = 0

# Android ნებართვები (Permissions)
android.permissions = INTERNET,CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Android API ვერსიები
android.api = 33
android.minapi = 21

# AndroidX მხარდაჭერა (თანამედროვე ბიბლიოთეკებისთვის აუცილებელია)
android.enable_androidx = True

# არქიტექტურები (arm64-v8a არის თანამედროვე 64-ბიტიანი მოწყობილობებისთვის)
android.archs = arm64-v8a, armeabi-v7a

# Splash screen და Icon (თუ გაქვს ფაილები, მოხსენი კომენტარი)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/splash.png

[buildozer]

# ლოგირების დონე (2 = დეტალური ლოგები შეცდომების საპოვნელად)
log_level = 2

# Warning root მომხმარებელზე
warn_on_root = 1
