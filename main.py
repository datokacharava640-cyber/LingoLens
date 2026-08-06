import os
import json
import threading
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
from kivy.resources import resource_add_path, resource_find

# Android-ის დირექტორიის დამატება Kivy-ს რესურსებში
APP_DIR = os.path.dirname(os.path.abspath(__file__))
resource_add_path(APP_DIR)
resource_add_path(os.getcwd())

# შრიფტის მოძებნა და გლობალურად დარეგისტრირება Roboto-ს ნაცვლად
font_path = resource_find('font.ttf') or (os.path.join(APP_DIR, 'font.ttf') if os.path.exists(os.path.join(APP_DIR, 'font.ttf')) else None)

if font_path:
    try:
        LabelBase.register(name='Roboto', fn_regular=font_path)
    except Exception as e:
        print(f"Font registration error: {e}")

class LingoLensApp(App):
    def build(self):
        self.title = 'LingoLens'
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        title_text = 'LingoLens\nზუსტი თარგმანი და გრამატიკა'
        if not font_path:
            title_text += '\n(Font file not found!)'

        title_label = Label(
            text=title_text,
            font_size='20sp',
            size_hint_y=None,
            height=70,
            halign='center'
        )
        main_layout.add_widget(title_label)
        
        self.input_text = TextInput(
            hint_text='ჩაწერეთ ან ჩასვით ტექსტი...',
            multiline=True,
            size_hint_y=0.35,
            font_size='16sp'
        )
        main_layout.add_widget(self.input_text)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        
        translate_btn = Button(
            text='თარგმნა (ქართულად)',
            background_color=(0.2, 0.6, 1, 1),
            font_size='15sp'
        )
        translate_btn.bind(on_press=self.start_translation)
        
        grammar_btn = Button(
            text='გრამატიკის შემოწმება',
            background_color=(0.2, 0.8, 0.4, 1),
            font_size='15sp'
        )
        grammar_btn.bind(on_press=self.start_grammar_check)
        
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
            valign='top'
        )
        self.result_label.bind(texture_size=self._update_label_size)
        scroll.add_widget(self.result_label)
        main_layout.add_widget(scroll)
        
        return main_layout

    def _update_label_size(self, instance, value):
        instance.height = max(value[1], 150)
        instance.text_size = (instance.width, None)

    def set_result(self, text):
        Clock.schedule_once(lambda dt: setattr(self.result_label, 'text', text))

    def start_translation(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "გთხოვთ, შეიყვანოთ ტექსტი!"
            return
        self.result_label.text = "მიმდინარეობს თარგმნა..."
        threading.Thread(target=self._do_translate, args=(text,), daemon=True).start()

    def _do_translate(self, text):
        try:
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={encoded_text}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = response.read().decode('utf-8')
                result_json = json.loads(res_data)
                translated_text = "".join([item[0] for item in result_json[0] if item[0]])
                self.set_result(f"თარგმანი:\n{translated_text}")
        except Exception as e:
            self.set_result(f"შეცდომა თარგმნისას: {str(e)}")

    def start_grammar_check(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "გთხოვთ, შეიყვანოთ ტექსტი!"
            return
        self.result_label.text = "მიმდინარეობს გრამატიკის შემოწმება..."
        threading.Thread(target=self._do_grammar_check, args=(text,), daemon=True).start()

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
                    self.set_result("✅ გრამატიკული შეცდომები ვერ მოიძებნა!")
                else:
                    report = f"ნაპოვნია {len(matches)} შეცდომა:\n\n"
                    for m in matches:
                        rule_desc = m.get('message', '')
                        replacements = [r['value'] for r in m.get('replacements', [])[:3]]
                        sug = ", ".join(replacements) if replacements else "შეთავაზება არ არის"
                        report += f"• {rule_desc}\n  შესწორება: {sug}\n\n"
                    self.set_result(report)
        except Exception as e:
            self.set_result(f"შეცდომა შემოწმებისას: {str(e)}")

if __name__ == '__main__':
    LingoLensApp().run()
