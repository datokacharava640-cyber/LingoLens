from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

def start():
    content = BoxLayout(orientation='vertical', padding=10, spacing=10)
    content.add_widget(Label(text="LingoLens Floating Bubble\nაქტიურია სხვა აპების ზემოდან!"))
    
    close_btn = Button(text="დახურვა", size_hint_y=0.3)
    content.add_widget(close_btn)
    
    popup = Popup(title="LingoLens Bubble", content=content, size_hint=(0.8, 0.4))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def run():
    start()
