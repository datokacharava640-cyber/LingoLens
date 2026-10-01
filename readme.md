# 🚀 LingoLens AI Translation App

**LingoLens AI** არის თანამედროვე, მრავალფუნქციური მობილური თარჯიმანი, შექმნილი Python & Kivy framework-ის ბაზაზე. აპლიკაცია უზრუნველყოფს მრავალენოვან Live თარგმნას, ხმოვან ასისტენტს (STT/TTS), ოფლაინ ქეშირებას, კამერის ინტეგრაციასა და სწავლების ინტერაქტიულ ინსტრუმენტებს.

---

## ✨ ძირითადი ფუნქციები

* 🌍 **მრავალენოვანი მხარდაჭერა:** 100-ზე მეტი მსოფლიო ენისა და ქართული ენის სრული მხარდაჭერა (სწრაფი ძებნის სისტემით).
* ⚡ **Live Translate & Debounce:** ტექსტის რეალურ დროში ავტომატური თარგმნა აკრეფისას (0.5 წამიანი დებოუნსის ლოგიკით UI-ის დასაცავად).
* 🪟 **Floating Overlay Window (მცურავი ფანჯარა):** Android-ის Native Overlay მხარდაჭერა სხვა აპლიკაციების თავზე სწრაფი თარგმნისთვის.
* 🧠 **Deep Think Analysis:** ტექსტის ღრმა სტატისტიკური ანალიზი, სიტყვების, სიმბოლოებისა და ენის სტრუქტურის შეფასება.
* 🤖 **Hybrid Online/Offline Engine:** ონლაინ API-ის შეფერხებისას ავტომატური გადართვა ლოკალურ ONNX AI თარჯიმნის ძრავზე.
* 💾 **SQLite მონაცემთა ბაზა:** ისტორიისა და ფავორიტი სიტყვების უსაფრთხო, ლოკალური შენახვა.
* 🎙️ **Real-time დიალოგი & TTS:** ხმოვანი გაჟღერება ნატიური Android Text-to-Speech (TTS) მხარდაჭერით.
* 🎓 **ინტერაქტიული ქვიზები:** შენახული ფავორიტი სიტყვების ბაზაზე დაფუძნებული საგანმანათლებლო ტესტები.
* 🔗 **Native Share & Clipboard:** ტექსტის სწრაფი კოპირება და გაზიარება Android Intent-ების გამოყენებით.

---

## 🛠️ ტექნოლოგიური სტეკი

* **Language:** Python 3
* **UI Framework:** Kivy / KivyMD
* **Android Integration:** Pyjnius, Android NDK/SDK, Java/Android APIs
* **AI & Machine Learning:** ONNX Runtime, NumPy, Google ML Kit (Text Recognition)
* **Database:** SQLite3
* **Build System:** Buildozer & GitHub Actions CI/CD

---

## 📦 დაყენება და ინსტალაცია

### 1. რეპოზიტორიის კლონირება
```bash
git clone [https://github.com/datokacharava640-cyber/LingoLens.git](https://github.com/datokacharava640-cyber/LingoLens.git)
cd LingoLens
