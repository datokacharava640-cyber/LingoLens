from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

def start():
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    
    lbl = Label(
        text="Design & Customization\n\nმორგება: Cyber Dark Theme, შრიფტის ზომები და ინტერფეისის სტილი.",
        font_size='14sp',
        halign='center'
    )
    
    theme_btn = Button(text="თემის შეცვლა (Dark / Light)", size_hint_y=0.25)
    close_btn = Button(text="დახურვა", size_hint_y=0.2)
    
    layout.add_widget(lbl)
    layout.add_widget(theme_btn)
    layout.add_widget(close_btn)
    
    popup = Popup(title="Design & Tools", content=layout, size_hint=(0.9, 0.5))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def run():
    start()
