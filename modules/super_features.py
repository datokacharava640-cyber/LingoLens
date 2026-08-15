import json
import os
import requests
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.core.clipboard import Clipboard

HISTORY_FILE = "translation_history.json"

# =====================================================================
# 1. ISTORIAS DA FAVORTIBIS LOGIKA
# =====================================================================
def save_to_history(original, translated, is_favorite=False):
    history = load_history()
    history.append({
        "original": original,
        "translated": translated,
        "favorite": is_favorite
    })
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"History Save Error: {e}")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# =====================================================================
# 2. INTERFEISI: KHUTIVE FUNQCIA ERT POPUP-SHI
# =====================================================================
def open_super_features(main_app):
    layout = BoxLayout(orientation='vertical', padding=10, spacing=8)

    # 1️⃣ Voice Speed Control
    layout.add_widget(Label(text="🔊 ხმის სიჩქარის რეგულირება (0.5x - 2.0x)", size_hint_y=0.08))
    speed_slider = Slider(min=0.5, max=2.0, value=1.0, step=0.1, size_hint_y=0.08)
    layout.add_widget(speed_slider)

    # 2️⃣ Smart Clipboard Auto-Translate
    clip_btn = Button(text="📋 ბუფერში დაკოპირებულის თარგმნა", size_hint_y=0.1, background_color=(0.2, 0.6, 0.8, 1))
    layout.add_widget(clip_btn)

    # 3️⃣ AI Grammar & Style Checker
    grammar_btn = Button(text="✍️ გრამატიკის შემოწმება (Gemini AI)", size_hint_y=0.1, background_color=(0.8, 0.4, 0.2, 1))
    layout.add_widget(grammar_btn)

    # 4️⃣ PDF / Document Reader Simulation
    doc_btn = Button(text="📄 დოკუმენტის/ტექსტის დამუშავება", size_hint_y=0.1, background_color=(0.3, 0.7, 0.4, 1))
    layout.add_widget(doc_btn)

    # 5️⃣ Translation History & Favorites
    hist_btn = Button(text="⭐ ისტორია და ფავორიტები", size_hint_y=0.1, background_color=(0.6, 0.3, 0.7, 1))
    layout.add_widget(hist_btn)

    close_btn = Button(text="დახურვა", size_hint_y=0.08)
    layout.add_widget(close_btn)

    popup = Popup(title="LingoLens Super Features", content=layout, size_hint=(0.9, 0.85))

    # --- LOGIC & BINDINGS ---
    def apply_clip(instance):
        clip_text = Clipboard.paste()
        if clip_text:
            main_app.text_input.text = clip_text
            main_app.translate_text(None)
            save_to_history(clip_text, main_app.output_label.text)
            popup.dismiss()

    def check_grammar(instance):
        txt = main_app.text_input.text.strip()
        if not txt:
            main_app.status_label.text = "შეიყვანეთ ტექსტი გრამატიკისთვის!"
            return
        if main_app.api_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={main_app.api_key}"
            payload = {"contents": [{"parts": [{"text": f"Correct the grammar and explain errors in Georgian: {txt}"}]}]}
            try:
                res = requests.post(url, json=payload, timeout=10).json()
                result = res['candidates'][0]['content']['parts'][0]['text']
                main_app.output_label.text = result
                popup.dismiss()
            except Exception as e:
                main_app.status_label.text = f"შეცდომა: {e}"

    def show_history(instance):
        hist_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        history_data = load_history()
        for item in history_data:
            lbl = Label(
                text=f"• {item['original']} ➔ {item['translated']}", 
                size_hint_y=None, 
                height=40,
                color=(0.9, 0.9, 0.9, 1)
            )
            content.add_widget(lbl)

        scroll.add_widget(content)
        hist_layout.add_widget(scroll)
        
        close_hist = Button(text="დახურვა", size_hint_y=0.1)
        hist_layout.add_widget(close_hist)
        
        hist_popup = Popup(title="თარგმანების ისტორია", content=hist_layout, size_hint=(0.85, 0.7))
        close_hist.bind(on_press=hist_popup.dismiss)
        hist_popup.open()

    clip_btn.bind(on_press=apply_clip)
    grammar_btn.bind(on_press=check_grammar)
    hist_btn.bind(on_press=show_history)
    close_btn.bind(on_press=popup.dismiss)

    popup.open()

def start():
    pass
