import base64
import json
import threading
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
import numpy as np
import websocket

# Android Native TTS
if platform == 'android':
  from jnius import autoclass

  PythonActivity = autoclass('org.kivy.android.PythonActivity')
  TextToSpeech = autoclass('android.speech.tts.TextToSpeech')


class LingoLensLiveApp(App):

  def build(self):
    self.is_streaming = True
    self.last_frame_bytes = None
    self.ws = None
    self.should_reconnect = True

    # მთავარი Layout
    self.main_layout = BoxLayout(orientation='vertical')

    # 1. UI Overlay (ზედა პანელი - ენის არჩევა და სტატუსი)
    self.top_bar = BoxLayout(size_hint=(1, 0.08), spacing=5)

    self.status_label = Label(
        text='[color=ffff00]Connecting...[/color]', markup=True
    )

    self.lang_spinner = Spinner(
        text='Georgian',
        values=('Georgian', 'English', 'German', 'Spanish', 'French'),
        size_hint=(0.4, 1),
    )

    self.top_bar.add_widget(self.status_label)
    self.top_bar.add_widget(self.lang_spinner)
    self.main_layout.add_widget(self.top_bar)

    # 2. Live Camera Stream
    self.camera = Camera(play=True, resolution=(640, 480))
    self.main_layout.add_widget(self.camera)

    # 3. AI-ს პასუხების ზონა
    self.scroll = ScrollView(size_hint=(1, 0.25))
    self.label = Label(
        text='[LingoLens AR Ready]',
        size_hint_y=None,
        font_size='16sp',
        markup=True,
    )
    self.label.bind(texture_size=self.label.setter('size'))
    self.scroll.add_widget(self.label)
    self.main_layout.add_widget(self.scroll)

    # 4. ქვედა მართვის პანელი (Pause/Resume ღილაკი)
    self.bottom_bar = BoxLayout(size_hint=(1, 0.08))
    self.toggle_btn = Button(
        text='Pause Stream', background_color=(0.8, 0.2, 0.2, 1)
    )
    self.toggle_btn.bind(on_press=self.toggle_streaming)
    self.bottom_bar.add_widget(self.toggle_btn)
    self.main_layout.add_widget(self.bottom_bar)

    # Native TTS Init
    self.tts = None
    if platform == 'android':
      self.init_tts()

    # WebSocket-ის გაშვება
    threading.Thread(target=self.websocket_thread, daemon=True).start()

    # კადრების შემოწმების ტაიმერი (0.5 წამში ერთხელ)
    Clock.schedule_interval(self.process_and_stream_frame, 0.5)

    return self.main_layout

  def toggle_streaming(self, instance):
    """სტრიმის შეჩერება / გაგრძელება"""
    self.is_streaming = not self.is_streaming
    if self.is_streaming:
      self.toggle_btn.text = 'Pause Stream'
      self.toggle_btn.background_color = (0.8, 0.2, 0.2, 1)
      self.update_status('[color=00ff00]Streaming Active[/color]')
    else:
      self.toggle_btn.text = 'Resume Stream'
      self.toggle_btn.background_color = (0.2, 0.8, 0.2, 1)
      self.update_status('[color=ff9900]Stream Paused[/color]')

  def has_motion(self, current_raw_bytes):
    """Smart Frame Throttling: ამოწმებს, შეიცვალა თუ არა კადრი (მოძრაობის დეტექცია)"""
    if self.last_frame_bytes is None:
      self.last_frame_bytes = current_raw_bytes
      return True

    # ბაიტების შედარება Numpy-ით სწრაფი გამოთვლისთვის
    arr1 = np.frombuffer(current_raw_bytes[:10000], dtype=np.uint8)
    arr2 = np.frombuffer(self.last_frame_bytes[:10000], dtype=np.uint8)

    diff = np.mean(np.abs(arr1.astype(int) - arr2.astype(int)))
    self.last_frame_bytes = current_raw_bytes

    # თუ განსხვავება 5%-ზე მეტია, ესე იგი კამერამ იმოძრავა
    return diff > 5.0

  def websocket_thread(self):
    """Auto-Reconnect WebSocket Logic"""
    while self.should_reconnect:
      try:
        self.update_status('[color=ffff00]Connecting AI...[/color]')
        self.ws = websocket.WebSocketApp(
            'wss://echo.websocket.org',  # ჩაანაცვლეთ AI Live WebSocket-ით
            on_message=self.on_ai_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open,
        )
        self.ws.run_forever()
      except Exception as e:
        print(f'WS Exception: {e}')

      time.sleep(3)  # გაწყვეტის შემთხვევაში 3 წამში ხელახლა ცდილობს დაკავშირებას

  def on_ws_open(self, ws):
    self.update_status('[color=00ff00]● LIVE AI[/color]')

  def on_ws_error(self, ws, error):
    self.update_status('[color=ff0000]WS Error[/color]')

  def on_ws_close(self, ws, close_status_code, close_msg):
    self.update_status('[color=ff0000]Disconnected. Reconnecting...[/color]')

  def process_and_stream_frame(self, dt):
    """ჭკვიანი გაგზავნა: მხოლოდ მაშინ, როცა აქტიურია და კადრი შეიცვალა"""
    if not self.is_streaming:
      return

    if (
        self.camera.texture
        and self.ws
        and self.ws.sock
        and self.ws.sock.connected
    ):
      texture = self.camera.texture
      raw_bytes = texture.pixels

      # იგზავნება მხოლოდ მოძრაობის დაფიქსირებისას (ზოგავს ტრაფიკს)
      if self.has_motion(raw_bytes):
        encoded_frame = base64.b64encode(raw_bytes).decode('utf-8')
        payload = json.dumps({
            'type': 'realtime_frame',
            'target_lang': self.lang_spinner.text,
            'image': encoded_frame,
            'width': texture.width,
            'height': texture.height,
        })
        self.ws.send(payload)

  def on_ai_message(self, ws, message):
    try:
      data = json.loads(message)
      translated_text = data.get('translation', message)
      self.update_ui(f'[color=ffffff]AI: {translated_text}[/color]')
      self.speak(translated_text)
    except:
      self.update_ui(f'[color=ffffff]AI: {message}[/color]')
      self.speak(message)

  def init_tts(self):
    try:
      activity = PythonActivity.mActivity
      self.tts = TextToSpeech(activity, None)
    except Exception as e:
      print(f'TTS Init Error: {e}')

  def speak(self, text):
    if platform == 'android' and self.tts:
      try:
        self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
      except Exception as e:
        print(f'TTS Error: {e}')

  def update_ui(self, text):
    Clock.schedule_once(lambda dt: setattr(self.label, 'text', text))

  def update_status(self, text):
    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', text))


if __name__ == '__main__':
  LingoLensLiveApp().run()
