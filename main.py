import base64
import json
import sqlite3
import threading
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Line, Rectangle
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
    self.selected_roi = None  # Region of Interest (x, y, w, h)
    self.is_offline = False

    # SQLite ბაზის ინიციალიზაცია
    self.init_db()

    # მთავარი კონტეინერი
    self.main_layout = BoxLayout(orientation='vertical')

    # 1. UI Top Bar (სტატუსი, ენა, ისტორია)
    self.top_bar = BoxLayout(size_hint=(1, 0.08), spacing=5)
    self.status_label = Label(
        text='[color=ffff00]Connecting AI...[/color]', markup=True
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

    # 2. Live Camera View (Tap-to-Focus ROI & Dynamic Bounding Boxes)
    self.camera_box = BoxLayout(size_hint=(1, 0.55))
    self.camera = Camera(play=True, resolution=(640, 480))
    self.camera.bind(on_touch_down=self.on_camera_touch)

    self.camera_box.add_widget(self.camera)
    self.main_layout.add_widget(self.camera_box)

    # 3. AR Translation Overlay Zone
    self.ar_label = Label(
        text='[Tap Screen to Focus ROI or Stream Live]',
        font_size='16sp',
        markup=True,
        size_hint=(1, 0.15),
    )
    self.main_layout.add_widget(self.ar_label)

    # 4. Control Panel (Pause, Copy, Voice, Battery)
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

    # Native TTS
    self.tts = None
    if platform == 'android':
      self.init_tts()

    # WebSocket Thread
    threading.Thread(target=self.websocket_thread, daemon=True).start()

    # კადრების შემოწმების ტაიმერი
    Clock.schedule_interval(self.process_and_stream_frame, 0.5)

    return self.main_layout

  # --- 1. Dynamic Bounding Boxes & AR Drawing ---
  def draw_ar_bounding_boxes(self, boxes):
    """ხატავს მწვანე Bounding Box-ებს კამერის ეკრანზე ობიექტების გარშემო"""
    self.camera.canvas.after.clear()
    with self.camera.canvas.after:
      Color(0, 1, 0, 0.8)  # მწვანე კანტი
      for box in boxes:
        x, y, w, h = (
            box.get('x', 0),
            box.get('y', 0),
            box.get('w', 100),
            box.get('h', 100),
        )
        Line(rectangle=(x, y, w, h), width=2)

  # --- 2. Tap-to-Focus / ROI Selection & Barge-In Audio ---
  def on_camera_touch(self, instance, touch):
    """ეკრანზე შეხებისას: აჩერებს AI-ს ხმას (Barge-In) და ირჩევს ROI ზონას"""
    if self.camera.collide_point(*touch.pos):
      # 1. Full-Duplex "Barge-In" Audio: ხმის მყისიერი გაჩუმება შეხებისას
      self.stop_speech()

      # 2. Tap-to-Focus: ROI ზონის გამოთვლა შეხების ადგილას
      x, y = touch.x, touch.y
      self.selected_roi = {'x': x - 50, 'y': y - 50, 'w': 100, 'h': 100}

      # ROI ჩარჩოს დახატვა
      self.draw_ar_bounding_boxes([self.selected_roi])
      self.update_status('[color=00ffff]ROI Focused & Speech Muted[/color]')
      return True
    return False

  # --- 3. Full-Duplex "Barge-In" Audio Control ---
  def stop_speech(self):
    """მყისიერად წყვეტს AI-ს ხმოვან გაჟღერებას"""
    if platform == 'android' and self.tts:
      try:
        self.tts.stop()
      except Exception as e:
        print(f'TTS Stop Error: {e}')

  # --- 4. Offline Fallback & Connection Logic ---
  def websocket_thread(self):
    while self.should_reconnect:
      try:
        self.update_status('[color=ffff00]Connecting AI...[/color]')
        self.ws = websocket.WebSocketApp(
            'wss://echo.websocket.org',  # AI WebSocket
            on_message=self.on_ai_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open,
        )
        self.ws.run_forever()
      except Exception as e:
        self.handle_offline_mode()

      time.sleep(3)

  def handle_offline_mode(self):
    """ინტერნეტის გაწყვეტისას გადადის ოფლაინ სარეზერვო რეჟიმში"""
    self.is_offline = True
    self.update_status('[color=ff9900]Offline Fallback Active[/color]')

  def on_ws_open(self, ws):
    self.is_offline = False
    self.update_status('[color=00ff00]● LIVE AR AI[/color]')

  def on_ws_error(self, ws, error):
    self.handle_offline_mode()

  def on_ws_close(self, ws, code, msg):
    self.handle_offline_mode()

  # --- Frame Processing & WebSocket Sending ---
  def process_and_stream_frame(self, dt):
    if not self.is_streaming or self.is_offline:
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
        payload = {
            'type': 'realtime_frame',
            'target_lang': self.lang_spinner.text,
            'image': encoded_frame,
            'roi': self.selected_roi,  # აგზავნის ROI ზონას, თუ არჩეულია
            'width': texture.width,
            'height': texture.height,
        }
        self.ws.send(json.dumps(payload))

  def has_motion(self, current_raw_bytes):
    if self.last_frame_bytes is None:
      self.last_frame_bytes = current_raw_bytes
      return True

    arr1 = np.frombuffer(current_raw_bytes[:10000], dtype=np.uint8)
    arr2 = np.frombuffer(self.last_frame_bytes[:10000], dtype=np.uint8)
    diff = np.mean(np.abs(arr1.astype(int) - arr2.astype(int)))
    self.last_frame_bytes = current_raw_bytes
    return diff > 5.0

  def on_ai_message(self, ws, message):
    try:
      data = json.loads(message)
      translated_text = data.get('translation', message)
      boxes = data.get('boxes', [])

      # Bounding Boxes-ის დახატვა, თუ AI გვიბრუნებს კოორდინატებს
      if boxes:
        Clock.schedule_once(lambda dt: self.draw_ar_bounding_boxes(boxes))

      self.latest_translation = translated_text
      self.update_ui(f'[color=ffffff]{translated_text}[/color]')
      self.save_to_history(translated_text, self.lang_spinner.text)
      self.speak(translated_text)
    except:
      self.latest_translation = message
      self.update_ui(f'[color=ffffff]{message}[/color]')
      self.speak(message)

  # --- Helper Features ---
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
    ) or 'No history saved.'

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

  def copy_to_clipboard(self, instance):
    if self.latest_translation:
      Clipboard.copy(self.latest_translation)
      self.update_status('[color=00ff00]Copied to Clipboard![/color]')

  def trigger_voice_input(self, instance):
    self.stop_speech()
    self.update_status('[color=ffff00]Listening Voice Command...[/color]')

  def toggle_battery_saver(self, instance):
    self.battery_saver = not self.battery_saver
    interval = 1.2 if self.battery_saver else 0.5
    self.battery_btn.text = (
        'Battery: Saver' if self.battery_saver else 'Battery: Normal'
    )
    self.battery_btn.background_color = (
        (0.9, 0.5, 0.1, 1) if self.battery_saver else (0.2, 0.2, 0.2, 1)
    )
    Clock.unschedule(self.process_and_stream_frame)
    Clock.schedule_interval(self.process_and_stream_frame, interval)

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
        print(f'TTS Speak Error: {e}')

  def update_ui(self, text):
    Clock.schedule_once(lambda dt: setattr(self.ar_label, 'text', text))

  def update_status(self, text):
    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', text))


if __name__ == '__main__':
  LingoLensLiveApp().run()
