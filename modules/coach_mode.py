from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

def start():
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    
    title_lbl = Label(text="AI Coach - დღის გაკვეთილი", font_size='16sp', size_hint_y=0.2)
    tip_lbl = Label(
        text="დღის რჩევა:\nგამოიყენეთ 'Would you mind...' როცა გსურთ ზრდილობიანი თხოვნა.\n\nმაგალითად: 'Would you mind closing the door?'",
        size_hint_y=0.6,
        halign='center'
    )
    
    close_btn = Button(text="გავიგე / დახურვა", size_hint_y=0.2)
    
    layout.add_widget(title_lbl)
    layout.add_widget(tip_lbl)
    layout.add_widget(close_btn)
    
    popup = Popup(title="LingoLens Coach Mode", content=layout, size_hint=(0.9, 0.5))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def run():
    start()
