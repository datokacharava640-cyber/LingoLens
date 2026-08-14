from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

def start():
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    
    streak_lbl = Label(
        text="🔥 შენი Streak: 1 დღე!\n\nყოველდღე გამოიყენე LingoLens, რომ არ დაკარგო პროგრესი!",
        font_size='16sp',
        halign='center'
    )
    
    close_btn = Button(text="სუპერ! / დახურვა", size_hint_y=0.25)
    
    layout.add_widget(streak_lbl)
    layout.add_widget(close_btn)
    
    popup = Popup(title="Daily Streak Tracker", content=layout, size_hint=(0.85, 0.45))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def run():
    start()
