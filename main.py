import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.utils import platform

# Android-ზე ნებართვების მოთხოვნა გაშვებისთანავე
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.INTERNET,
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.READ_PHONE_STATE,
        Permission.RECEIVE_SMS,
        Permission.READ_SMS,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])

class LingoLensMain(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        # ფონტის შემოწმება
        font_path = 'font.ttf' if os.path.exists('font.ttf') else 'Roboto'

        # სათაური
        self.add_widget(Label(
            text='LingoLens - Real-Time AI Translator',
            font_size='22sp',
            bold=True,
            size_hint_y=0.2
        ))

        # სტატუსის ეტიკეტი (ქართული ფონტით)
        self.status_label = Label(
            text='სისტემა მზადაა რეალურ დროში თარგმნისთვის',
            font_name=font_path,
            font_size='18sp',
            size_hint_y=0.4
        ))
        self.add_widget(self.status_label)

        # ტესტური ღილაკი
        btn = Button(
            text='თარგმნის დაწყება',
            font_name=font_path,
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 1, 1)
        )
        btn.bind(on_press=self.on_start)
        self.add_widget(btn)

    def on_start(self, instance):
        font_path = 'font.ttf' if os.path.exists('font.ttf') else 'Roboto'
        self.status_label.text = 'მიკროფონი და კამერა გააქტიურებულია!'

class LingoLensApp(App):
    def build(self):
        return LingoLensMain()

if __name__ == '__main__':
    LingoLensApp().run()
