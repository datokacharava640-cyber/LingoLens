from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class LingoLensApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        lbl = Label(
            text='LingoLens Working!',
            font_size='24sp',
            bold=True
        )
        layout.add_widget(lbl)
        
        btn = Button(
            text='Click Test',
            font_size='18sp',
            size_hint_y=0.3
        )
        btn.bind(on_press=lambda x: setattr(lbl, 'text', 'Button Clicked Successfully!'))
        layout.add_widget(btn)
        
        return layout


if __name__ == '__main__':
    LingoLensApp().run()
