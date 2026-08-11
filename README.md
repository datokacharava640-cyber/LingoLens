# 🇬🇪 LingoLens Live AI

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Kivy-green.svg)
![Python](https://img.shields.io/badge/Python-3.10-yellow.svg)
![Engine](https://img.shields.io/badge/AI Engine-Gemini%202.0%20Flash%20Live-orange.svg)

**LingoLens Live AI** არის რეალური დროის მულტიმოდალური ხელოვნური ინტელექტის ასისტენტი და თარჯიმანი Android მოწყობილობებისთვის. აპლიკაცია ახორციელებს ხმისა და ვიდეო ნაკადის ორმხრივ მყისიერ თარგმნას Gemini Live WebSocket პროტოკოლის გამოყენებით.

---

## 👤 ავტორი და პროექტის ინფორმაცია

* **ავტორი / დამფუძნებელი:** დავით კაჭარავა (Davit Kacharava)
* **ქვეყანა:** საქართველო (Georgia) 🇬🇪
* **შექმნის თარიღი:** 11 აგვისტო, 2026 წელი (August 11, 2026)
* **ვერსია:** `1.0.0 (Production Ready)`
* **ლიცენზია:** MIT License

---

## ✨ ძირითადი ფუნქციონალი

1. **🎙️ Real-time Bi-directional Voice Translate:**
   * 16kHz Audio input & 24kHz Low-latency PCM stream.
   * VAD (Voice Activity Detection) და ექოს ჩახშობის (Acoustic Echo Cancellation) მხარდაჭერა.
2. **📷 Live Cam Context Translator:**
   * კადრების ავტომატური დამუშავება RAM-ში (In-Memory Processing PIL/Pillow-ით) 2 წამიანი ინტერვალით.
3. **⚡ Low-Latency WebSocket Engine:**
   * Gemini Multimodal Live API (`models/gemini-2.0-flash-exp`) პირდაპირი ნაკადური მიერთება.
   * Auto Reconnect (Exponential Backoff) ქსელის გაწყვეტისას ($1s \rightarrow 32s$).
4. **⛔ Barge-in / Interrupt Signal:**
   * AI-ს საუბრის მყისიერი შეწყვეტის მხარდაჭერა WebSocket `clientContent` გაუქმების პაკეტით.
5. **🔔 Android Background Service & Notification:**
   * Native Android Foreground Service (Android 14 / API 34 თავსებადი) მუდმივი Status Bar Notification-ით, რაც გამორიცხავს პროცესორის/მიკროფონის გათიშვას ჩაკეცვისას.
6. **🇬🇪 Georgian Font Support:**
   * `NotoSansGeorgian.ttf` ინტეგრაცია Kivy UI-ში ქართული ასოების სრული მხარდაჭერისთვის.

---

## 🛠️ ტექნოლოგიური სტეკი (Tech Stack)

* **Language:** Python 3.10
* **Framework:** Kivy
* **Native Android Interface:** PyJnius (Java Class Mapping)
* **API:** Google Gemini Multimodal Live API (WebSocket)
* **Build System:** Buildozer / Python-for-Android (NDK 25b, API 33)
* **CI/CD:** GitHub Actions Auto-Builder

---

## 📂 პროექტის სტრუქტურა

```text
LingoLens/
├── .github/
│   └── workflows/
│       └── build.yml             # GitHub Actions CI/CD (APK Builder)
├── main.py                       # აპლიკაციის ძირითადი კოდი & UI
├── service.py                    # Android Background Foreground Service
├── buildozer.spec                # Buildozer Android კონფიგურაცია
├── NotoSansGeorgian.ttf          # ქართული შრიფტი
├── LICENSE                       # MIT იურიდიული ლიცენზია
└── README.md                     # პროექტის დოკუმენტაცია
