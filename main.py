from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

class LingoLensDesktopApp(App):
    def build(self):
        root = FloatLayout()
        btn = Button(text="Test Working!", size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        root.add_widget(btn)
        return root

if __name__ == "__main__":
    LingoLensDesktopApp().run()
