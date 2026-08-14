from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

def start():
    layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
    
    phrases = [
        "🆘 მჭირდება დახმარება! / I need help!",
        "🏥 სადაა უახლოესი საავადმყოფო? / Where is the hospital?",
        "👮 გამოიძახეთ პოლიცია! / Call the police!",
        "📍 დავიკარგე / I am lost"
    ]
    
    for p in phrases:
        layout.add_widget(Label(text=p, font_size='14sp'))
        
    close_btn = Button(text="დახურვა", size_hint_y=0.2)
    layout.add_widget(close_btn)
    
    popup = Popup(title="Travel SOS - გადაუდებელი ფრაზები", content=layout, size_hint=(0.9, 0.6))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def run():
    start()
