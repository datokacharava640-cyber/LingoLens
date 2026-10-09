from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
import threading
from network_helper import check_server_health, send_data_to_server

class LingoLensApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        self.label = Label(text="LingoLens AI მზადაა!", font_size=24)
        root.add_widget(self.label)
        
        btn = Button(text="სერვერის შემოწმება", size_hint=(1, 0.2))
        btn.bind(on_press=self.test_connection)
        root.add_widget(btn)
        
        return root

    def test_connection(self, instance):
        self.label.text = "მიმდინარეობს სერვერთან დაკავშირება..."
        def handle_health(is_healthy):
            if is_healthy:
                self.label.text = "სერვერი წარმატებით დაკავშირდა! (Online)"
            else:
                self.label.text = "სერვერი მიუწვდომელია."
        
        check_server_health(handle_health)

if __name__ == '__main__':
    LingoLensApp().run()
