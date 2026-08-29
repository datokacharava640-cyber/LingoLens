import os
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.textinput import TextInput

# Plyer-ის უსაფრთხო იმპორტი
try:
  from plyer import tts
except Exception:
  tts = None

# ქართული შრიფტის რეგისტრაცია
LabelBase.register(
    name='Roboto',
    fn_regular='font.ttf',
    fn_bold='font.ttf',
    fn_italic='font.ttf',
    fn_bolditalic='font.ttf',
)

LANGUAGES = {
    'ka': 'ქართული (Georgian)',
    'en': 'English (ინგლისური)',
    'es': 'Español (ესპანური)',
    'fr': 'Français (ფრანგული)',
    'de': 'Deutsch (გერმანული)',
    'ru': 'Русский (რუსული)',
    'zh': '中文 (ჩინური)',
    'ja': '日本語 (იაპონური)',
    'ko': '한국어 (კორეული)',
    'it': 'Italiano (იტალიური)',
    'pt': 'Português (პორტუგალიური)',
    'tr': 'Türkçe (თურქული)',
    'ar': 'العربية (არაბული)',
    'el': 'Ελληνικά (ბერძნული)',
    'uk': 'Українська (უკრაინული)',
    'pl': 'Polski (პოლონური)',
    'nl': 'Nederlands (ჰოლანდიური)',
    'hi': 'हिन्दी (ჰინდი)',
    'fa': 'فارسی (სპარსული)',
    'he': 'עברית (ებრაული)',
    'sv': 'Svenska (შვედური)',
    'no': 'Norsk (ნორვეგიული)',
    'fi': 'Suomi (ფინური)',
    'da': 'Dansk (დანიური)',
    'cs': 'Čeština (ჩეხური)',
    'hu': 'Magyar (უნგრული)',
    'ro': 'Română (რუმინული)',
    'az': 'Azərbaycan (აზერბაიჯანული)',
    'hy': 'Հայერენ (სომხური)',
    'kk': 'Қазақ (ყაზახური)',
    'uz': 'Oʻzbek (უზბეკური)',
    'th': 'ไทย (ტაილანდური)',
    'vi': 'Tiếng Việt (ვიეტნამური)',
    'id': 'Bahasa Indonesia (ინდონეზიური)',
}


class SplashScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
    layout.add_widget(
        Label(
            text='LingoLens Ultra Pro',
            font_size='32sp',
            font_name='Roboto',
            color=(0.2, 0.6, 1, 1),
        )
    )
    layout.add_widget(
        Label(
            text='იტვირთება...',
            font_size='16sp',
            font_name='Roboto',
            color=(0.7, 0.7, 0.7, 1),
        )
    )
    self.add_widget(layout)

  def on_enter(self):
    Clock.schedule_once(self.switch_to_main, 2.0)

  def switch_to_main(self, dt):
    self.manager.transition = SlideTransition(direction='left')
    self.manager.current = 'main_menu'


class MainMenuScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
    layout.add_widget(
        Label(
            text='LingoLens - მთავარი მენიუ',
            font_size='22sp',
            font_name='Roboto',
            size_hint=(1, 0.1),
        )
    )

    grid = GridLayout(cols=2, spacing=15, padding=10, size_hint=(1, 0.8))

    btn_trans = Button(
        text='ტექსტის\nთარგმნა',
        font_name='Roboto',
        halign='center',
        background_color=(0.2, 0.6, 1, 1),
    )
    btn_trans.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'translator')
    )

    btn_voice = Button(
        text='ორმხრივი\nხმოვანი თარგმნა',
        font_name='Roboto',
        halign='center',
        background_color=(0.9, 0.4, 0.2, 1),
    )
    btn_voice.bind(on_press=lambda x: setattr(self.manager, 'current', 'voice'))

    btn_cam = Button(
        text='კამერით\nსკანირება',
        font_name='Roboto',
        halign='center',
        background_color=(0.3, 0.8, 0.4, 1),
    )
    btn_cam.bind(on_press=lambda x: setattr(self.manager, 'current', 'camera'))

    btn_set = Button(
        text='პარამეტრები',
        font_name='Roboto',
        halign='center',
        background_color=(0.6, 0.4, 0.8, 1),
    )

    grid.add_widget(btn_trans)
    grid.add_widget(btn_voice)
    grid.add_widget(btn_cam)
    grid.add_widget(btn_set)

    layout.add_widget(grid)
    self.add_widget(layout)


class TranslatorScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.src_lang = 'ka'
    self.target_lang = 'en'
    self.server_url = 'https://lingo-lens-eight.vercel.app'
    self.tts_engine = None
    self.tts_listener = None

    layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

    # 1. უკან დაბრუნების ღილაკი
    btn_back = Button(
        text='< უკან',
        font_name='Roboto',
        size_hint=(0.3, 0.08),
        background_color=(0.8, 0.2, 0.2, 1),
    )
    btn_back.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'main_menu')
    )
    layout.add_widget(btn_back)

    # 2. ენების არჩევის ზოლი
    lang_layout = BoxLayout(size_hint=(1, 0.1), spacing=5)

    self.btn_src = Button(
        text=LANGUAGES[self.src_lang], font_name='Roboto', size_hint=(0.4, 1)
    )
    self.btn_src.bind(on_release=self.open_src_dropdown)

    self.btn_target = Button(
        text=LANGUAGES[self.target_lang],
        font_name='Roboto',
        size_hint=(0.4, 1),
    )
    self.btn_target.bind(on_release=self.open_target_dropdown)

    btn_swap = Button(text='<->', size_hint=(0.2, 1))
    btn_swap.bind(on_press=self.swap_languages)

    lang_layout.add_widget(self.btn_src)
    lang_layout.add_widget(btn_swap)
    lang_layout.add_widget(self.btn_target)
    layout.add_widget(lang_layout)

    # 3. ეკრანის ჰორიზონტალური გაყოფა გვერდიგვერდ
    content_layout = BoxLayout(
        orientation='horizontal', size_hint=(1, 0.55), spacing=10
    )

    self.input_text = TextInput(
        hint_text='შეიყვანეთ ტექსტი...',
        font_name='Roboto',
        multiline=True,
        size_hint=(0.5, 1),
    )

    self.result_label = Label(
        text='შედეგი გამოჩნდება აქ',
        font_name='Roboto',
        halign='center',
        valign='middle',
        size_hint=(0.5, 1),
    )
    self.result_label.bind(size=self.result_label.setter('text_size'))

    content_layout.add_widget(self.input_text)
    content_layout.add_widget(self.result_label)
    layout.add_widget(content_layout)

    # 4. თარგმნის ღილაკი
    btn_action = Button(
        text='თარგმნა',
        font_name='Roboto',
        size_hint=(1, 0.1),
        background_color=(0.2, 0.6, 1, 1),
    )
    btn_action.bind(on_press=self.translate_text)
    layout.add_widget(btn_action)

    # 5. განხმოვანების ღილაკი
    btn_speak = Button(
        text='განხმოვანება',
        font_name='Roboto',
        size_hint=(1, 0.1),
        background_color=(0.5, 0.3, 0.8, 1),
    )
    btn_speak.bind(on_press=self.speak_result)
    layout.add_widget(btn_speak)

    self.add_widget(layout)

  def open_src_dropdown(self, widget):
    dropdown = DropDown()
    for code, name in LANGUAGES.items():
      btn = Button(text=name, font_name='Roboto', size_hint_y=None, height=44)
      btn.bind(
          on_release=lambda b, c=code, n=name: self.set_src(c, n, dropdown)
      )
      dropdown.add_widget(btn)
    dropdown.open(widget)

  def set_src(self, code, name, dropdown):
    self.src_lang = code
    self.btn_src.text = name
    dropdown.dismiss()

  def open_target_dropdown(self, widget):
    dropdown = DropDown()
    for code, name in LANGUAGES.items():
      btn = Button(text=name, font_name='Roboto', size_hint_y=None, height=44)
      btn.bind(
          on_release=lambda b, c=code, n=name: self.set_target(c, n, dropdown)
      )
      dropdown.add_widget(btn)
    dropdown.open(widget)

  def set_target(self, code, name, dropdown):
    self.target_lang = code
    self.btn_target.text = name
    dropdown.dismiss()

  def swap_languages(self, instance):
    self.src_lang, self.target_lang = self.target_lang, self.src_lang
    self.btn_src.text = LANGUAGES.get(self.src_lang, self.src_lang)
    self.btn_target.text = LANGUAGES.get(self.target_lang, self.target_lang)

    current_input = self.input_text.text.strip()
    current_result = self.result_label.text.strip()

    if (
        current_result
        and 'შეცდომა' not in current_result
        and 'შედეგი' not in current_result
    ):
      self.input_text.text = current_result
      self.result_label.text = (
          current_input if current_input else 'შედეგი გამოჩნდება აქ'
      )

  def translate_text(self, instance):
    text = self.input_text.text.strip()
    if not text:
      self.result_label.text = 'შეიყვანეთ ტექსტი!'
      return

    self.result_label.text = 'მიმდინარეობს თარგმნა...'
    try:
      url = f'{self.server_url}/api/index'
      payload = {
          'text': text,
          'source': self.src_lang,
          'target': self.target_lang,
      }
      headers = {'Content-Type': 'application/json'}

      resp = requests.post(url, json=payload, headers=headers, timeout=10)

      if resp.status_code == 200:
        data = resp.json()
        self.result_label.text = data.get(
            'translated_text', 'თარგმანი ვერ მოიძებნა'
        )
      else:
        try:
          err_msg = resp.json().get('error', resp.text)
          self.result_label.text = f'შეცდომა {resp.status_code}: {err_msg}'
        except Exception:
          self.result_label.text = f'სერვერის შეცდომა: {resp.status_code}'

    except Exception as e:
      self.result_label.text = f'ქსელის შეცდომა: {str(e)}'

  def speak_result(self, instance):
    text_to_speak = self.result_label.text.strip()
    if (
        not text_to_speak
        or 'შეცდომა' in text_to_speak
        or 'შედეგი' in text_to_speak
    ):
      return

    # Android Native TTS (Pyjnius)
    try:
      from jnius import autoclass

      PythonActivity = autoclass('org.kivy.android.PythonActivity')
      TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
      Locale = autoclass('java.util.Locale')

      activity = PythonActivity.mActivity

      class TTSOnInitListener(
          autoclass('android.speech.tts.TextToSpeech$OnInitListener')
      ):

        def __init__(self, text, lang, tts_ref):
          super().__init__()
          self.text = text
          self.lang = lang
          self.tts_ref = tts_ref

        def onInit(self, status):
          if status == TextToSpeech.SUCCESS:
            if self.lang == 'en':
              self.tts_ref.setLanguage(Locale.ENGLISH)
            else:
              self.tts_ref.setLanguage(Locale(self.lang))

            self.tts_ref.speak(self.text, TextToSpeech.QUEUE_FLUSH, None, None)

      self.tts_listener = TTSOnInitListener(
          text_to_speak, self.target_lang, None
      )
      self.tts_engine = TextToSpeech(activity, self.tts_listener)
      self.tts_listener.tts_ref = self.tts_engine
      return
    except Exception as e:
      print(f'Pyjnius error: {e}')

    # Plymouth / Plyer fallback
    try:
      if tts:
        tts.speak(text_to_speak)
      else:
        self.result_label.text = 'განხმოვანება არ არის მხარდაჭერილი'
    except Exception as e:
      self.result_label.text = f'ხმის შეცდომა: {str(e)}'


class VoiceScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
    btn_back = Button(text='< უკან', font_name='Roboto', size_hint=(0.3, 0.08))
    btn_back.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'main_menu')
    )
    layout.add_widget(btn_back)

    layout.add_widget(
        Label(
            text='ორმხრივი ხმოვანი რეჟიმი',
            font_name='Roboto',
            font_size='18sp',
            size_hint=(1, 0.1),
        )
    )

    btn_mic1 = Button(
        text='საუბარი (ენა 1)',
        font_name='Roboto',
        size_hint=(1, 0.2),
        background_color=(0.2, 0.7, 0.3, 1),
    )
    btn_mic2 = Button(
        text='საუბარი (ენა 2)',
        font_name='Roboto',
        size_hint=(1, 0.2),
        background_color=(0.9, 0.5, 0.1, 1),
    )

    layout.add_widget(btn_mic1)
    layout.add_widget(btn_mic2)
    layout.add_widget(
        Label(
            text='დააჭირეთ ღილაკს და ილაპარაკეთ',
            font_name='Roboto',
            size_hint=(1, 0.4),
        )
    )
    self.add_widget(layout)


class CameraScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
    btn_back = Button(text='< უკან', font_name='Roboto', size_hint=(0.3, 0.08))
    btn_back.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'main_menu')
    )
    layout.add_widget(btn_back)

    layout.add_widget(
        Label(
            text='კამერით სკანირება (OCR)',
            font_name='Roboto',
            font_size='18sp',
            size_hint=(1, 0.1),
        )
    )

    btn_capture = Button(
        text='ფოტოს გადაღება და თარგმნა',
        font_name='Roboto',
        size_hint=(1, 0.2),
        background_color=(0.3, 0.6, 0.9, 1),
    )
    layout.add_widget(btn_capture)

    layout.add_widget(
        Label(
            text='მიმართეთ კამერა ტექსტზე',
            font_name='Roboto',
            size_hint=(1, 0.6),
        )
    )
    self.add_widget(layout)


class LingoLensApp(App):

  def build(self):
    sm = ScreenManager()
    sm.add_widget(SplashScreen(name='splash'))
    sm.add_widget(MainMenuScreen(name='main_menu'))
    sm.add_widget(TranslatorScreen(name='translator'))
    sm.add_widget(VoiceScreen(name='voice'))
    sm.add_widget(CameraScreen(name='camera'))
    return sm


if __name__ == '__main__':
  LingoLensApp().run()
