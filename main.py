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
import websocket


class LingoLensLiveApp(App):

  def build(self):
    self.layout = BoxLayout(orientation='vertical')

    # 1. Real-time Live Camera View
    self.camera = Camera(play=True, resolution=(640, 480))
    self.layout.add_widget(self.camera)

    # 2. AI-ს რეალური დროის თარგმანის/პასუხის ზონა
    self.scroll = ScrollView(size_hint=(1, 0.3))
    self.label = Label(
        text='[Live AI Connection Setup...]',
        size_hint_y=None,
        font_size='18sp',
        markup=True,
    )
    self.label.bind(texture_size=self.label.setter('size'))
    self.scroll.add_widget(self.label)
    self.layout.add_widget(self.scroll)

    self.ws = None
    # იწყებს WebSocket კავშირს ცალკე ნაკადში (Thread)
    threading.Thread(target=self.connect_websocket, daemon=True).start()

    # ყოველ 0.5 წამში (წამში 2-ჯერ) აგზავნის კადრს სერვერზე
    Clock.schedule_interval(self.stream_frame_to_ai, 0.5)

    return self.layout

  def connect_websocket(self):
    try:
      # შეცვალეთ თქვენი Live AI WebSocket Endpoint-ით
      self.ws = websocket.WebSocketApp(
          'wss://echo.websocket.org',  # ტესტირებისთვის, ჩაანაცვლეთ AI სერვერით
          on_message=self.on_ai_message,
          on_error=self.on_ws_error,
          on_open=self.on_ws_open,
      )
      self.ws.run_forever()
    except Exception as e:
      self.update_ui(f'[color=ff0000]WS Connection Fail: {e}[/color]')

  def on_ws_open(self, ws):
    self.update_ui('[color=00ff00]✓ AI Live Stream Connected![/color]')

  def on_ws_error(self, ws, error):
    self.update_ui(f'[color=ff0000]WS Error: {error}[/color]')

  def on_ai_message(self, ws, message):
    # AI სერვერიდან მიღებული თარგმანი/პასუხი
    try:
      data = json.loads(message)
      translated_text = data.get('translation', message)
      self.update_ui(f'[color=ffffff]AI: {translated_text}[/color]')
    except:
      self.update_ui(f'[color=ffffff]AI: {message}[/color]')

  def stream_frame_to_ai(self, dt):
    # იღებს კადრს Kivy Camera-დან და გზავნის WebSocket-ით
    if (
        self.camera.texture
        and self.ws
        and self.ws.sock
        and self.ws.sock.connected
    ):
      texture = self.camera.texture
      raw_bytes = texture.pixels

      # Base64 კოდირება რეალურ დროში გაგზავნისთვის
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
