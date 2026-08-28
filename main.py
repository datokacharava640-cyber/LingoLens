import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class LingoLensApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.lbl = Label(
            text="LingoLens Ultra Pro v3.3.0\nReady to Build",
            halign="center"
        )
        layout.add_widget(self.lbl)

        btn = Button(text="Test Button", size_hint=(1, 0.2))
        btn.bind(on_press=self.on_click)
        layout.add_widget(btn)

        return layout

    def on_click(self, instance):
        self.lbl.text = "App is Working fine!"

if __name__ == "__main__":
    LingoLensApp().run()
