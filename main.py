from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.core.clipboard import Clipboard
import requests

try:
    from android.permissions import request_permissions, Permission
except ImportError:
    pass

BACKEND_URL = "http://127.0.0.1:8000"
font_path = "font.ttf"

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text="LingoLens AI - მთავარი მენიუ", 
            font_name=font_path,
            font_size=20,
            size_hint_y=None, 
            height=50
        )
        layout.add_widget(title)

        grid_menu = GridLayout(cols=2, spacing=12, size_hint=(1, 0.8))

        btn_trans = Button(text="მთარგმნელი", font_name=font_path, font_size=16)
        btn_trans.bind(on_press=lambda x: setattr(self.manager, 'current', 'translator'))
        grid_menu.add_widget(btn_trans)

        btn_chat = Button(text="დიალოგი", font_name=font_path, font_size=16)
        btn_chat.bind(on_press=lambda x: setattr(self.manager, 'current', 'dialogue'))
        grid_menu.add_widget(btn_chat)

        btn_gram = Button(text="გრამატიკა", font_name=font_path, font_size=16)
        btn_gram.bind(on_press=lambda x: setattr(self.manager, 'current', 'grammar'))
        grid_menu.add_widget(btn_gram)

        btn_ocr = Button(text="ლაივ კამერა / OCR", font_name=font_path, font_size=16)
        btn_ocr.bind(on_press=lambda x: setattr(self.manager, 'current', 'ocr'))
        grid_menu.add_widget(btn_ocr)

        btn_hist = Button(text="ისტორია", font_name=font_path, font_size=16)
        btn_hist.bind(on_press=lambda x: setattr(self.manager, 'current', 'history'))
        grid_menu.add_widget(btn_hist)

        btn_sett = Button(text="პარამეტრები", font_name=font_path, font_size=16)
        btn_sett.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        grid_menu.add_widget(btn_sett)

        layout.add_widget(grid_menu)
        self.add_widget(layout)

class TranslatorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        root_scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        
        # ენების არჩევის ჩამონათვალი (Spinner)
        lang_layout = GridLayout(cols=3, size_hint_y=None, height=50, spacing=5)
        
        languages = ('Georgian', 'English', 'Russian', 'German', 'French', 'Spanish')
        
        self.spinner_lang1 = Spinner(
            text='Georgian',
            values=languages,
            font_name=font_path
        )
        
        btn_swap = Button(text="<=>", font_name=font_path, size_hint_x=None, width=60)
        btn_swap.bind(on_press=self.swap_languages)
        
        self.spinner_lang2 = Spinner(
            text='English',
            values=languages,
            font_name=font_path
        )
        
        lang_layout.add_widget(self.spinner_lang1)
        lang_layout.add_widget(btn_swap)
        lang_layout.add_widget(self.spinner_lang2)
        layout.add_widget(lang_layout)

        self.input_box = TextInput(
            text="გამარჯობა როგორ ხარ", 
            font_name=font_path, 
            size_hint_y=None, 
            height=100
        )
        layout.add_widget(self.input_box)
        
        btn_action = Button(text="თარგმნა", font_name=font_path, size_hint_y=None, height=45)
        btn_action.bind(on_press=self.do_translate)
        layout.add_widget(btn_action)

        self.res_box = TextInput(
            text="", 
            font_name=font_path, 
            readonly=True, 
            size_hint_y=None, 
            height=100
        )
        layout.add_widget(self.res_box)

        # მართვის ღილაკები (კოპირება, ჩასმა, გაზიარება, ხმოვანი)
        bottom_layout = GridLayout(cols=4, size_hint_y=None, height=50, spacing=5)
        
        btn_copy = Button(text="კოპირება", font_name=font_path)
        btn_copy.bind(on_press=self.copy_text)
        
        btn_paste = Button(text="ჩასმა", font_name=font_path)
        btn_paste.bind(on_press=self.paste_text)
        
        btn_share = Button(text="გაზიარება", font_name=font_path)
        btn_share.bind(on_press=self.share_text)
        
        btn_voice = Button(text="ხმოვანი", font_name=font_path)
        btn_voice.bind(on_press=self.voice_text)
        
        bottom_layout.add_widget(btn_copy)
        bottom_layout.add_widget(btn_paste)
        bottom_layout.add_widget(btn_share)
        bottom_layout.add_widget(btn_voice)
        layout.add_widget(bottom_layout)
        
        root_scroll.add_widget(layout)
        self.add_widget(root_scroll)

    def swap_languages(self, instance):
        t1 = self.spinner_lang1.text
        self.spinner_lang1.text = self.spinner_lang2.text
        self.spinner_lang2.text = t1

    def do_translate(self, instance):
        text = self.input_box.text.strip()
        if not text:
            self.res_box.text = "გთხოვთ ჩაწეროთ ტექსტი!"
            return
        
        lang_map = {
            'Georgian': 'ka',
            'English': 'en',
            'Russian': 'ru',
            'German': 'de',
            'French': 'fr',
            'Spanish': 'es'
        }
        target = lang_map.get(self.spinner_lang2.text, 'en')
        
        try:
            res = requests.post(f"{BACKEND_URL}/translate/", json={"text": text, "target_lang": target}, timeout=3)
            if res.status_code == 200:
                data = res.json()
                self.res_box.text = data.get('translation', '')
            else:
                self.res_box.text = "სერვერის შეცდომა."
        except Exception as e:
            self.res_box.text = "ვერ მოხერხდა სერვერთან დაკავშირება!"

    def copy_text(self, instance):
        text_to_copy = self.res_box.text.strip()
        if text_to_copy:
            Clipboard.copy(text_to_copy)

    def paste_text(self, instance):
        pasted_text = Clipboard.paste()
        if pasted_text:
            self.input_box.text = pasted_text

    def share_text(self, instance):
        text_to_share = self.res_box.text.strip()
        if text_to_share:
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, text_to_share)
                current_activity = PythonActivity.mActivity
                current_activity.startActivity(Intent.createChooser(intent, "გაზიარება"))
            except Exception:
                pass

    def voice_text(self, instance):
        pass

class DialogueScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="დიალოგის რეჟიმი", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

class GrammarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="გრამატიკის შემოწმება", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

class OcrScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="ლაივ კამერა / OCR", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="ისტორია", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="პარამეტრები", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main'))
        sm.add_widget(TranslatorScreen(name='translator'))
        sm.add_widget(DialogueScreen(name='dialogue'))
        sm.add_widget(GrammarScreen(name='grammar'))
        sm.add_widget(OcrScreen(name='ocr'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()
