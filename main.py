from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
import requests

try:
    from android.permissions import request_permissions, Permission
except ImportError:
    pass

BACKEND_URL = "http://37.27.255.1:8000"
font_path = "font.ttf"

# 1. მთავარი მენიუს ეკრანი (6 ბლოკიანი Grid)
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        title = Label(
            text="LingoLens AI - მართვის პანელი", 
            font_name=font_path, 
            font_size=18,
            size_hint_y=None, 
            height=40
        )
        layout.add_widget(title)

        # 2x3 ბადის განლაგება
        grid_menu = GridLayout(cols=2, spacing=10, size_hint=(1, 0.8))

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
        grid_menu.add_widget(btn_hist>grid_menu.add_widget) # simplified next line

        btn_sett = Button(text="პარამეტრები", font_name=font_path, font_size=16)
        btn_sett.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        grid_menu.add_widget(btn_sett)

        layout.add_widget(grid_menu)
        self.add_widget(layout)

# 2. მთარგმნელის ეკრანი
class TranslatorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        layout.add_widget(Label(text="მთარგმნელის მოდული", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        
        self.input_box = TextInput(hint_text="ჩაწერეთ ტექსტი...", font_name=font_path, size_hint_y=None, height=50)
        layout.add_widget(self.input_box)
        
        btn_action = Button(text="თარგმნა", font_name=font_path, size_hint_y=None, height=45)
        btn_action.bind(on_press=self.do_translate)
        layout.add_widget(btn_action)

        self.res_label = Label(text="შედეგი გამოჩნდება აქ...", font_name=font_path, font_size=15)
        layout.add_widget(self.res_label)

        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        
        self.add_widget(layout)

    def do_translate(self, instance):
        text = self.input_box.text.strip()
        if not text:
            self.res_label.text = "გთხოვთ ჩაწეროთ ტექსტი!"
            return
        try:
            res = requests.post(f"{BACKEND_URL}/translate/", json={"text": text, "target_lang": "en"})
            if res.status_code == 200:
                data = res.json()
                self.res_label.text = f"თარგმანი: {data.get('translation', '')}"
            else:
                self.res_label.text = "სერვერის შეცდომა."
        except Exception as e:
            self.res_label.text = f"კავშირის შეცდომა: {e}"

# 3. დიალოგის ეკრანი
class DialogueScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        layout.add_widget(Label(text="AI ორმხრივი დიალოგი", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        
        self.chat_input = TextInput(hint_text="მიწერეთ ასისტენტს...", font_name=font_path, size_hint_y=None, height=50)
        layout.add_widget(self.chat_input)
        
        btn_send = Button(text="გაგზავნა", font_name=font_path, size_hint_y=None, height=45)
        btn_send.bind(on_press=self.send_chat)
        layout.add_widget(btn_send)

        self.chat_res = Label(text="დიალოგის ისტორია ცარიელია...", font_name=font_path, font_size=15)
        layout.add_widget(self.chat_res)

        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        
        self.add_widget(layout)

    def send_chat(self, instance):
        msg = self.chat_input.text.strip()
        if not msg:
            return
        try:
            res = requests.post(f"{BACKEND_URL}/chat/", json={"message": msg})
            if res.status_code == 200:
                self.chat_res.text = f"პასუხი: {res.json().get('response', '')}"
        except Exception as e:
            self.chat_res.text = f"შეცდომა: {e}"

# 4. გრამატიკის ეკრანი
class GrammarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="გრამატიკული შემოწმება", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        
        self.g_input = TextInput(hint_text="ჩაწერეთ ტექსტი გრამატიკისთვის...", font_name=font_path, size_hint_y=None, height=50)
        layout.add_widget(self.g_input)
        
        btn_g = Button(text="შემოწმება", font_name=font_path, size_hint_y=None, height=45)
        layout.add_widget(btn_g)
        
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

# 5. ლაივ კამერა / OCR ეკრანი
class OcrScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="ლაივ კამერა / OCR ამოცნობა", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        
        self.ocr_res = Label(text="კამერა მზადაა ტექსტის ამოსაცნობად...", font_name=font_path, font_size=15)
        layout.add_widget(self.ocr_res)
        
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

# 6. ისტორიის ეკრანი
class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="თარგმანებისა და ძიების ისტორია", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

# 7. პარამეტრების ეკრანი
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="აპლიკაციის პარამეტრები და OTA", font_name=font_path, font_size=18, size_hint_y=None, height=40))
        
        btn_back = Button(text="უკან", font_name=font_path, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self):
        try:
            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.SEND_SMS,
                Permission.READ_SMS,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        except Exception:
            pass

        # ეკრანების მენეჯერის აწყობა
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
