from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label

def translate_sms(input_text, from_lang, to_lang, output_label):
    sms = input_text.text.strip()
    if not sms:
        output_label.text = "ჩაწერეთ ან ჩასვით SMS ტექსტი!"
        return
    output_label.text = f"[{from_lang.text} ➔ {to_lang.text}]: {sms} (ნათარგმნია)"

def start():
    layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
    
    # ენების არჩევის პანელი
    lang_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.15)
    
    languages = ["ქართული", "English", "Русский", "Deutsch", "Français", "Español"]
    
    from_spinner = Spinner(text="ქართული", values=languages)
    switch_btn = Button(text="⇄", size_hint_x=0.2)
    to_spinner = Spinner(text="English", values=languages)
    
    # ენების ადგილების გაცვლა
    def switch_languages(instance):
        from_spinner.text, to_spinner.text = to_spinner.text, from_spinner.text

    switch_btn.bind(on_press=switch_languages)

    lang_layout.add_widget(from_spinner)
    lang_layout.add_widget(switch_btn)
    lang_layout.add_widget(to_spinner)

    # ტექსტის ველები
    inp = TextInput(hint_text="ჩასვით SMS ტექსტი...", multiline=True, size_hint_y=0.35)
    out = Label(text="ნათარგმნი SMS გამოჩნდება აქ", size_hint_y=0.3)
    
    trans_btn = Button(text="SMS-ის თარგმნა", size_hint_y=0.12)
    trans_btn.bind(on_press=lambda x: translate_sms(inp, from_spinner, to_spinner, out))

    close_btn = Button(text="დახურვა", size_hint_y=0.1)

    layout.add_widget(lang_layout)
    layout.add_widget(inp)
    layout.add_widget(trans_btn)
    layout.add_widget(out)
    layout.add_widget(close_btn)

    popup = Popup(title="SMS Translator with Language Switcher", content=layout, size_hint=(0.95, 0.7))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def run():
    start()
