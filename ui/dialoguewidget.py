from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import config
from utils.translator import translate_text

# ვცდილობთ ჩავტვირთოთ მიკროფონის (Speech-to-Text) მხარდაჭერა plyer-იდან
try:
  from plyer import stt
except ImportError:
  stt = None


class DialogueWidget(BoxLayout):

  def __init__(self, **kwargs):
    super().__init__(orientation="vertical", spacing=8, padding=10, **kwargs)
    font = getattr(config, "FONT_PATH", None)

    # 1. ზედა ნაწილი: პირველი ადამიანი (მაგ. ინგლისური)
    top_box = BoxLayout(orientation="vertical", spacing=4)
    top_box.add_widget(
        Label(
            text="👤 Person A (English)",
            font_name=font,
            size_hint_y=None,
            height=30,
        )
    )

    self.input_a = TextInput(
        hint_text="Type here / Speak...",
        font_name=font,
        multiline=True,
        size_hint_y=0.4,
    )
    self.output_a = TextInput(
        hint_text="Translation (English)...",
        font_name=font,
        readonly=True,
        multiline=True,
        size_hint_y=0.4,
    )

    top_box.add_widget(self.input_a)
    top_box.add_widget(self.output_a)

    # A ადამიანის მიკროფონის ღილაკი
    btn_mic_a = Button(
        text="🎤 Speak (EN)", font_name=font, size_hint_y=None, height=45
    )
    btn_mic_a.bind(on_press=self.record_audio_a)

    # 2. შუა ღილაკები: თარგმანი A -> B
    btn_translate_a = Button(
        text="Translate to Georgian ↓", font_name=font, size_hint_y=None, height=45
    )
    btn_translate_a.bind(on_press=self.translate_a_to_b)

    # 3. ქვედა ნაწილი: მეორე ადამიანი (მაგ. ქართული)
    bottom_box = BoxLayout(orientation="vertical", spacing=4)
    bottom_box.add_widget(
        Label(
            text="👤 Person B (ქართული)",
            font_name=font,
            size_hint_y=None,
            height=30,
        )
    )

    self.input_b = TextInput(
        hint_text="ჩაწერეთ აქ ან ისაუბრეთ...",
        font_name=font,
        multiline=True,
        size_hint_y=0.4,
    )
    self.output_b = TextInput(
        hint_text="თარგმანი (ქართული)...",
        font_name=font,
        readonly=True,
        multiline=True,
        size_hint_y=0.4,
    )

    bottom_box.add_widget(self.input_b)
    bottom_box.add_widget(self.output_b)

    # B ადამიანის მიკროფონის ღილაკი
    btn_mic_b = Button(
        text="🎤 საუბარი (ქართულად)",
        font_name=font,
        size_hint_y=None,
        height=45,
    )
    btn_mic_b.bind(on_press=self.record_audio_b)

    # 4. შუა ღილაკი: თარგმანი B -> A
    btn_translate_b = Button(
        text="Translate to English ↑", font_name=font, size_hint_y=None, height=45
    )
    btn_translate_b.bind(on_press=self.translate_b_to_a)

    # ვიჯეტების დამატება მთავარ ლეიაუთში თანმიმდევრობით
    self.add_widget(top_box)
    self.add_widget(btn_mic_a)
    self.add_widget(btn_translate_a)
    self.add_widget(bottom_box)
    self.add_widget(btn_mic_b)
    self.add_widget(btn_translate_b)

  def translate_a_to_b(self, instance):
    val = self.input_a.text.strip()
    if val:
      prompt = f"Translate accurately from English to Georgian: {val}"
      translate_text(
          prompt,
          val,
          "en",
          "ka",
          lambda res: Clock.schedule_once(
              lambda dt: setattr(self.output_b, "text", res)
          ),
      )

  def translate_b_to_a(self, instance):
    val = self.input_b.text.strip()
    if val:
      prompt = f"Translate accurately from Georgian to English: {val}"
      translate_text(
          prompt,
          val,
          "ka",
          "en",
          lambda res: Clock.schedule_once(
              lambda dt: setattr(self.output_a, "text", res)
          ),
      )

  def record_audio_a(self, instance):
    """Person A-ს ხმოვანი შეყვანა (ინგლისური)"""
    if stt:
      try:
        stt.start(
            language="en_US",
            callback=lambda text: Clock.schedule_once(
                lambda dt: setattr(self.input_a, "text", text)
            ),
        )
      except Exception as e:
        self.input_a.text = f"მიკროფონის შეცდომა: {e}"
    else:
      self.input_a.text = "Speech-to-Text მხარდაჭერილია მხოლოდ ანდროიდზე."

  def record_audio_b(self, instance):
    """Person B-ს ხმოვანი შეყვანა (ქართული)"""
    if stt:
      try:
        stt.start(
            language="ka_GE",
            callback=lambda text: Clock.schedule_once(
                lambda dt: setattr(self.input_b, "text", text)
            ),
        )
      except Exception as e:
        self.input_b.text = f"მიკროფონის შეცდომა: {e}"
    else:
      self.input_b.text = "მიკროფონი ხელმისაწვდომია მობილურ აპლიკაციაში."
