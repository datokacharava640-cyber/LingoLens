import base64
import json
import sqlite3
import threading
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Line
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

# Android Native Audio & Hardware FX Integration
if platform == 'android':
  from jnius import autoclass

  PythonActivity = autoclass('org.kivy.android.PythonActivity')
  AudioRecord = autoclass('android.media.AudioRecord')
  AudioTrack = autoclass('android.media.AudioTrack')
  AudioFormat = autoclass('android.media.AudioFormat')
  MediaRecorder = autoclass('android.media.MediaRecorder')
  AudioManager = autoclass('android.media.AudioManager')
  AcousticEchoCanceler = autoclass(
      'android.media.audiofx.AcousticEchoCanceler'
  )
  NoiseSuppressor = autoclass('android.media.audiofx.NoiseSuppressor')
  TextToSpeech = autoclass('android.speech.tts.TextToSpeech')


class LingoLensLiveApp(App):

  def build(self):
    self.is_streaming = True
    self.battery_saver = False
    self.last_frame_bytes = None
    self.ws = None
    self.should_reconnect = True
    self.latest_translation = ''
    self.selected_roi = None
    self.is_offline = False

    # Audio Engine variables
    self.sample_rate = 16000
    self.audio_record = None
    self.audio_track = None
    self.is_recording = False

    # SQLite
    self.init_db()

    # UI Construction
    self.main_layout = BoxLayout(orientation='vertical')

    # 1. Top Bar
    self.top_bar = BoxLayout(size_hint=(1, 0.08), spacing=5)
    self.status_label = Label(
        text='[color=ffff00]Initializing Engine...[/color]', markup=True
    )
    self.lang_spinner = Spinner(
        text='Auto Bidirectional',
        values=('Auto Bidirectional', 'Georgian', 'English', 'German'),
        size_hint=(0.4, 1),
    )
    self.history_btn = Button(text='History', size_hint=(0.2, 1))
    self.history_btn.bind(on_press=self.show_history)

    self.top_bar.add_widget(self.status_label)
    self.top_bar.add_widget(self.lang_spinner)
    self.top_bar.add_widget(self.history_btn)
    self.main_layout.add_widget(self.top_bar)

    # 2. Camera View & AR Overlay
    self.camera_box = BoxLayout(size_hint=(1, 0.55))
    self.camera = Camera(play=True, resolution=(640, 480))
    self.camera.bind(on_touch_down=self.on_camera_touch)
    self.camera_box.add_widget(self.camera)
    self.main_layout.add_widget(self.camera_box)

    # 3. Live Streaming Captions AR Zone (Word-by-Word)
    self.ar_label = Label(
        text='[Live Speech & AR Vision Ready]',
        font_size='16sp',
        markup=True,
        size_hint=(1, 0.15),
    )
    self.main_layout.add_widget(self.ar_label)

    # 4. Controls
    self.controls_bar = BoxLayout(size_hint=(1, 0.1), spacing=5)
    self.toggle_btn = Button(
        text='Pause', background_color=(0.8, 0.2, 0.2, 1)
    )
    self.toggle_btn.bind(on_press=self.toggle_streaming)

    self.copy_btn = Button(
        text='Copy Text', background_color=(0.2, 0.6, 0.8, 1)
    )
    self.copy_btn.bind(on_press=self.copy_to_clipboard)

    self.battery_btn = Button(text='Battery: Normal', size_hint=(0.3, 1))
    self.battery_btn.bind(on_press=self.toggle_battery_saver)

    self.controls_bar.add_widget(self.toggle_btn)
    self.controls_bar.add_widget(self.copy_btn)
    self.controls_bar.add_widget(self.battery_btn)
    self.main_layout.add_widget(self.controls_bar)

    # Audio Hardware setup (Android)
    if platform == 'android':
      self.init_android_audio()

    # Threads
    threading.Thread(target=self.websocket_thread, daemon=True).start()

    # Video Loop
    Clock.schedule_interval(self.process_and_stream_frame, 0.5)

    return self.main_layout

  # --- 1. Continuous Audio Record & Hardware Echo/Noise Cancellation ---
  def init_android_audio(self):
    try:
      # Audio Record configuration
      min_buf_size = AudioRecord.getMinBufferSize(
          self.sample_rate,
          AudioFormat.CHANNEL_IN_MONO,
          AudioFormat.ENCODING_PCM_16BIT,
      )
      self.audio_record = AudioRecord(
          MediaRecorder.AudioSource.VOICE_COMMUNICATION,
          self.sample_rate,
          AudioFormat.CHANNEL_IN_MONO,
          AudioFormat.ENCODING_PCM_16BIT,
          min_buf_size * 2,
      )

      # Hardware Echo & Noise Cancellation
      session_id = self.audio_record.getAudioSessionId()
      if AcousticEchoCanceler.isAvailable():
        aec = AcousticEchoCanceler.create(session_id)
        if aec:
          aec.setEnabled(True)
      if NoiseSuppressor.isAvailable():
        ns = NoiseSuppressor.create(session_id)
        if ns:
          ns.setEnabled(True)

      # Audio Track Player configuration (Direct PCM Playback)
      out_buf_size = AudioTrack.getMinBufferSize(
          self.sample_rate,
          AudioFormat.CHANNEL_OUT_MONO,
          AudioFormat.ENCODING_PCM_16BIT,
      )
      self.audio_track = AudioTrack(
          AudioManager.STREAM_MUSIC,
          self.sample_rate,
          AudioFormat.CHANNEL_OUT_MONO,
          AudioFormat.ENCODING_PCM_16BIT,
          out_buf_size * 2,
          AudioTrack.MODE_STREAM,
      )
      self.audio_track.play()

      # Start Mic Background Recording
      self.is_recording = True
      threading.Thread(
          target=self.continuous_audio_stream, daemon=True
      ).start()
    except Exception as e:
      print(f'Audio Initialization Error: {e}')

  def continuous_audio_stream(self):
    """მიკროფონიდან PCM აუდიო ნაკადის უწყვეტი გაგზავნა WebSocket-ით"""
    if not self.audio_record:
      return

    self.audio_record.startRecording()
    buffer_size = 2048
    audio_buffer = bytearray(buffer_size)

    while self.is_recording:
      if self.is_streaming and self.ws and self.ws.sock and self.ws.sock.connected:
        read_size = self.audio_record.read(audio_buffer, 0, buffer_size)
        if read_size > 0:
          encoded_audio = base64.b64encode(audio_buffer[:read_size]).decode(
              'utf-8'
          )
          payload = {
              'type': 'audio_chunk',
              'audio': encoded_audio,
              'mode': self.lang_spinner.text,
          }
          try:
            self.ws.send(json.dumps(payload))
          except:
            pass
      time.sleep(0.05)

  # --- 2. Live PCM Audio Playback & Word-by-Word Live Captions ---
  def play_pcm_audio_chunk(self, raw_audio_bytes):
    """AI-სგან მიღებული აუდიო ნაკადის მყისიერი დაკვრა დინამიკში"""
    if platform == 'android' and self.audio_track:
      try:
        self.audio_track.write(
            raw_audio_bytes, 0, len(raw_audio_bytes)
        )
      except Exception as e:
        print(f'Audio Playback Error: {e}')

  def on_ai_message(self, ws, message):
    try:
      data = json.loads(message)

      # 1. Live Word-by-Word Captions Stream
      if 'caption_token' in data:
        token = data['caption_token']
        self.latest_translation += token
        self.update_ui(f'[color=ffffff]{self.latest_translation}[/color]')

      # 2. Live Audio Streaming Chunk
      if 'audio_stream' in data:
        pcm_bytes = base64.b64decode(data['audio_stream'])
        self.play_pcm_audio_chunk(pcm_bytes)

      # 3. Dynamic Bounding Boxes
      if 'boxes' in data:
        Clock.schedule_once(
            lambda dt: self.draw_ar_bounding_boxes(data['boxes'])
        )

      # Save Complete Sentence
      if data.get('is_final', False):
        self.save_to_history(
            self.latest_translation, self.lang_spinner.text
        )
        self.latest_translation = ''

    except Exception as e:
      self.update_ui(f'[color=ffffff]{message}[/color]')

  # --- 3. Barge-In Audio & Dynamic ROI ---
  def stop_speech(self):
    """მყისიერად გაჩუმება შეხებისას (Barge-In)"""
    if platform == 'android' and self.audio_track:
      try:
        self.audio_track.pause()
        self.audio_track.flush()
        self.audio_track.play()
      except Exception as e:
        print(f'Barge-in Error: {e}')

  def on_camera_touch(self, instance, touch):
    if self.camera.collide_point(*touch.pos):
      self.stop_speech()
      x, y = touch.x, touch.y
      self.selected_roi = {'x': x - 50, 'y': y - 50, 'w': 100, 'h': 100}
      self.draw_ar_bounding_boxes([self.selected_roi])
      self.update_status('[color=00ffff]ROI Focused & Muted[/color]')
      return True
    return False

  def draw_ar_bounding_boxes(self, boxes):
    self.camera.canvas.after.clear()
    with self.camera.canvas.after:
      Color(0, 1, 0, 0.8)
      for box in boxes:
        Line(
            rectangle=(
                box.get('x', 0),
                box.get('y', 0),
                box.get('w', 100),
                box.get('h', 100),
            ),
            width=2,
        )

  # --- 4. Video Frame Streaming & Motion Engine ---
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
            'type': 'video_frame',
            'image': encoded_frame,
            'roi': self.selected_roi,
            'mode': self.lang_spinner.text,
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

  # --- 5. Network & Database Helpers ---
  def websocket_thread(self):
    while self.should_reconnect:
      try:
        self.update_status('[color=ffff00]Connecting AI Live...[/color]')
        self.ws = websocket.WebSocketApp(
            'wss://echo.websocket.org',
            on_message=self.on_ai_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open,
        )
        self.ws.run_forever()
      except:
        self.handle_offline_mode()
      time.sleep(3)

  def handle_offline_mode(self):
    self.is_offline = True
    self.update_status('[color=ff9900]Offline Fallback Active[/color]')

  def on_ws_open(self, ws):
    self.is_offline = False
    self.update_status('[color=00ff00]● ULTRA LIVE AR AI[/color]')

  def on_ws_error(self, ws, error):
    self.handle_offline_mode()

  def on_ws_close(self, ws, code, msg):
    self.handle_offline_mode()

  def init_db(self):
    self.conn = sqlite3.connect('lingolens_history.db')
    self.cursor = self.conn.cursor()
    self.cursor.execute(
        'CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, text TEXT,'
        ' lang TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
    )
    self.conn.commit()

  def save_to_history(self, text, lang):
    if text.strip():
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
    Popup(
        title='Translation History', content=scroll, size_hint=(0.9, 0.8)
    ).open()

  def copy_to_clipboard(self, instance):
    if self.ar_label.text:
      Clipboard.copy(self.ar_label.text)
      self.update_status('[color=00ff00]Copied to Clipboard![/color]')

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

  def update_ui(self, text):
    Clock.schedule_once(lambda dt: setattr(self.ar_label, 'text', text))

  def update_status(self, text):
    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', text))


if __name__ == '__main__':
  LingoLensLiveApp().run()
