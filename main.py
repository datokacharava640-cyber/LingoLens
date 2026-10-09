from kivy.app import App
from kivy.uix.label import Label

class LingoLensApp(App):
    def build(self):
        return Label(
            text="ტესტი: აპლიკაცია გაშვებულია!", 
            font_size=24,
            font_name="font.ttf"  # მივუთითეთ ქართული შრიფტი, რომელიც პროექტის папკაშია
        )

if __name__ == '__main__':
    LingoLensApp().run()
