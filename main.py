from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import platform

class LingoLensDesktopApp(App):
    def build(self):
        root = FloatLayout()
        
        # ვამოწმებთ, ირთვება თუ არა ძირითადი ღილაკი
        btn = Button(
            text="LingoLens მუშაობს!\nდააჭირე ტესტისთვის", 
            size_hint=(0.8, 0.3), 
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            font_size=18
        )
        btn.bind(on_press=self.test_click)
        root.add_widget(btn)
        return root

    def test_click(self, instance):
        instance.text = "შესანიშნავია! აპი მუშაობს."

if __name__ == "__main__":
    LingoLensDesktopApp().run()
