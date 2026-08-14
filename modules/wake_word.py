import time
import threading
import requests
from kivy.utils import platform

# Android/PyJNIus და SpeechRecognition იმპორტის უსაფრთხოება
try:
    import speech_recognition as sr
except ImportError:
    sr = None

def process_voice_command(text, api_key=""):
    """
    ნაბიჯი 2 & 3: Gemini AI-ს ინტელექტი — ამოიცნობს ენასა და ბრძანებას
    (მაგ: "ლინგოლენს გადამითარგმნე ეს იტალიურად: გამარჯობა")
    """
    print(f"[LingoLens AI] დამუშავება: {text}")
    
    prompt = (
        f"შენ ხარ LingoLens AI ხმოვანი ასისტენტი. "
        f"მომხმარებელმა თქვა: '{text}'. "
        f"თუ მომხმარებელი ითხოვს თარგმანს (მაგ. იტალიურად, ინგლისურად, გერმანულად და ა.შ.), "
        f"გადათარგმნე მოთხოვნილ ენაზე და დააბრუნე მხოლოს ნათარგმნი ტექსტი. "
        f"თუ ჩვეულებრივი შეკითხვაა, უპასუხე მოკლედ იმავე ენაზე."
    )

    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini API Error: {e}")

    # Fallback: უფასო Google Translate
    try:
        gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={text}"
        res = requests.get(gt_url, timeout=5).json()
        return res[0][0][0]
    except Exception as e:
        return f"შეცდომა: {e}"

def speak_response(text):
    """
    ნაბიჯი 4: ხმოვანი პასუხი (Text-To-Speech)
    """
    print(f"[LingoLens TTS]: {text}")
    if platform == 'android':
        try:
            from jnius import autoclass
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            Locale = autoclass('java.util.Locale')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            tts = TextToSpeech(PythonActivity.mActivity, None)
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
        except Exception as e:
            print(f"Android TTS Error: {e}")

def listen_loop(api_key=""):
    """
    ნაბიჯი 1: ფონური მოსმენა "LingoLens" / "ლინგოლენს" ძახილზე
    """
    if not sr:
        print("SpeechRecognition ბიბლიოთეკა არ არის დაინსტალირებული.")
        return

    recognizer = sr.Recognizer()
    
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("[Wake Word] LingoLens უსმენს...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                
                # ქართული ხმის ამოცნობა
                command = recognizer.recognize_google(audio, language="ka-GE")
                command_lower = command.lower()

                # "LingoLens" ან "ლინგოლენს" გააქტიურება
                if "ლინგოლენს" in command_lower or "lingolens" in command_lower or "გადამითარგმნე" in command_lower:
                    print(f"ბრძანება მიღებულია: {command}")
                    
                    # AI-ით თარგმნა/დამუშავება
                    result = process_voice_command(command, api_key)
                    
                    # ხმოვანი პასუხი
                    speak_response(result)

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"Wake Word Loop Error: {e}")
            time.sleep(2)

def start(api_key=""):
    """
    მთავარი ფუნქცია, რომელსაც main.py იძახებს
    """
    thread = threading.Thread(target=listen_loop, args=(api_key,), daemon=True)
    thread.start()
    print("Wake Word ფონური სერვისი გაეშვა!")

if __name__ == "__main__":
    start()
