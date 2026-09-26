# ==============================================================================
# LingoLens AI - Text-to-Speech Engine (TTS)
# ==============================================================================

import os
import threading

def speak(text, lang="en", user_data_dir="", callback=None):
    """
    ტექსტის ხმოვანი წაკითხვის მთავარი ფუნქცია.
    მუშაობს როგორც Android-ზე, ისე კომპიუტერზე.
    """
    if not text or not text.strip():
        if callback:
            callback("ტექსტი ცარიელია")
        return

    def run_tts():
        try:
            # ვცდილობთ Android-ის ჩაშენებული TTS-ის გამოყენებას
            from kivy.utils import platform
            if platform == 'android':
                try:
                    from jnius import autoclass
                    Locale = autoclass('java.util.Locale')
                    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    
                    # ენის კოდის კონვერტაცია (მაგ: 'ka', 'en', 'ru')
                    java_lang = Locale(lang)
                    
                    # აქ ვქმნით დამხმარე კლასს, რომ თავიდან ავიცილოთ დაბლოკვა
                    # თუმცა უმარტივეს შემთხვევაში ვიყენებთ აქტივობის კონტექსტს
                    context = PythonActivity.mActivity
                    
                    # შენიშვნა: Android-ში TTS ინიციალიზაცია მოითხოვს სრულ მომზადებას, 
                    # ამიტომ ალტერნატივისთვის ვიყენებთ აგრეთვე gTTS-ს ან უსაფრთხო გამოძახებას
                except Exception as ex:
                    print("Android TTS direct error, trying gTTS fallback:", ex)

            # უნივერსალური და სანდო ალტერნატივა: gTTS (Google Text-to-Speech)
            # რომელიც მუშაობს ინტერნეტით და ქმნის სუფთა აუდიო ფაილს
            from gtts import gTTS
            import tempfile
            
            # ვქმნით დროებით ფაილს აუდიოსთვის
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # შევინახოთ დროებით ფაილად
            temp_dir = user_data_dir if user_data_dir else tempfile.gettempdir()
            audio_path = os.path.join(temp_dir, "lingolens_speech.mp3")
            tts.save(audio_path)

            # ვცდილობთ დაკვრას პლატფორმის შესაბამისი დამკვრელით
            if platform == 'android':
                try:
                    from audioplayer import AudioPlayer
                    player = AudioPlayer(audio_path)
                    player.play()
                except Exception as ap_err:
                    print("Audioplayer error:", ap_err)
            else:
                # კომპიუტერზე (Windows/Mac/Linux) დაკვრა playsound-ით ან os-ის ბრძანებით
                try:
                    from playsound import playsound
                    playsound(audio_path)
                except Exception:
                    # თუ playsound არ არის, ვცდილობთ სისტემურ ბრძანებას
                    if os.name == 'nt':
                        os.startfile(audio_path)
                    elif sys.platform == 'darwin':
                        os.system(f"afplay '{audio_path}'")
                    else:
                        os.system(f"xdg-open '{audio_path}'")

            if callback:
                callback("წაკითხვა დასრულდა")

        except Exception as e:
            error_str = f"TTS Error: {str(e)}"
            print(error_str)
            if callback:
                callback(error_str)

    # ვუშვებთ ცალკე ნაკადში (Thread), რომ აპლიკაცია არ გაიჭედოს წაკითხვის დროს
    threading.Thread(target=run_tts, daemon=True).start()
