from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label

def summarize_text(inp_widget, out_widget):
    txt = inp_widget.text.strip()
    if not txt:
        out_widget.text = "გთხოვთ ჩასვათ ტექსტი!"
        return
    
    # AI შეჯამების ლოგიკის შაბლონი
    out_widget.text = f"📄 ტექსტის რეზიუმე:\nტექსტი შეიცავს {len(txt.split())} სიტყვას.\nმთავარი აზრი: [AI-მ დაამუშავა ტექსტი და გამოყო საკვანძო პუნქტები]."

def start():
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    
    inp = TextInput(hint_text="ჩასვით დიდი ტექსტი შეჯამებისთვის...", multiline=True, size_hint_y=0.4)
    btn = Button(text="📝 ტექსტის შეჯამება (Summarize)", size_hint_y=0.2)
    out = Label(text="შედეგი გამოჩნდება აქ", size_hint_y=0.4)
    
    btn.bind(on_press=lambda x: summarize_text(inp, out))
    
    layout.add_widget(inp)
    layout.add_widget(btn)
    layout.add_widget(out)
    
    popup = Popup(title="Doc Summarizer", content=layout, size_hint=(0.9, 0.6))
    popup.open()

def run():
    start()
