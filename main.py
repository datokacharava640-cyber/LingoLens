import os
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.textinput import TextInput

# ქართული შრიფტის რეგისტრაცია
LabelBase.register(
    name='Roboto',
    fn_regular='font.ttf',
    fn_bold='font.ttf',
    fn_italic='font.ttf',
    fn_bolditalic='font.ttf',
)


# 1. ანიმაციური ჩატვირთვის ეკრანი (Splash Screen)
class SplashScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    layout = BoxLayout(
        orientation='vertical', padding=20, spacing=20, background_color=(1, 1, 1, 1)
    )

    # GIF ანიმაცია (ჩააგდეთ flag_animation.gif პროექტის საქაღალდეში)
    if os.path.exists('flag_animation.gif'):
      self.anim_image = Image(source='flag_animation.gif', anim_loop=0)
      layout.add_widget(self.anim_image)
    else:
      layout.add_widget(
          Label(text='LingoLens Ultra Pro', font_size='28sp', font_name='font.ttf')
      )

    self.add_widget(layout)

  def on_enter(self):
    # 3 წამში ავტომატურად გადადის მთავარ მენიუზე
    Clock.schedule_once(self.switch_to_main, 3)

  def switch_to_main(self, dt):
    self.manager.transition = SlideTransition(direction='left')
    self.manager.current = 'main_menu'


# 2. მთავარი მენიუს ეკრანი
class MainMenuScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    main_layout = BoxLayout(orientation='vertical', padding=15, spacing=15)

    # სათაური
    header = Label(
        text='LingoLens - მთავარი მენიუ',
        font_size='22sp',
        font_name='font.ttf',
        size_hint=(1, 0.1),
    )
    main_layout.add_widget(header)

    # ფუნქციების ბადე (2 სვეტად)
    grid = GridLayout(cols=2, spacing=15, padding=10, size_hint=(1, 0.8))

    # მენიუს ღილაკები
    btn_translate = Button(
        text='📝 ტექსტის\nთარგმნა',
        font_name='font.ttf',
        halign='center',
        background_color=(0.2, 0.6, 1, 1),
    )
    btn_translate.bind(
        on_press=lambda x: setattr(self.manager, 'current', 'translator')
    )

    btn_camera = Button(
        text='📷 კამერით\nსკანირება',
        font_name='font.ttf',
        halign='center',
        background_color=(0.3, 0.8, 0.4, 1),
    )

    btn_history = Button(
        text='📜 ისტორია',
        font_name='font.ttf',
        halign='center',
        background_color=(0.9, 0.6, 0.2, 1),
    )

    btn_settings = Button(
        text='⚙️ პარამეტრები',
        font_name='font.ttf',
        halign='center',
        background_color=(0.6, 0.4, 0.8, 1),
    )

    grid.add_widget(btn_translate)
    grid.add_widget(btn_camera)
    grid.add_widget(btn_history)
    grid.add_widget(btn_settings)

    main_layout.add_widget(grid)
    self.add_widget(main_layout)


# 3. თარგმნის ეკრანი
class TranslatorScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.server_url = 'https://lingo-lens-eight.vercel.app'

    layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

    # უკან დაბრუნების ღილაკი
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

    # ტექსტის შესაყვანი
    self.input_text = TextInput(
        hint_text='შეიყვანეთ ტექსტი სათარგმნად...',
        font_name='font.ttf',
        multiline=True,
        size_hint=(1, 0.35),
    )
    layout.add_widget(self.input_text)

    # თარგმნის ღილაკი
    btn_action = Button(
        text='თარგმნა (Vercel API)',
        font_name='font.ttf',
        size_hint=(1, 0.12),
        background_color=(0.2, 0.6, 1, 1),
    )
    btn_action.bind(on_press=self.translate_text)
    layout.add_widget(btn_action)

    # შედეგის ველი
    self.result_label = Label(
        text='შედეგი გამოჩნდება აქ',
        font_name='font.ttf',
        halign='center',
        valign='middle',
        size_hint=(1, 0.35),
    )
    self.result_label.bind(size=self.result_label.setter('text_size'))
    layout.add_widget(self.result_label)

    self.add_widget(layout)

  def translate_text(self, instance):
    text_to_translate = self.input_text.text.strip()
    if not text_to_translate:
      self.result_label.text = 'გთხოვთ, შეიყვანოთ ტექსტი!'
      return

    self.result_label.text = 'მიმდინარეობს თარგმნა...'

    try:
      response = requests.post(
          f'{self.server_url}/api/index',
          json={'text': text_to_translate},
          timeout=10,
      )
      if response.status_code == 200:
        data = response.json()
        self.result_label.text = data.get(
            'translated_text', 'თარგმნა ვერ მოხერხდა'
        )
      else:
        self.result_label.text = f'სერვერის შეცდომა: {response.status_code}'
    except Exception as e:
      self.result_label.text = f'კავშირის შეცდომა: {str(e)}'


# აპლიკაციის კლასი
class LingoLensApp(App):

  def build(self):
    sm = ScreenManager()
    sm.add_widget(SplashScreen(name='splash'))
    sm.add_widget(MainMenuScreen(name='main_menu'))
    sm.add_widget(TranslatorScreen(name='translator'))
    return sm


if __name__ == '__main__':
  LingoLensApp().run()
