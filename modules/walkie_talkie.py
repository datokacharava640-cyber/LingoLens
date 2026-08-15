from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

def start():
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    
    lbl = Label(
        text="Walkie Talkie რეჟიმი\n\nდააჭირეთ ღილაკს და ისაუბრეთ. AI გადათარგმნის მეორე ენაზე!",
        font_size='15sp',
        halign='center'
    )
    
    talk_btn1 = Button(text="მიკროფონი: პირი A (ქართული)", size_hint_y=0.25)
    talk_btn2 = Button(text="მიკროფონი: პირი B (English)", size_hint_y=0.25)
    close_btn = Button(text="დახურვა", size_hint_y=0.2)
    
    layout.add_widget(lbl)
    layout.add_widget(talk_btn1)
    layout.add_widget(talk_btn2)
    layout.add_widget(close_btn)
    
    popup = Popup(title="Walkie Talkie Live Dialog", content=layout, size_hint=(0.9, 0.6))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def run():
    start()
