import os
import json
import urllib.parse
import urllib.request

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.text import LabelBase

# ფონტის აბსოლუტური მისამართის პოვნა
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'font.ttf')

FONT_NAME = None

if os.path.exists(FONT_PATH) and os.path.getsize(FONT_PATH) > 10000:
    try:
        LabelBase.register(name='GeorgianFont', fn_regular=FONT_PATH)
        FONT_NAME = 'GeorgianFont'
    except Exception as e:
        print(f"Font error: {e}")

def get_font_arg():
    return {'font_name': FONT_NAME} if FONT_NAME else {}

class LingoLensApp(App):
    def build(self):
        self.title = 'LingoLens'
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        title_label = Label(
            text='LingoLens\nზუსტი თარგმანი და გრამატიკის კონტროლი',
            font_size='20sp',
            size_hint_y=None,
            height=60,
            halign='center',
            **get_font_arg()
        )
        main_layout.add_widget(title_label)
        
        self.input_text = TextInput(
            hint_text='ჩაწერეთ ან ჩასვით ტექსტი ნებისმიერ ენაზე...',
            multiline=True,
            size_hint_y=0.35,
            font_size='16sp',
            **get_font_arg()
        )
        main_layout.add_widget(self.input_text)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        
        translate_btn = Button(
            text='თარგმნა (ქართულად)',
            background_color=(0.2, 0.6, 1, 1),
            font_size='15sp',
            **get_font_arg()
        )
        translate_btn.bind(on_press=self.translate_text)
        
        grammar_btn = Button(
            text='გრამატიკის შემოწმება',
            background_color=(0.2, 0.8, 0.4, 1),
            font_size='15sp',
            **get_font_arg()
        )
        grammar_btn.bind(on_press=self.check_grammar)
        
        btn_layout.add_widget(translate_btn)
        btn_layout.add_widget(grammar_btn)
        main_layout.add_widget(btn_layout)
        
        scroll = ScrollView(size_hint_y=0.45)
        self.result_label = Label(
            text='შედეგი გამოჩნდება აქ...',
            font_size='16sp',
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top',
            **get_font_arg()
        )
        self.result_label.bind(texture_size=self._update_label_size)
        scroll.add_widget(self.result_label)
        main_layout.add_widget(scroll)
        
        return main_layout

    def _update_label_size(self, instance, value):
        instance.height = value[1]
        instance.text_size = (instance.width, None)

    def translate_text(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "გთხოვთ, შეიყვანოთ ტექსტი!"
            return
        
        self.result_label.text = "მიმდინარეობს თარგმნა..."
        Clock.schedule_once(lambda dt: self._do_translate(text), 0.1)

    def _do_translate(self, text):
        try:
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={encoded_text}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = response.read().decode('utf-8')
                result_json = json.loads(res_data)
                translated_text = "".join([item[0] for item in result_json[0] if item[0]])
                self.result_label.text = f"თარგმანი:\n{translated_text}"
        except Exception as e:
            self.result_label.text = f"შეცდომა: {str(e)}"

    def check_grammar(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "გთხოვთ, შეიყვანოთ ტექსტი!"
            return
        
        self.result_label.text = "მიმდინარეობს გრამატიკის შემოწმება..."
        Clock.schedule_once(lambda dt: self._do_grammar_check(text), 0.1)

    def _do_grammar_check(self, text):
        try:
            url = "https://api.languagetool.org/v2/check"
            data = urllib.parse.urlencode({'text': text, 'language': 'auto'}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = response.read().decode('utf-8')
                res = json.loads(res_data)
                matches = res.get('matches', [])
                if not matches:
                    self.result_label.text = "✅ გრამატიკული შეცდომები ვერ მოიძებნა!"
                else:
                    report = f"ნაპოვნია {len(matches)} შეცდომა:\n\n"
                    for m in matches:
                        rule_desc = m.get('message', '')
                        replacements = [r['value'] for r in m.get('replacements', [])[:3]]
                        sug = ", ".join(replacements) if replacements else "შეთავაზება არ არის"
                        report += f"• {rule_desc}\n  შესწორება: {sug}\n\n"
                    self.result_label.text = report
        except Exception as e:
            self.result_label.text = f"შეცდომა: {str(e)}"

if __name__ == '__main__':
    LingoLensApp().run()
