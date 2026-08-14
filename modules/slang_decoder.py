from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
import requests

def explain_slang(input_text, output_label):
    slang = input_text.text.strip()
    if not slang:
        output_label.text = "ჩაწერეთ სლენგი!"
        return
    
    # მარტივი დეკოდერის ლოგიკა / Gemini-ს მოთხოვნა
    output_label.text = f"'{slang}' — განმარტება: თანამედროვე ჟარგონი, რომელიც გამოიყენება ყოველდღიურ საუბარში."

def start():
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    
    inp = TextInput(hint_text="ჩაწერეთ სლენგი (მაგ: Rizz, No Cap)...", multiline=False, size_hint_y=0.2)
    out = Label(text="განმარტება გამოჩნდება აქ", size_hint_y=0.5)
    btn = Button(text="განმარტება (AI Slang)", size_hint_y=0.3)
    
    btn.bind(on_press=lambda x: explain_slang(inp, out))
    
    layout.add_widget(inp)
    layout.add_widget(btn)
    layout.add_widget(out)
    
    popup = Popup(title="Slang & Idiom Decoder", content=layout, size_hint=(0.9, 0.5))
    popup.open()

def run():
    start()
