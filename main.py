import json
import base64
import threading
import websocket
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import platform

# Render-ის WSS მისამართი
PROXY_URL = "wss://lingolens-2euo.onrender.com"

class LingoLensApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.label = Label(
            text="LingoLens Live AI - მიერთება...", 
            font_name="NotoSansGeorgian.ttf",
            font_size='18sp'
        )
        self.layout.add_widget(self.label)
        return self.layout

    def on_start(self):
        if platform == 'android':
            self.request_android_permissions()
        else:
            threading.Thread(target=self.connect_to_proxy, daemon=True).start()

    def request_android_permissions(self):
        try:
            from android.permissions import request_permissions, Permission, check_permission

            def permissions_callback(permissions, grants):
                # ნებართვის მიღების შემდეგ ირთვება აუდიო და მიერთება
                if all(grants):
                    self.label.text = "ნებართვა გაცემულია, ვუერთდებით..."
                    self.init_android_audio_with_aec()
                    self.acquire_wakelock()
                    threading.Thread(target=self.connect_to_proxy, daemon=True).start()
                else:
                    self.label.text = "გთხოვთ მოგვცეთ მიკროფონის ნებართვა"

            # ითხოვს მხოლოდ იმ ნებართვებს, რაც Runtime-შია საჭირო
            permissions_to_request = [Permission.RECORD_AUDIO, Permission.CAMERA]
            
            if check_permission(Permission.RECORD_AUDIO):
                self.init_android_audio_with_aec()
                self.acquire_wakelock()
                threading.Thread(target=self.connect_to_proxy, daemon=True).start()
            else:
                request_permissions(permissions_to_request, permissions_callback)
        except Exception as e:
            print(f"[Permissions Error]: {e}")
            threading.Thread(target=self.connect_to_proxy, daemon=True).start()

    def init_android_audio_with_aec(self, sample_rate=16000, buffer_size=1024):
        try:
            from jnius import autoclass
            AudioRecord = autoclass('android.media.AudioRecord')
            MediaRecorder = autoclass('android.media.MediaRecorder$AudioSource')
            AudioFormat = autoclass('android.media.AudioFormat')
            AcousticEchoCanceler = autoclass('android.media.audiofx.AcousticEchoCanceler')
            
            min_buff = AudioRecord.getMinBufferSize(
                sample_rate, 
                AudioFormat.CHANNEL_IN_MONO, 
                AudioFormat.ENCODING_PCM_16BIT
            )
            
            self.recorder = AudioRecord(
                MediaRecorder.VOICE_COMMUNICATION,
                sample_rate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                max(min_buff, buffer_size)
            )
            
            if AcousticEchoCanceler.isAvailable():
                aec = AcousticEchoCanceler.create(self.recorder.getAudioSessionId())
                if aec:
                    aec.setEnabled(True)
        except Exception as e:
            print(f"[AudioFX Error]: {e}")

    def acquire_wakelock(self):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            PowerManager = autoclass('android.os.PowerManager')
            
            activity = PythonActivity.mActivity
            power_manager = activity.getSystemService(Context.POWER_SERVICE)
            self.wake_lock = power_manager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK, 
                "LingoLens::AppWakeLock"
            )
            self.wake_lock.acquire()
        except Exception as e:
            print(f"[WakeLock Error]: {e}")

    def connect_to_proxy(self):
        def on_open(ws):
            self.label.text = "LingoLens: AI-სთან კავშირი დამყარდა"
            
            setup_msg = {
                "setup": {
                    "model": "models/gemini-2.0-flash-exp",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {"voiceName": "Puck"}
                            }
                        }
                    }
                }
            }
            ws.send(json.dumps(setup_msg))
            
            threading.Thread(target=self.stream_mic_audio, args=(ws,), daemon=True).start()

        def on_message(ws, message):
            try:
                data = json.loads(message)
                if "serverContent" in data:
                    model_turn = data["serverContent"].get("modelTurn", {})
                    parts = model_turn.get("parts", [])
                    for part in parts:
                        if "inlineData" in part and part["inlineData"]["mimeType"].startswith("audio/pcm"):
                            pcm_base64 = part["inlineData"]["data"]
                            pcm_bytes = base64.b64decode(pcm_base64)
            except Exception as e:
                print(f"[Message Error]: {e}")

        def on_error(ws, error):
            self.label.text = f"შეცდომა: {error}"

        def on_close(ws, close_status_code, close_msg):
            self.label.text = "კავშირი გაწყდა"

        ws = websocket.WebSocketApp(
            PROXY_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.run_forever()

    def stream_mic_audio(self, ws):
        if platform == 'android' and hasattr(self, 'recorder'):
            try:
                self.recorder.startRecording()
                buffer_size = 1024
                audio_buffer = bytearray(buffer_size)
                
                while ws.sock and ws.sock.connected:
                    read_bytes = self.recorder.read(audio_buffer, 0, buffer_size)
                    if read_bytes > 0:
                        encoded_audio = base64.b64encode(audio_buffer[:read_bytes]).decode('utf-8')
                        realtime_input = {
                            "realtimeInput": {
                                "mediaChunks": [
                                    {
                                        "mimeType": "audio/pcm",
                                        "data": encoded_audio
                                    }
                                ]
                            }
                        }
                        ws.send(json.dumps(realtime_input))
            except Exception as e:
                print(f"[Stream Error]: {e}")

if __name__ == '__main__':
    LingoLensApp().run()
