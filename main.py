import os
import asyncio
import threading
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

API_KEY = "AIzaSy..."  # თქვენი Gemini API Key

# Android Native Audio და Permissions
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    
    AudioRecord = autoclass('android.media.AudioRecord')
    AudioTrack = autoclass('android.media.AudioTrack')
    AudioFormat = autoclass('android.media.AudioFormat')
    MediaRecorder = autoclass('android.media.MediaRecorder')
    AudioManager = autoclass('android.media.AudioManager')
    jarray = autoclass('jarray')

class LingoLensApp(App):
    def build(self):
        self.is_listening = False
        self.loop = None
        
        # 1. მიკროფონის უფლების მოთხოვნა ჩართვისთანავე
        if platform == 'android':
            request_permissions([Permission.RECORD_AUDIO, Permission.INTERNET])

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.status_label = Label(
            text="LingoLens Live AI Translator", 
            font_size='20sp', 
            size_hint_y=0.1
        )
        layout.add_widget(self.status_label)
        
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
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=API_KEY)
            
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                system_instruction=types.Content(
                    parts=[types.Part.from_text(
                        "You are a real-time bi-directional translator between Georgian and English. "
                        "When you hear Georgian, translate immediately to English. "
                        "When you hear English, translate immediately to Georgian. "
                        "Respond ONLY with spoken translated audio."
                    )]
                )
            )

            async with client.aio.live.connect(model="gemini-2.0-flash-exp", config=config) as session:
                self.append_text("[AI]: მზად ვარ, ილაპარაკეთ...\n")
                
                if platform == 'android':
                    sample_rate = 16000
                    buffer_size = AudioRecord.getMinBufferSize(
                        sample_rate, 
                        AudioFormat.CHANNEL_IN_MONO, 
                        AudioFormat.ENCODING_PCM_16BIT
                    )
                    recorder = AudioRecord(
                        MediaRecorder.AudioSource.MIC,
                        sample_rate,
                        AudioFormat.CHANNEL_IN_MONO,
                        AudioFormat.ENCODING_PCM_16BIT,
                        buffer_size
                    )
                    recorder.startRecording()
                    
                    track_buffer = AudioTrack.getMinBufferSize(
                        24000, 
                        AudioFormat.CHANNEL_OUT_MONO, 
                        AudioFormat.ENCODING_PCM_16BIT
                    )
                    player = AudioTrack(
                        AudioManager.STREAM_MUSIC,
                        24000,
                        AudioFormat.CHANNEL_OUT_MONO,
                        AudioFormat.ENCODING_PCM_16BIT,
                        track_buffer,
                        AudioTrack.MODE_STREAM
                    )
                    player.play()

                    # Java-სთვის თავსებადი აუდიო ბუფერი
                    j_buffer = jarray('b')([0] * buffer_size)

                while self.is_listening:
                    if platform == 'android':
                        read_bytes = recorder.read(j_buffer, 0, buffer_size)
                        if read_bytes > 0:
                            py_bytes = bytes(j_buffer[:read_bytes])
                            await session.send(input={"data": py_bytes, "mime_type": "audio/pcm"})

                    async for response in session.receive():
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if part.inline_data:
                                    pcm_out = part.inline_data.data
                                    if platform == 'android':
                                        j_out = jarray('b')(pcm_out)
                                        player.write(j_out, 0, len(pcm_out))
                    
                    await asyncio.sleep(0.02)

                if platform == 'android':
                    recorder.stop()
                    recorder.release()
                    player.stop()
                    player.release()

        except Exception as e:
            self.append_text(f"\n[შეცდომა]: {str(e)}\n")

if __name__ == '__main__':
    LingoLensApp().run()
