import base64
import json
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
import websocket

# Android-ის ნატიური TextToSpeech ინტეგრაცია pyjnius-ით
if platform == 'android':
  from jnius import autoclass

  PythonActivity = autoclass('org.kivy.android.PythonActivity')
  TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
  Locale = autoclass('java.util.Locale')


class LingoLensLiveApp(App):

  def build(self):
    self.layout = BoxLayout(orientation='vertical')

    # 1. Real-time Live Camera View
    self.camera = Camera(play=True, resolution=(640, 480))
    self.layout.add_widget(self.camera)

    # 2. AI ტექსტური პასუხის ზონა
    self.scroll = ScrollView(size_hint=(1, 0.3))
    self.label = Label(
        text='[Live AI Stream Starting...]',
        size_hint_y=None,
        font_size='18sp',
        markup=True,
    )
    self.label.bind(texture_size=self.label.setter('size'))
    self.scroll.add_widget(self.label)
    self.layout.add_widget(self.scroll)

    # 3. აუდიო სისტემის (TTS) ინიციალიზაცია
    self.tts = None
    if platform == 'android':
      self.init_tts()

    self.ws = None
    threading.Thread(target=self.connect_websocket, daemon=True).start()

    # ყოველ 0.5 წამში კადრის გაგზავნა
    Clock.schedule_interval(self.stream_frame_to_ai, 0.5)

    return self.layout

  def init_tts(self):
    """ინგრევს Android-ის ხმოვან ძრავას"""
    try:
      activity = PythonActivity.mActivity
      self.tts = TextToSpeech(activity, None)
    except Exception as e:
      print(f'TTS Init Error: {e}')

  def speak(self, text):
    """AI-ს მიერ დაბრუნებული ტექსტის გაჟღერება"""
    if platform == 'android' and self.tts:
      try:
        # QUEUE_FLUSH - ახალი პასუხისას წინა ხმის გაჩუმება და ახლის დაწყება
        self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
      except Exception as e:
        print(f'TTS Speak Error: {e}')
    else:
      print(f'[Audio Mock]: {text}')

  def connect_websocket(self):
    try:
      self.ws = websocket.WebSocketApp(
          'wss://echo.websocket.org',  # ჩაანაცვლეთ AI სერვერით
          on_message=self.on_ai_message,
          on_error=self.on_ws_error,
          on_open=self.on_ws_open,
      )
      self.ws.run_forever()
    except Exception as e:
      self.update_ui(f'[color=ff0000]WS Fail: {e}[/color]')

  def on_ws_open(self, ws):
    self.update_ui('[color=00ff00]✓ Live AI Connected![/color]')

  def on_ws_error(self, ws, error):
    self.update_ui(f'[color=ff0000]WS Error: {error}[/color]')

  def on_ai_message(self, ws, message):
    try:
      data = json.loads(message)
      translated_text = data.get('translation', message)

      # 1. ტექსტის განახლება ეკრანზე
      self.update_ui(f'[color=ffffff]AI: {translated_text}[/color]')

      # 2. ხმოვანი გაჟღერება (Audio Output)
      self.speak(translated_text)
    except:
      self.update_ui(f'[color=ffffff]AI: {message}[/color]')
      self.speak(message)

  def stream_frame_to_ai(self, dt):
    if (
        self.camera.texture
        and self.ws
        and self.ws.sock
        and self.ws.sock.connected
    ):
      texture = self.camera.texture
      raw_bytes = texture.pixels
      encoded_frame = base64.b64encode(raw_bytes).decode('utf-8')

      payload = json.dumps({
          'type': 'realtime_frame',
          'image': encoded_frame,
          'width': texture.width,
          'height': texture.height,
      })
      self.ws.send(payload)

  def update_ui(self, text):
    Clock.schedule_once(lambda dt: setattr(self.label, 'text', text))


if __name__ == '__main__':
  LingoLensLiveApp().run()
