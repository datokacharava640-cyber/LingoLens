import os
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.textinput import TextInput
from plyer import tts

# ქართული შრიფტის რეგისტრაცია
LabelBase.register(
    name='Roboto',
    fn_regular='font.ttf',
    fn_bold='font.ttf',
    fn_italic='font.ttf',
    fn_bolditalic='font.ttf',
)

# მსოფლიოს ენების ვრცელი სია
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
    'hy': 'Հայերեն (სომხური)',
    'kk': 'Қазақ (ყაზახური)',
    'uz': 'Oʻzbek (უზბეკური)',
    'th': 'ไทย (ტაილანდური)',
    'vi': 'Tiếng Việt (ვიეტნამური)',
    'id': 'Bahasa Indonesia (ინდონეზიური)',
}


# 1. Splash Screen
class SplashScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(orientation='vertical')
    if os.path.exists('flag_animation.gif'):
      layout.add_widget(
          Image(
              source='flag_animation.gif',
              anim_loop=0,
              allow_stretch=True,
              keep_ratio=False,
          )
      )
    else:
      layout.add_widget(
          Label(text='LingoLens Ultra Pro', font_size='28sp', font_name='font.ttf')
      )
    self.add_widget(layout)

  def on_enter(self):
    Clock.schedule_once(self.switch_to_main, 3.5)

  def switch_to_main(self, dt):
    self.manager.transition = SlideTransition(direction='left')
    self.manager.current = 'main_menu'


# 2. მთავარი მენიუ
class MainMenuScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
    layout.add_widget(
        Label(
            text='LingoLens - მთავარი მენიუ',
            font_size='22sp',
            font_name='font.ttf',
            size_hint=(1, 0.1),
        )
    )

    grid = GridLayout(cols=2, spacing=15, padding=10, size_hint=(1, 0.8))

    btn_trans = Button(
        text='📝 ტექსტის\nთარგმნა',
        font_name='font.ttf',
        halign='center',
        background_color=(0.2, 0.6, 1, 1),
    )
    btn_trans.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'translator')
    )

    btn_voice = Button(
        text='🎙️ ორმხრივი\nხმოვანი თარგმნა',
        font_name='font.ttf',
        halign='center',
        background_color=(0.9, 0.4, 0.2, 1),
    )
    btn_voice.bind(on_press=lambda x: setattr(self.manager, 'current', 'voice'))

    btn_cam = Button(
        text='📷 კამერით\nსკანირება',
        font_name='font.ttf',
        halign='center',
        background_color=(0.3, 0.8, 0.4, 1),
    )
    btn_cam.bind(on_press=lambda x: setattr(self.manager, 'current', 'camera'))

    btn_set = Button(
        text='⚙️ პარამეტრები',
        font_name='font.ttf',
        halign='center',
        background_color=(0.6, 0.4, 0.8, 1),
    )

    grid.add_widget(btn_trans)
    grid.add_widget(btn_voice)
    grid.add_widget(btn_cam)
    grid.add_widget(btn_set)

    layout.add_widget(grid)
    self.add_widget(layout)


# 3. თარგმნის ეკრანი ჩამოშლადი ენების მენიუთი
class TranslatorScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.src_lang = 'en'
    self.target_lang = 'ka'
    self.server_url = 'https://lingo-lens-eight.vercel.app'

    layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

    # უკან დაბრუნება
    btn_back = Button(
        text='⬅️ უკან',
        font_name='font.ttf',
        size_hint=(0.3, 0.08),
        background_color=(0.8, 0.2, 0.2, 1),
    )
    btn_back.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'main_menu')
    )
    layout.add_widget(btn_back)

    # ენების არჩევანი (ჩამოშლადი მენიუებით)
    lang_layout = BoxLayout(size_hint=(1, 0.1), spacing=5)

    self.btn_src = Button(
        text=LANGUAGES[self.src_lang],
        font_name='font.ttf',
        size_hint=(0.4, 1),
    )
    self.btn_src.bind(on_release=self.open_src_dropdown)

    self.btn_target = Button(
        text=LANGUAGES[self.target_lang],
        font_name='font.ttf',
        size_hint=(0.4, 1),
    )
    self.btn_target.bind(on_release=self.open_target_dropdown)

    btn_swap = Button(text='⇄', size_hint=(0.2, 1))
    btn_swap.bind(on_press=self.swap_languages)

    lang_layout.add_widget(self.btn_src)
    lang_layout.add_widget(btn_swap)
    lang_layout.add_widget(self.btn_target)
    layout.add_widget(lang_layout)

    # შესაყვანი ველი
    self.input_text = TextInput(
        hint_text='შეიყვანეთ ტექსტი...',
        font_name='font.ttf',
        multiline=True,
        size_hint=(1, 0.3),
    )
    layout.add_widget(self.input_text)

    # თარგმნა
    btn_action = Button(
        text='თარგმნა',
        font_name='font.ttf',
        size_hint=(1, 0.1),
        background_color=(0.2, 0.6, 1, 1),
    )
    btn_action.bind(on_press=self.translate_text)
    layout.add_widget(btn_action)

    # შედეგი
    self.result_label = Label(
        text='შედეგი გამოჩნდება აქ',
        font_name='font.ttf',
        halign='center',
        valign='middle',
        size_hint=(1, 0.25),
    )
    self.result_label.bind(size=self.result_label.setter('text_size'))
    layout.add_widget(self.result_label)

    # განხმოვანება
    btn_speak = Button(
        text='🔊 განხმოვანება',
        font_name='font.ttf',
        size_hint=(1, 0.1),
        background_color=(0.5, 0.3, 0.8, 1),
    )
    btn_speak.bind(on_press=self.speak_result)
    layout.add_widget(btn_speak)

    self.add_widget(layout)

  # ჩამოშლადი მენიუ წყარო ენისთვის
  def open_src_dropdown(self, widget):
    dropdown = DropDown()
    for code, name in LANGUAGES.items():
      btn = Button(
          text=name, font_name='font.ttf', size_hint_y=None, height=44
      )
      btn.bind(on_release=lambda b, c=code, n=name: self.set_src(c, n, dropdown))
      dropdown.add_widget(btn)
    dropdown.open(widget)

  def set_src(self, code, name, dropdown):
    self.src_lang = code
    self.btn_src.text = name
    dropdown.dismiss()

  # ჩამოშლადი მენიუ სამიზნე ენისთვის
  def open_target_dropdown(self, widget):
    dropdown = DropDown()
    for code, name in LANGUAGES.items():
      btn = Button(
          text=name, font_name='font.ttf', size_hint_y=None, height=44
      )
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

  def translate_text(self, instance):
    text = self.input_text.text.strip()
    if not text:
      self.result_label.text = 'შეიყვანეთ ტექსტი!'
      return

    self.result_label.text = 'მიმდინარეობს თარგმნა...'
    try:
      resp = requests.post(
          f'{self.server_url}/api/index',
          json={
              'text': text,
              'source': self.src_lang,
              'target': self.target_lang,
          },
          timeout=10,
      )
      if resp.status_code == 200:
        self.result_label.text = resp.json().get(
            'translated_text', 'შეცდომა თარგმნისას'
        )
      else:
        self.result_label.text = f'სერვერის შეცდომა: {resp.status_code}'
    except Exception as e:
      self.result_label.text = f'შეცდომა: {str(e)}'

  def speak_result(self, instance):
    if self.result_label.text and 'შეცდომა' not in self.result_label.text:
      try:
        tts.speak(self.result_label.text)
      except Exception:
        self.result_label.text = 'განხმოვანება ხელმისაწვდომია Android-ზე'


# 4. ხმოვანი ეკრანი
class VoiceScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
    btn_back = Button(
        text='⬅️ უკან', font_name='font.ttf', size_hint=(0.3, 0.08)
    )
    btn_back.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'main_menu')
    )
    layout.add_widget(btn_back)

    layout.add_widget(
        Label(
            text='🎙️ ორმხრივი ხმოვანი რეჟიმი',
            font_name='font.ttf',
            font_size='18sp',
            size_hint=(1, 0.1),
        )
    )

    btn_mic1 = Button(
        text='🎤 საუბარი (ენა 1)',
        font_name='font.ttf',
        size_hint=(1, 0.2),
        background_color=(0.2, 0.7, 0.3, 1),
    )
    btn_mic2 = Button(
        text='🎤 საუბარი (ენა 2)',
        font_name='font.ttf',
        size_hint=(1, 0.2),
        background_color=(0.9, 0.5, 0.1, 1),
    )

    layout.add_widget(btn_mic1)
    layout.add_widget(btn_mic2)
    layout.add_widget(
        Label(
            text='დააჭირეთ ღილაკს და ილაპარაკეთ',
            font_name='font.ttf',
            size_hint=(1, 0.4),
        )
    )
    self.add_widget(layout)


# 5. კამერის ეკრანი
class CameraScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
    btn_back = Button(
        text='⬅️ უკან', font_name='font.ttf', size_hint=(0.3, 0.08)
    )
    btn_back.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'main_menu')
    )
    layout.add_widget(btn_back)

    layout.add_widget(
        Label(
            text='📷 კამერით სკანირება (OCR)',
            font_name='font.ttf',
            font_size='18sp',
            size_hint=(1, 0.1),
        )
    )

    btn_capture = Button(
        text='📸 ფოტოს გადაღება და თარგმნა',
        font_name='font.ttf',
        size_hint=(1, 0.2),
        background_color=(0.3, 0.6, 0.9, 1),
    )
    layout.add_widget(btn_capture)

    layout.add_widget(
        Label(
            text='მიმართეთ კამერა ტექსტზე',
            font_name='font.ttf',
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
