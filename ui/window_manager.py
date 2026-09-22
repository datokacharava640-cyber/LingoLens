from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
import config

class MovableWindow(ScatterLayout):
    def __init__(self, title="ფანჯარა", content_widget=None, **kwargs):
        super().__init__(**kwargs)
        
        # პარამეტრები: ზომის შეცვლა და გადაადგილება
        self.do_rotation = False   # როტაციის გათიშვა (რომ არ დატრიალდეს)
        self.do_scale = True      # გადიდება / დაპატარავება (Zoom)
        self.do_translation = True# ეკრანზე გადაადგილება
        
        self.size_hint = (None, None)
        self.size = (320, 420)
        
        # ფანჯრის ძირითადი ბლოკი
        main_box = BoxLayout(orientation='vertical', spacing=2, padding=5)
        
        # ფანჯრის ზედა ზოლი (Header)
        header = BoxLayout(size_hint_y=None, height=40, spacing=5)
        title_label = Label(
            text=title, 
            font_name=getattr(config, 'FONT_PATH', None),
            bold=True
        )
        btn_close = Button(
            text="X", 
            size_hint_x=None, 
            width=40, 
            on_press=self.close_window
        )
        
        header.add_widget(title_label)
        header.add_widget(btn_close)
        main_box.add_widget(header)
        
        # შიგთავსი (თარგმანი, გრამატიკა, კამერა და ა.შ.)
        if content_widget:
            main_box.add_widget(content_widget)
            
        self.add_widget(main_box)

    def close_window(self, instance):
        if self.parent:
            self.parent.remove_widget(self)
