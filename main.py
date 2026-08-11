import json
import base64
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform

class LingoLensApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.label = Label(
            text="LingoLens Live AI - მზადაა გასაშვებად", 
            font_name="NotoSansGeorgian.ttf",
            font_size='20sp'
        )
        self.layout.add_widget(self.label)
        return self.layout

    def on_start(self):
        if platform == 'android':
            self.init_android_audio_with_aec()
            self.acquire_wakelock()

    # Android Native Acoustic Echo Cancellation (AEC) & Noise Suppressor
    def init_android_audio_with_aec(self, sample_rate=16000, buffer_size=1024):
        try:
            from jnius import autoclass
            AudioRecord = autoclass('android.media.AudioRecord')
            MediaRecorder = autoclass('android.media.MediaRecorder$AudioSource')
            AudioFormat = autoclass('android.media.AudioFormat')
            AcousticEchoCanceler = autoclass('android.media.audiofx.AcousticEchoCanceler')
            NoiseSuppressor = autoclass('android.media.audiofx.NoiseSuppressor')

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

            audio_session_id = self.recorder.getAudioSessionId()

            if AcousticEchoCanceler.isAvailable():
                aec = AcousticEchoCanceler.create(audio_session_id)
                aec.setEnabled(True)
                print("[AudioFX]: AEC წარმატებით ჩაირთო.")

            if NoiseSuppressor.isAvailable():
                ns = NoiseSuppressor.create(audio_session_id)
                ns.setEnabled(True)
                print("[AudioFX]: Noise Suppressor ჩაირთო.")

        except Exception as e:
            print(f"[AudioFX Error]: {e}")

    # WakeLock - პროცესორის დაძინების აღსაკვეთად (სერვისის გარეშე)
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
            print("[App]: WakeLock წარმატებით გააქტიურდა.")
        except Exception as e:
            print(f"[WakeLock Error]: {e}")

    # Gemini Multimodal Live API Protocol Handshake
    def send_gemini_setup_handshake(self, ws):
        setup_message = {
            "setup": {
                "model": "models/gemini-2.0-flash-exp",
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": "Puck"
                            }
                        }
                    }
                }
            }
        }
        ws.send(json.dumps(setup_message))
        print("[Gemini Protocol]: Live API Handshake გაიგზავნა.")

if __name__ == '__main__':
    LingoLensApp().run()
