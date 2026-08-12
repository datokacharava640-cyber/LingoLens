import json
import base64
import threading
from queue import Queue
import websocket

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.clock import Clock

# Render WSS მისამართი (LingoLens-2)
PROXY_URL = "wss://lingolens-2-ylqe.onrender.com"

class LingoLensApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.label = Label(
            text="LingoLens Live AI - მიერთება...", 
            font_name="NotoSansGeorgian.ttf",
            font_size='18sp'
        )
        self.layout.add_widget(self.label)
        
        # AI ხმის დაკვრის რიგი (Queue)
        self.audio_queue = Queue()
        self.audio_track = None
        self.recorder = None
        
        return self.layout

    def update_label(self, text):
        Clock.schedule_once(lambda dt: setattr(self.label, 'text', text))

    def on_start(self):
        if platform == 'android':
            self.request_android_permissions()
        else:
            threading.Thread(target=self.connect_to_proxy, daemon=True).start()

    def request_android_permissions(self):
        try:
            from android.permissions import request_permissions, Permission, check_permission

            def permissions_callback(permissions, grants):
                if all(grants):
                    self.update_label("ნებართვა გაცემულია, ვუერთდებით...")
                    self.init_android_audio()
                    self.acquire_wakelock()
                    threading.Thread(target=self.connect_to_proxy, daemon=True).start()
                else:
                    self.update_label("გთხოვთ მოგვცეთ მიკროფონის ნებართვა")

            permissions_to_request = [Permission.RECORD_AUDIO, Permission.CAMERA]
            
            if check_permission(Permission.RECORD_AUDIO):
                self.init_android_audio()
                self.acquire_wakelock()
                threading.Thread(target=self.connect_to_proxy, daemon=True).start()
            else:
                request_permissions(permissions_to_request, permissions_callback)
        except Exception as e:
            print(f"[Permissions Error]: {e}")
            threading.Thread(target=self.connect_to_proxy, daemon=True).start()

    def init_android_audio(self):
        """მიკროფონის (AudioRecord) და დინამიკის (AudioTrack) ინიციალიზაცია"""
        try:
            from jnius import autoclass
            AudioRecord = autoclass('android.media.AudioRecord')
            AudioTrack = autoclass('android.media.AudioTrack')
            AudioManager = autoclass('android.media.AudioManager')
            MediaRecorder = autoclass('android.media.MediaRecorder$AudioSource')
            AudioFormat = autoclass('android.media.AudioFormat')
            AcousticEchoCanceler = autoclass('android.media.audiofx.AcousticEchoCanceler')

            # 1. მიკროფონის ინიციალიზაცია (16kHz PCM input)
            mic_sample_rate = 16000
            min_mic_buff = AudioRecord.getMinBufferSize(
                mic_sample_rate, 
                AudioFormat.CHANNEL_IN_MONO, 
                AudioFormat.ENCODING_PCM_16BIT
            )
            
            self.recorder = AudioRecord(
                MediaRecorder.VOICE_COMMUNICATION,
                mic_sample_rate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                max(min_mic_buff, 2048)
            )
            
            # Echo Cancellation-ის ჩართვა
            if AcousticEchoCanceler.isAvailable():
                aec = AcousticEchoCanceler.create(self.recorder.getAudioSessionId())
                if aec:
                    aec.setEnabled(True)

            # 2. დინამიკის ინიციალიზაცია AI-ის ხმისთვის (24kHz PCM output Gemini-დან)
            speaker_sample_rate = 24000
            min_speaker_buff = AudioTrack.getMinBufferSize(
                speaker_sample_rate,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )

            self.audio_track = AudioTrack(
                AudioManager.STREAM_MUSIC,
                speaker_sample_rate,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                max(min_speaker_buff * 2, 4096),
                AudioTrack.MODE_STREAM
            )
            self.audio_track.play()

            # აუდიო დამკვრელი თრედის გაშვება
            threading.Thread(target=self._audio_player_worker, daemon=True).start()

        except Exception as e:
            print(f"[Audio Init Error]: {e}")

    def _audio_player_worker(self):
        """AI-სგან მიღებული PCM ბაიტების უწყვეტი დაკვრა"""
        from jnius import jarray
        while True:
            pcm_bytes = self.audio_queue.get()
            if pcm_bytes is None:
                break
            if self.audio_track:
                try:
                    java_bytes = jarray('b')(pcm_bytes)
                    self.audio_track.write(java_bytes, 0, len(java_bytes))
                except Exception as e:
                    print(f"[Audio Track Write Error]: {e}")
            self.audio_queue.task_done()

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
            self.update_label("LingoLens: AI-სთან კავშირი დამყარდა")
            
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
            
            # მიკროფონის სტრიმინგის დაწყება
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
                            # მიღებული აუდიო იგზავნება დაკვრის რიგში
                            self.audio_queue.put(pcm_bytes)
            except Exception as e:
                print(f"[Message Error]: {e}")

        def on_error(ws, error):
            self.update_label(f"შეცდომა: {error}")

        def on_close(ws, close_status_code, close_msg):
            self.update_label("კავშირი გაწყდა")

        ws = websocket.WebSocketApp(
            PROXY_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.run_forever()

    def stream_mic_audio(self, ws):
        if platform == 'android' and self.recorder:
            try:
                from jnius import jarray
                self.recorder.startRecording()
                buffer_size = 1024
                # Native Java byte array მიკროფონიდან წასაკითხად
                java_buffer = jarray('b')([0] * buffer_size)
                
                while ws.sock and ws.sock.connected:
                    read_bytes = self.recorder.read(java_buffer, 0, buffer_size)
                    if read_bytes > 0:
                        raw_bytes = bytes(java_buffer[:read_bytes])
                        encoded_audio = base64.b64encode(raw_bytes).decode('utf-8')
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
