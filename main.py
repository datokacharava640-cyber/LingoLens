from kivy.app import App
from kivy.uix.label import Label

class LingoLensApp(App):
    def build(self):
        return Label(text="ტესტი: აპლიკაცია გაშვებულია!", font_size=24)

if __name__ == '__main__':
    LingoLensApp().run()
