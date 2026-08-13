import base64
import json
import sqlite3
import threading
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase  # <--- ფონტის რეგისტრაციისთვის
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.utils import platform
import numpy as np
import websocket

# 1. ქართული NotoSans-ის გლობალური რეგისტრაცია Kivy-სთვის
LabelBase.register(name='Roboto', fn_regular='NotoSansGeorgian.ttf')

# Android Native Integration & Dynamic Permissions
if platform == 'android':
  from android.permissions import Permission, request_permissions
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


# Glassmorphism Custom Panel
class GlassPanel(BoxLayout):

  def __init__(
      self,
      bg_color=(0.1, 0.1, 0.18, 0.75),
      border_color=(0.3, 0.5, 0.9, 0.6),
      radius=[16],
      **kwargs,
  ):
    super().__init__(**kwargs)
    self.bg_color = bg_color
    self.border_color = border_color
    self.radius = radius
    self.bind(pos=self.update_canvas, size=self.update_canvas)

  def update_canvas(self, *args):
    self.canvas.before.clear()
    with self.canvas.before:
      Color(*self.bg_color)
      RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
      Color(*self.border_color)
      Line(
          rounded_rectangle=(
              self.x,
              self.y,
              self.width,
              self.height,
              self.radius[0],
          ),
          width=1.2,
      )


class LingoLensUltraApp(App):

  def build(self):
    self.is_streaming = True
    self.hud_mode = False
    self.last_frame_bytes = None
    self.ws = None
    self.should_reconnect = True
    self.latest_translation = ''
    self.selected_roi = None
    self.is_offline = False

    self.stream_fps_interval = 0.5
    self.api_key = ''

    self.sample_rate = 16000
    self.audio_record = None
    self.audio_track = None
    self.is_recording = False
    self.mic_level = 0.0

    self.init_db()

    # Base Layout
    self.main_layout = BoxLayout(
        orientation='vertical', padding=12, spacing=10
    )

    # Top Bar Panel
    self.top_bar = GlassPanel(
        bg_color=(0.08, 0.08, 0.15, 0.8),
        border_color=(0.0, 0.8, 1.0, 0.5),
        size_hint=(1, 0.09),
        padding=[10, 5],
        spacing=8,
    )

    self.status_label = Label(
        text='[color=00ffff]● INITIALIZING ULTRA ENGINE[/color]',
        markup=True,
        font_size='13sp',
        bold=True,
    )

    self.lang_spinner = Spinner(
        text='Auto Bidirectional',
        values=(
            'Auto Bidirectional',
            'Georgian',
            'English',
            'German',
            'French',
        ),
        size_hint=(0.38, 1),
        background_normal='',
        background_color=(0.15, 0.2, 0.35, 0.85),
        color=(1, 1, 1, 1),
    )

    self.settings_btn = Button(
        text='⚙ Key',
        size_hint=(0.15, 1),
        background_normal='',
        background_color=(0.2, 0.3, 0.6, 0.85),
        bold=True,
    )
    self.settings_btn.bind(on_press=self.open_settings)

    self.flashcard_btn = Button(
        text='🎴 Cards',
        size_hint=(0.18, 1),
        background_normal='',
        background_color=(0.4, 0.2, 0.7, 0.85),
        bold=True,
    )
    self.flashcard_btn.bind(on_press=self.show_flashcards)

    self.top_bar.add_widget(self.status_label)
    self.top_bar.add_widget(self.lang_spinner)
    self.top_bar.add_widget(self.settings_btn)
    self.top_bar.add_widget(self.flashcard_btn)
    self.main_layout.add_widget(self.top_bar)

    # Viewport
    self.viewport_container = BoxLayout(size_hint=(1, 0.54), spacing=8)
    self.camera_left = Camera(play=True, resolution=(640, 480))
    self.camera_left.bind(on_touch_down=self.on_camera_touch)
    self.viewport_container.add_widget(self.camera_left)

    self.camera_right = Camera(
        play=True, resolution=(640, 480), opacity=0, size_hint=(0, 1)
    )
    self.viewport_container.add_widget(self.camera_right)
    self.main_layout.add_widget(self.viewport_container)

    # Subtitles Panel
    self.middle_panel = GlassPanel(
        orientation='vertical',
        bg_color=(0.05, 0.05, 0.12, 0.85),
        border_color=(0.5, 0.2, 0.9, 0.5),
        size_hint=(1, 0.23),
        padding=10,
        spacing=5,
    )

    self.visualizer_box = BoxLayout(size_hint=(1, 0.25))
    self.visualizer_box.bind(size=self.draw_audio_waveform)
    self.middle_panel.add_widget(self.visualizer_box)

    self.ar_label = Label(
        text=(
            '[color=00ffff]✨ LingoLens Glass UI Ready[/color]\n[color=888888]Tap'
            ' screen to focus ROI & Mute[/color]'
        ),
        font_size='15sp',
        markup=True,
        halign='center',
        valign='middle',
        size_hint=(1, 0.75),
    )
    self.ar_label.bind(size=self.ar_label.setter('text_size'))
    self.middle_panel.add_widget(self.ar_label)
    self.main_layout.add_widget(self.middle_panel)

    # Controls
    self.controls_bar = GlassPanel(
        bg_color=(0.08, 0.08, 0.15, 0.8),
        border_color=(0.0, 0.8, 1.0, 0.4),
        size_hint=(1, 0.1),
        padding=[8, 5],
        spacing=6,
    )

    self.toggle_btn = Button(
        text='Pause',
        background_normal='',
        background_color=(0.8, 0.2, 0.3, 0.85),
        bold=True,
    )
    self.toggle_btn.bind(on_press=self.toggle_streaming)

    self.copy_btn = Button(
        text='Copy',
        background_normal='',
        background_color=(0.1, 0.6, 0.8, 0.85),
        bold=True,
    )
    self.copy_btn.bind(on_press=self.copy_to_clipboard)

    self.hud_btn = Button(
        text='🕶 HUD',
        background_normal='',
        background_color=(0.5, 0.2, 0.8, 0.85),
        bold=True,
    )
    self.hud_btn.bind(on_press=self.toggle_hud_mode)

    self.battery_btn = Button(
        text='⚡ 2 FPS',
        size_hint=(0.28, 1),
        background_normal='',
        background_color=(0.1, 0.7, 0.4, 0.85),
        bold=True,
    )
    self.battery_btn.bind(on_press=self.toggle_adaptive_quality)

    self.controls_bar.add_widget(self.toggle_btn)
    self.controls_bar.add_widget(self.copy_btn)
    self.controls_bar.add_widget(self.hud_btn)
    self.controls_bar.add_widget(self.battery_btn)
    self.main_layout.add_widget(self.controls_bar)

    threading.Thread(target=self.websocket_thread, daemon=True).start()
    Clock.schedule_interval(
        self.process_and_stream_frame, self.stream_fps_interval
    )

    return self.main_layout

  def on_start(self):
    if platform == 'android':

      def callback(permissions, results):
        if all(results):
          self.init_android_audio()
          self.update_status('[color=00ff00]● PERMISSIONS GRANTED[/color]')
        else:
          self.update_status('[color=ff0000]PERMISSIONS DENIED![/color]')

      request_permissions(
          [
              Permission.CAMERA,
              Permission.RECORD_AUDIO,
              Permission.INTERNET,
              Permission.MODIFY_AUDIO_SETTINGS,
          ],
          callback,
      )

  def draw_audio_waveform(self, *args):
    self.visualizer_box.canvas.clear()
    with self.visualizer_box.canvas:
      Color(0.0, 0.9, 1.0, 0.85)
      center_y = self.visualizer_box.y + self.visualizer_box.height / 2
      width = self.visualizer_box.width
      height_amplitude = self.mic_level * 40.0

      points = []
      for x in range(0, int(width), 12):
        y = center_y + (np.sin(x * 0.1 + time.time() * 12) * height_amplitude)
        points.extend([self.visualizer_box.x + x, y])

      if len(points) >= 4:
        Line(points=points, width=2.0)

  def init_android_audio(self):
    try:
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

      session_id = self.audio_record.getAudioSessionId()
      if AcousticEchoCanceler.isAvailable():
        aec = AcousticEchoCanceler.create(session_id)
        if aec:
          aec.setEnabled(True)
      if NoiseSuppressor.isAvailable():
        ns = NoiseSuppressor.create(session_id)
        if ns:
          ns.setEnabled(True)

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

      self.is_recording = True
      threading.Thread(
          target=self.continuous_audio_stream, daemon=True
      ).start()
    except Exception as e:
      print(f'Audio Engine Error: {e}')

  def continuous_audio_stream(self):
    if not self.audio_record:
      return
    self.audio_record.startRecording()
    buffer_size = 2048
    audio_buffer = bytearray(buffer_size)

    while self.is_recording:
      if (
          self.is_streaming
          and self.ws
          and self.ws.sock
          and self.ws.sock.connected
      ):
        read_size = self.audio_record.read(audio_buffer, 0, buffer_size)
        if read_size > 0:
          raw_data = np.frombuffer(audio_buffer[:read_size], dtype=np.int16)
          self.mic_level = np.abs(raw_data).mean() / 32768.0
          Clock.schedule_once(self.draw_audio_waveform)

          encoded_audio = base64.b64encode(audio_buffer[:read_size]).decode(
              'utf-8'
          )
          payload = {
              'type': 'audio_chunk',
              'audio': encoded_audio,
              'api_key': self.api_key,
              'mode': self.lang_spinner.text,
          }
          try:
            self.ws.send(json.dumps(payload))
          except:
            pass
      time.sleep(0.05)

  def process_and_stream_frame(self, dt):
    if not self.is_streaming or self.is_offline:
      return
    if (
        self.camera_left.texture
        and self.ws
        and self.ws.sock
        and self.ws.sock.connected
    ):
      texture = self.camera_left.texture
      raw_bytes = texture.pixels
      if self.has_motion(raw_bytes):
        encoded_frame = base64.b64encode(raw_bytes).decode('utf-8')
        payload = {
            'type': 'video_frame',
            'image': encoded_frame,
            'roi': self.selected_roi,
            'api_key': self.api_key,
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

  def on_ai_message(self, ws, message):
    try:
      data = json.loads(message)
      if 'caption_token' in data:
        self.latest_translation += data['caption_token']
        self.update_ui(f'[color=ffffff]{self.latest_translation}[/color]')

      if 'audio_stream' in data and platform == 'android' and self.audio_track:
        pcm_bytes = base64.b64decode(data['audio_stream'])
        self.audio_track.write(pcm_bytes, 0, len(pcm_bytes))

      if 'boxes' in data:
        Clock.schedule_once(
            lambda dt: self.draw_ar_bounding_boxes(data['boxes'])
        )

      if data.get('is_final', False):
        self.save_flashcard('Original Text', self.latest_translation)
        self.latest_translation = ''
    except:
      self.update_ui(f'[color=ffffff]{message}[/color]')

  def on_camera_touch(self, instance, touch):
    if self.camera_left.collide_point(*touch.pos):
      if platform == 'android' and self.audio_track:
        self.audio_track.pause()
        self.audio_track.flush()
        self.audio_track.play()
      x, y = touch.x, touch.y
      self.selected_roi = {'x': x - 50, 'y': y - 50, 'w': 100, 'h': 100}
      self.draw_ar_bounding_boxes([self.selected_roi])
      self.update_status('[color=00ffff]● ROI FOCUSED[/color]')
      return True
    return False

  def draw_ar_bounding_boxes(self, boxes):
    self.camera_left.canvas.after.clear()
    with self.camera_left.canvas.after:
      Color(0, 1, 0.8, 0.9)
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

  def toggle_adaptive_quality(self, instance):
    if self.stream_fps_interval == 0.5:
      self.stream_fps_interval = 1.0
      self.battery_btn.text = '⚡ 1 FPS'
      self.battery_btn.background_color = (0.9, 0.5, 0.1, 0.85)
    else:
      self.stream_fps_interval = 0.5
      self.battery_btn.text = '⚡ 2 FPS'
      self.battery_btn.background_color = (0.1, 0.7, 0.4, 0.85)

    Clock.unschedule(self.process_and_stream_frame)
    Clock.schedule_interval(
        self.process_and_stream_frame, self.stream_fps_interval
    )

  def open_settings(self, instance):
    content = BoxLayout(orientation='vertical', padding=10, spacing=10)
    text_input = TextInput(
        text=self.api_key,
        hint_text='Enter Google Gemini API Key...',
        multiline=False,
    )
    save_btn = Button(text='Save Key', size_hint=(1, 0.3))
    content.add_widget(text_input)
    content.add_widget(save_btn)

    popup = Popup(title='API Settings', content=content, size_hint=(0.85, 0.4))

    def save_key(btn_instance):
      self.api_key = text_input.text.strip()
      self.update_status('[color=00ff00]API KEY SAVED[/color]')
      popup.dismiss()

    save_btn.bind(on_press=save_key)
    popup.open()

  def toggle_hud_mode(self, instance):
    self.hud_mode = not self.hud_mode
    if self.hud_mode:
      self.camera_right.opacity = 1
      self.camera_right.size_hint = (1, 1)
      self.hud_btn.text = '📱 Normal'
      self.update_status('[color=00ffff]● HUD AR ACTIVE[/color]')
    else:
      self.camera_right.opacity = 0
      self.camera_right.size_hint = (0, 1)
      self.hud_btn.text = '🕶 HUD'
      self.update_status('[color=00ff00]● ULTRA LIVE AR[/color]')

  def init_db(self):
    self.conn = sqlite3.connect('lingolens_ultra.db')
    self.cursor = self.conn.cursor()
    self.cursor.execute(
        'CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, text TEXT,'
        ' lang TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
    )
    self.cursor.execute(
        'CREATE TABLE IF NOT EXISTS flashcards (id INTEGER PRIMARY KEY, phrase'
        ' TEXT, translation TEXT, review_count INT DEFAULT 0)'
    )
    self.conn.commit()

  def save_flashcard(self, text, translation):
    if text.strip() and translation.strip():
      self.cursor.execute(
          'INSERT INTO flashcards (phrase, translation) VALUES (?, ?)',
          (text, translation),
      )
      self.conn.commit()

  def show_flashcards(self, instance):
    self.cursor.execute(
        'SELECT phrase, translation FROM flashcards ORDER BY id DESC LIMIT 15'
    )
    cards = self.cursor.fetchall()

    content = BoxLayout(orientation='vertical', padding=10, spacing=10)
    card_text = '\n\n'.join(
        [f'🎴 {c[0]}\n➔ {c[1]}' for c in cards]
    ) or 'No Flashcards Saved Yet.'

    scroll = ScrollView()
    lbl = Label(text=card_text, size_hint_y=None, font_size='16sp', markup=True)
    lbl.bind(texture_size=lbl.setter('size'))
    scroll.add_widget(lbl)
    content.add_widget(scroll)

    Popup(title='Smart Flashcards', content=content, size_hint=(0.9, 0.8)).open()

  def websocket_thread(self):
    while self.should_reconnect:
      try:
        self.update_status('[color=ffff00]● CONNECTING...[/color]')
        self.ws = websocket.WebSocketApp(
            'wss://echo.websocket.org',
            on_message=self.on_ai_message,
            on_error=lambda ws, e: self.handle_offline_mode(),
            on_close=lambda ws, c, m: self.handle_offline_mode(),
            on_open=lambda ws: self.update_status(
                '[color=00ff00]● ULTRA LIVE AR[/color]'
            ),
        )
        self.ws.run_forever()
      except:
        self.handle_offline_mode()
      time.sleep(3)

  def handle_offline_mode(self):
    self.is_offline = True
    self.update_status('[color=ff9900]● OFFLINE FALLBACK[/color]')

  def copy_to_clipboard(self, instance):
    if self.ar_label.text:
      Clipboard.copy(self.ar_label.text)
      self.update_status('[color=00ff00]COPIED![/color]')

  def toggle_streaming(self, instance):
    self.is_streaming = not self.is_streaming
    self.toggle_btn.text = 'Resume' if not self.is_streaming else 'Pause'

  def update_ui(self, text):
    Clock.schedule_once(lambda dt: setattr(self.ar_label, 'text', text))

  def update_status(self, text):
    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', text))


if __name__ == '__main__':
  LingoLensUltraApp().run()
