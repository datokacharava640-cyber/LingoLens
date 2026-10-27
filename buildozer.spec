ERROR: charset-normalizer-3.5.2-cp314-cp314-android_24_arm64_v8a.whl is not a supported wheel on this platform.
```[cite: 30, 31]

### 🔍 რა იწვევს ამას?
როდესაც `python-for-android` იწერება უშუალოდ Git-იდან (მთავარი `master` ბრენჩიდან), მისი უახლესი ვერსია ავტომატურად გადართულია **Python 3.14**-ზე (`cp314`). რადგან პითონის ეს ვერსია ძალიან ახალია, ანდროიდის პლატფორმისთვის საჭირო ბიბლიოთეკები (როგორიცაა `charset-normalizer`) ჯერ არ არის მხარდაჭერილი ამ ვერსიაზე და ბილდი იჭრება[cite: 30, 31].

---

### 🛠️ როგორ მოვაგვაროთ?

იმისათვის, რომ ბილდმა მკაცრად გამოიყენოს **Python 3.10** და თავიდან ავიცილოთ 3.14-ის კონფლიქტი, საჭიროა:
1. `.github/workflows/build.yml` ფაილში `python-for-android` დავაინსტალიროთ არა Git-იდან, არამედ მის სტაბილურ ვერსიაზე (`2024.1.21`), რომელიც სრულად მუშაობს Python 3.10-ზე.
2. `buildozer.spec` ფაილში მკაცრად მივუთითოთ პითონის ვერსია.

#### 1. განაახლეთ `.github/workflows/build.yml` ფაილი:

```yaml
name: Build Android APK

on:
  push:
    branches: [ "main", "master" ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-22.04

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Cache Buildozer global directory
        uses: actions/cache@v4
        with:
          path: ~/.buildozer
          key: buildozer-v10-${{ hashFiles('buildozer.spec') }}-${{ runner.os }}

      - name: Install System Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            git zip unzip openjdk-17-jdk autoconf libtool pkg-config \
            zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev \
            libsqlite3-dev libssl-dev libffi-dev liblzma-dev

      - name: Install Buildozer, Cython & Python-for-Android
        run: |
          python -m pip install --upgrade pip
          pip install "Cython==0.29.36" "buildozer==1.5.0" "python-for-android==2024.1.21"

      - name: Clean Old Build Cache & Env
        run: |
          rm -rf ~/.buildozer/android/platform/android-ndk-r23b
          unset ANDROIDNDK

      - name: Build APK with Buildozer
        env:
          CFLAGS: "-w"
          CXXFLAGS: "-w"
        run: |
          buildozer -v android debug

      - name: Upload APK Artifact
        uses: actions/upload-artifact@v4
        with:
          name: LingoLens-APK
          path: bin/*.apk
