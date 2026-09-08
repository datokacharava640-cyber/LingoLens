# 🚀 LingoLens AI Translation App

**LingoLens AI** არის თანამედროვე, მრავალფუნქციური მობილური თარჯიმანი, შექმნილი Python & Kivy framework-ის ბაზაზე. აპლიკაცია უზრუნველყოფს მრავალენოვან Live თარგმნას, ხმოვან ასისტენტს (STT/TTS), ოფლაინ ქეშირებას, კამერის ინტეგრაციასა და სწავლების ინტერაქტიულ ინსტრუმენტებს.

---

## ✨ ძირითადი ფუნქციები

- 🌍 **მრავალენოვანი მხარდაჭერა:** 100-ზე მეტი მსოფლიო ენისა და ქართული ენის სრული მხარდაჭერა.
- ⚡ **Live Translate & Debounce:** ტექსტის რეალურ დროში ავტომატური თარგმნა აკრეფისას (0.5 წამიანი დებოუნსის ლოგიკით UI-ს დასაცავად).
- 💾 **SQLite ოფლაინ ქეშირება & ფავორიტები:** 
  - ნათარგმნი ტექსტების ავტომატური შენახვა ლოკალურ ბაზაში (`lingolens.db`) ინტერნეტის გარეშე ხელახალი გამოყენებისთვის.
  - ფავორიტების სიის მართვა dictionary hub-ში.
- 📷 **Android Camera OCR Integration:** კამერის პირდაპირი გამოძახება ფოტოდან ტექსტის ამოსაცნობად Android OS-ზე (Pyjnius-ის გამოყენებით).
- 🗣️ **STT & TTS (Speech-to-Text / Text-to-Speech):**
  - ხმოვანი შეყვანა და ტექსტის გაჟღერება ენის შესაბამისი აქცენტით.
  - TTS სიჩქარის რეგულირება (0.75x, 1.0x, 1.25x, 1.5x).
- 🧠 **Deep Think (ღრმა ანალიზი):** ტექსტის სტრუქტურული, სიტყვათა რაოდენობისა და კონტექსტური ანალიზი.
- 💬 **ორმხრივი თარჯიმნის რეჟიმი (Interpreter Mode):** დიალოგური რეჟიმი ორ მომხმარებელს შორის კომუნიკაციისთვის.
- 🎓 **ინტერაქტიული ქვიზი (Quiz Mode):** ფავორიტებში შენახული სიტყვების სასწავლო ქვიზები.
- 📄 **ფაილების თარჯიმანი (File Translator):** `.txt` ფორმატის ტექსტური ფაილების წაკითხვა და პირდაპირი თარგმნა.
- 🎨 **ინტერფეისის თემები:** Dynamic animated background (Dark / Light რეჟიმების მხარდაჭერა).
- 📲 **Native Android Sharing & Vibration:** Haptic უკუკავშირი და ტექსტის გაზიარება სხვა აპლიკაციებში (Plyer / Android Intents).

---

## 🛠️ ტექნოლოგიები (Tech Stack)

- **UI Framework:** Kivy / Kivy Language (`.kv`)
- **Programming Language:** Python 3.x
- **Database:** SQLite3 (Local caching, History, Favorites)
- **Android Integration:** Pyjnius (Native Android Intents: Camera, SpeechRecognizer, TTS), Plyer (Vibrator, Share)
- **Networking:** Requests (Google Translate API Endpoints)
- **Multithreading:** `threading.Thread` (ასინქრონული მოთხოვნები UI-ს შეფერხების გარეშე)

---

## 📂 პროექტის სტრუქტურა

```text
LingoLens/
│── main.py              # მთავარი სააპლიკაციო კოდი (UI, SQLite DB, Async Translation, Android Bridge)
│── font.ttf             # ქართული/საერთაშორისო ფონტი
│── lingolens.db         # SQLite ლოკალური მონაცემთა ბაზა (ავტომატურად იქმნება გაშვებისას)
└── README.md            # პროექტის დოკუმენტაცია
