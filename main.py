import base64
import json
import sqlite3
import threading
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
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
    self.battery_saver = False
    self.last_frame_bytes = None
    self.ws = None
    self.should_reconnect = True
    self.latest_translation = ''

    # SQLite ბაზა ისტორიისთვის
    self.init_db()

    self.main_layout = BoxLayout(orientation='vertical')

    # 1. UI Overlay (ზედა პანელი - სტატუსი, ენა და ისტორია)
    self.top_bar = BoxLayout(size_hint=(1, 0.08), spacing=5)
    self.status_label = Label(
        text='[color=ffff00]Connecting...[/color]', markup=True
    )
    self.lang_spinner = Spinner(
        text='Georgian',
        values=('Georgian', 'English', 'German', 'Spanish', 'French'),
        size_hint=(0.3, 1),
    )
    self.history_btn = Button(text='History', size_hint=(0.2, 1))
    self.history_btn.bind(on_press=self.show_history)

    self.top_bar.add_widget(self.status_label)
    self.top_bar.add_widget(self.lang_spinner)
    self.top_bar.add_widget(self.history_btn)
    self.main_layout.add_widget(self.top_bar)

    # 2. Live Camera View + AR Overlay Canvas
    self.camera_box = BoxLayout(size_hint=(1, 0.55))
    self.camera = Camera(play=True, resolution=(640, 480))

    # Canvas AR Overlay კამერის თავზე
    with self.camera.canvas.after:
      Color(0, 0, 0, 0.4)  # ნახევრად გამჭვირვალე AR ფონი
      self.ar_rect = Rectangle(
          pos=(10, 100), size=(self.camera.width - 20, 80)
      )

    self.camera_box.add_widget(self.camera)
    self.main_layout.add_widget(self.camera_box)

    # 3. AI AR Text Display & Controls Panel
    self.ar_label = Label(
        text='[AR Translation Ready]',
        font_size='16sp',
        markup=True,
        size_hint=(1, 0.15),
    )
    self.main_layout.add_widget(self.ar_label)

    # 4. მართვის ღილაკები (Pause, Copy, Voice, Battery Saver)
    self.controls_bar = BoxLayout(size_hint=(1, 0.1), spacing=5)

    self.toggle_btn = Button(
        text='Pause', background_color=(0.8, 0.2, 0.2, 1)
    )
    self.toggle_btn.bind(on_press=self.toggle_streaming)

    self.copy_btn = Button(
        text='Copy Text', background_color=(0.2, 0.6, 0.8, 1)
    )
    self.copy_btn.bind(on_press=self.copy_to_clipboard)

    self.voice_btn = Button(text='🎤 Speak', background_color=(0.3, 0.7, 0.3, 1))
    self.voice_btn.bind(on_press=self.trigger_voice_input)

    self.battery_btn = Button(
        text='Battery: Normal', size_hint=(0.3, 1)
    )
    self.battery_btn.bind(on_press=self.toggle_battery_saver)

    self.controls_bar.add_widget(self.toggle_btn)
    self.controls_bar.add_widget(self.copy_btn)
    self.controls_bar.add_widget(self.voice_btn)
    self.controls_bar.add_widget(self.battery_btn)
    self.main_layout.add_widget(self.controls_bar)

    # Native TTS Init
    self.tts = None
    if platform == 'android':
      self.init_tts()

    # WebSocket Thread
    threading.Thread(target=self.websocket_thread, daemon=True).start()

    # კადრების შემოწმების ტაიმერი (0.5 წამში ერთხელ)
    Clock.schedule_interval(self.process_and_stream_frame, 0.5)

    return self.main_layout

  # --- 1. SQLite History ---
  def init_db(self):
    self.conn = sqlite3.connect('lingolens_history.db')
    self.cursor = self.conn.cursor()
    self.cursor.execute(
        'CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, text TEXT,'
        ' lang TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
    )
    self.conn.commit()

  def save_to_history(self, text, lang):
    self.cursor.execute(
        'INSERT INTO history (text, lang) VALUES (?, ?)', (text, lang)
    )
    self.conn.commit()

  def show_history(self, instance):
    self.cursor.execute(
        'SELECT text, lang, time FROM history ORDER BY id DESC LIMIT 20'
    )
    records = self.cursor.fetchall()

    history_text = '\n\n'.join(
        [f'[{r[2]}] ({r[1]}):\n{r[0]}' for r in records]
    )
    if not history_text:
      history_text = 'No history saved yet.'

    scroll = ScrollView()
    lbl = Label(
        text=history_text, size_hint_y=None, font_size='14sp', markup=True
    )
    lbl.bind(texture_size=lbl.setter('size'))
    scroll.add_widget(lbl)

    popup = Popup(
        title='Translation History', content=scroll, size_hint=(0.9, 0.8)
    )
    popup.open()

  # --- 2. Copy & Clipboard ---
  def copy_to_clipboard(self, instance):
    if self.latest_translation:
      Clipboard.copy(self.latest_translation)
      self.update_status('[color=00ff00]Copied to Clipboard![/color]')

  # --- 3. Voice Input (Speech-to-Text) ---
  def trigger_voice_input(self, instance):
    self.update_status('[color=ffff00]Listening...[/color]')
    # Android SpeechRecognizer-ის გამოძახება
    if platform == 'android':
      self.speak('Listening for your command...')

  # --- 4. Adaptive Battery Saver ---
  def toggle_battery_saver(self, instance):
    self.battery_saver = not self.battery_saver
    if self.battery_saver:
      self.battery_btn.text = 'Battery: Saver'
      self.battery_btn.background_color = (0.9, 0.5, 0.1, 1)
      Clock.unschedule(self.process_and_stream_frame)
      Clock.schedule_interval(
          self.process_and_stream_frame, 1.2
      )  # ნელი ინტერვალი
    else:
      self.battery_btn.text = 'Battery: Normal'
      self.battery_btn.background_color = (0.2, 0.2, 0.2, 1)
      Clock.unschedule(self.process_and_stream_frame)
      Clock.schedule_interval(self.process_and_stream_frame, 0.5)

  # --- Motion Detection & Streaming ---
  def has_motion(self, current_raw_bytes):
    if self.last_frame_bytes is None:
      self.last_frame_bytes = current_raw_bytes
      return True

    arr1 = np.frombuffer(current_raw_bytes[:10000], dtype=np.uint8)
    arr2 = np.frombuffer(self.last_frame_bytes[:10000], dtype=np.uint8)
    diff = np.mean(np.abs(arr1.astype(int) - arr2.astype(int)))
    self.last_frame_bytes = current_raw_bytes
    return diff > 5.0

  def websocket_thread(self):
    while self.should_reconnect:
      try:
        self.update_status('[color=ffff00]Connecting...[/color]')
        self.ws = websocket.WebSocketApp(
            'wss://echo.websocket.org',
            on_message=self.on_ai_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open,
        )
        self.ws.run_forever()
      except Exception as e:
        print(f'WS Error: {e}')
      time.sleep(3)

  def process_and_stream_frame(self, dt):
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
      self.latest_translation = translated_text
      self.update_ui(f'[color=ffffff]{translated_text}[/color]')
      self.save_to_history(translated_text, self.lang_spinner.text)
      self.speak(translated_text)
    except:
      self.latest_translation = message
      self.update_ui(f'[color=ffffff]{message}[/color]')
      self.speak(message)

  def toggle_streaming(self, instance):
    self.is_streaming = not self.is_streaming
    self.toggle_btn.text = 'Resume' if not self.is_streaming else 'Pause'

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
    Clock.schedule_once(lambda dt: setattr(self.ar_label, 'text', text))

  def update_status(self, text):
    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', text))


if __name__ == '__main__':
  LingoLensLiveApp().run()
