import os
import asyncio
import threading
import base64
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.utils import platform

# NotoSansGeorgian ფონტის რეგისტრირება
if os.path.exists("NotoSansGeorgian.ttf"):
    LabelBase.register(name="Roboto", fn_regular="NotoSansGeorgian.ttf")

# წინა კოდიდან ამოღებული თქვენი Gemini API Key
API_KEY = "AIzaSy..."  # აქ ჩასმულია თქვენი მოქმედი API Key

class LingoLensApp(App):
    def build(self):
        self.is_listening = False
        self.loop = None
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # სათაური
        self.status_label = Label(
            text="LingoLens Gemini Live AI", 
            font_size='20sp', 
            size_hint_y=0.1
        )
        layout.add_widget(self.status_label)
        
        # ჩატის ფანჯარა
        self.chat_label = Label(
            text="დააჭირეთ ღილაკს საუბრის დასაწყებად...\n", 
            font_size='16sp', 
            size_hint_y=None, 
            text_size=(400, None),
            halign='left',
            valign='top'
        )
        self.chat_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        scroll = ScrollView(size_hint=(1, 0.75))
        scroll.add_widget(self.chat_label)
        layout.add_widget(scroll)
        
        # მთავარი ღილაკი
        self.btn = Button(
            text="საუბრის დაწყება", 
            font_size='18sp', 
            size_hint_y=0.15,
            background_color=(0.2, 0.7, 0.3, 1)
        )
        self.btn.bind(on_press=self.toggle_listening)
        layout.add_widget(self.btn)
        
        return layout

    def toggle_listening(self, instance):
        if not self.is_listening:
            self.is_listening = True
            self.btn.text = "შეჩერება"
            self.btn.background_color = (0.9, 0.2, 0.2, 1)
            self.append_text("\n[სისტემა]: Gemini Live ჩაირთო...\n")
            threading.Thread(target=self.start_async_loop, daemon=True).start()
        else:
            self.is_listening = False
            self.btn.text = "საუბრის დაწყება"
            self.btn.background_color = (0.2, 0.7, 0.3, 1)
            self.append_text("[სისტემა]: Gemini Live გაჩერდა.\n")

    def append_text(self, text):
        Clock.schedule_once(lambda dt: self._update_ui_text(text))

    def _update_ui_text(self, text):
        self.chat_label.text += text

    def start_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.gemini_live_session())

    async def gemini_live_session(self):
        """ Gemini WebSocket Live S2S სესიის ინტეგრაცია """
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=API_KEY)
            
            # Streaming & Real-time Bi-directional Translate Config
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                system_instruction=types.Content(
                    parts=[types.Part.from_text(
                        "You are a real-time bi-directional voice translator between Georgian and English. "
                        "When you hear Georgian, translate to English. When you hear English, translate to Georgian. "
                        "Respond ONLY with the audio translation natively and concisely."
                    )]
                )
            )

            # Live API მიერთება
            async with client.aio.live.connect(model="gemini-2.0-flash-exp", config=config) as session:
                self.append_text("[AI]: მზად ვარ, გისმენთ...\n")
                
                while self.is_listening:
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            self.append_text(f"\n[შეცდომა]: {str(e)}\n")

if __name__ == '__main__':
    LingoLensApp().run()
