import json
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner

FLASHCARDS_FILE = "flashcards.json"

def open_next_gen_features(main_app):
    layout = BoxLayout(orientation='vertical', padding=10, spacing=8)

    layout.add_widget(Label(text="🚀 Next-Gen AI ინსტრუმენტები", font_size='16sp', size_hint_y=0.08))

    # 1️⃣ Dialect & Accent Adapter
    layout.add_widget(Label(text="🎯 აირჩიეთ აქცენტი / დიალექტი:", size_hint_y=0.06))
    accent_spinner = Spinner(
        text="English (US)",
        values=["English (US)", "English (UK)", "English (AU)", "Deutsch (DE)", "Español (ES)"],
        size_hint_y=0.08
    )
    layout.add_widget(accent_spinner)

    # 2️⃣ AI Flashcards & Quiz
    cards_btn = Button(
        text="🎴 Flashcards & სიტყვების სავარჯიშო", 
        size_hint_y=0.1, 
        background_color=(0.2, 0.7, 0.5, 1)
    )
    layout.add_widget(cards_btn)

    # 3️⃣ Offline Voice Translator
    offline_voice_btn = Button(
        text="🎙️ ოფლაინ ხმოვანი თარგმანი", 
        size_hint_y=0.1, 
        background_color=(0.3, 0.4, 0.8, 1)
    )
    layout.add_widget(offline_voice_btn)

    # 4️⃣ Smart OCR Scene Detection
    scene_btn = Button(
        text="👁️ ჭკვიანი OCR & ობიექტების ამოცნობა", 
        size_hint_y=0.1, 
        background_color=(0.8, 0.5, 0.2, 1)
    )
    layout.add_widget(scene_btn)

    # 5️⃣ Quick Launcher Widget
    widget_btn = Button(
        text="⚡ სწრაფი წვდომის ვიჯეტის ჩართვა", 
        size_hint_y=0.1, 
        background_color=(0.6, 0.2, 0.7, 1)
    )
    layout.add_widget(widget_btn)

    close_btn = Button(text="დახურვა", size_hint_y=0.08)
    layout.add_widget(close_btn)

    popup = Popup(title="LingoLens Next-Gen Modules", content=layout, size_hint=(0.9, 0.85))

    # --- ლოგიკა ---
    def save_flashcard(instance):
        txt = main_app.text_input.text.strip()
        trans = main_app.output_label.text.strip()
        if txt and trans and not trans.startswith("["):
            cards = []
            if os.path.exists(FLASHCARDS_FILE):
                try:
                    with open(FLASHCARDS_FILE, 'r', encoding='utf-8') as f:
                        cards = json.load(f)
                except: pass
            cards.append({"word": txt, "translation": trans})
            with open(FLASHCARDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(cards, f, ensure_ascii=False, indent=2)
            main_app.status_label.text = "სიტყვა დაემატა Flashcards-ში!"
        else:
            main_app.status_label.text = "ჯერ ჯერობით არაფერია ნათარგმნი!"

    cards_btn.bind(on_press=save_flashcard)
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def start():
    pass
