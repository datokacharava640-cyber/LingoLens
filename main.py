import sys
import traceback
import threading
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle
import requests

# იმპორტები პროექტის მოდულებიდან
from config import BACKEND_URL, FONT_PATH, API_SECRET_KEY
from languages import LANGUAGES_MAP

# სერვისების იმპორტი
try:
    from chat_service import ChatService
except ImportError:
    ChatService = None

try:
    from ocr_service import OCRService
except ImportError:
    OCRService = None

try:
    from android.permissions import request_permissions, Permission
except ImportError:
    pass


# ---------------------------------------------------------
# კრიტიკული შეცდომების დამჭერი (Crash Handler)
# ---------------------------------------------------------
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("CRASH DETECTED:\n", error_msg)
    
    try:
        class ErrorApp(App):
            def build(self):
                root = ScrollView()
                layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=15)
                layout.bind(minimum_height=layout.setter('height'))
                
                lbl_title = Label(text="აპლიკაცია დახურულია შეცდომის გამო:", color=(1, 0, 0, 1), font_size=16, size_hint_y=None, height=40)
                lbl_error = Label(text=error_msg, color=(1, 1, 1, 1), font_size=12, size_hint_y=None)
                lbl_error.bind(texture_size=lambda s, w: setattr(s, 'height', w[1]))
                
                layout.add_widget(lbl_title)
                layout.add_widget(lbl_error)
                root.add_widget(layout)
                return root
        ErrorApp().run()
    except Exception:
        pass

sys.excepthook = handle_exception
# ---------------------------------------------------------


class GeorgianFlagBackgroundMixin:
    """ქართული დროშის სტილის ფონი (თეთრი ფონი და წითელი აქცენტიანი ზოლი)"""
    def setup_georgian_bg(self, widget):
        with widget.canvas.before:
            Color(0.97, 0.97, 0.97, 1)
            self.bg_rect = Rectangle(size=widget.size, pos=widget.pos)
            
            Color(0.85, 0.1, 0.1, 1)
            self.top_stripe = Rectangle(size=(widget.width, 10), pos=(widget.x, widget.top - 10))
            
        widget.bind(size=self.update_georgian_bg, pos=self.update_georgian_bg)

    def update_georgian_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        self.top_stripe.pos = (instance.x, instance.top - 10)
        self.top_stripe.size = (instance.width, 10)


class MainMenuScreen(Screen, GeorgianFlagBackgroundMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_georgian_bg(self)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text="LingoLens AI - მთავარი მენიუ", 
            font_name=FONT_PATH,
            font_size=22,
            color=(0.8, 0.1, 0.1, 1),
            size_hint_y=None, 
            height=60
        )
        layout.add_widget(title)

        grid_menu = GridLayout(cols=2, spacing=12, size_hint=(1, 0.8))

        btn_trans = Button(text="მთარგმნელი", font_name=FONT_PATH, font_size=16)
        btn_trans.bind(on_press=lambda x: setattr(self.manager, 'current', 'translator'))
        grid_menu.add_widget(btn_trans)

        btn_chat = Button(text="დიალოგი", font_name=FONT_PATH, font_size=16)
        btn_chat.bind(on_press=lambda x: setattr(self.manager, 'current', 'dialogue'))
        grid_menu.add_widget(btn_chat)

        btn_sms = Button(text="SMS ხმოვანი", font_name=FONT_PATH, font_size=16)
        btn_sms.bind(on_press=lambda x: setattr(self.manager, 'current', 'sms_voice'))
        grid_menu.add_widget(btn_sms)

        btn_ocr = Button(text="Live კამერა / OCR", font_name=FONT_PATH, font_size=16)
        btn_ocr.bind(on_press=lambda x: setattr(self.manager, 'current', 'ocr'))
        grid_menu.add_widget(btn_ocr)

        btn_hist = Button(text="ისტორია", font_name=FONT_PATH, font_size=16)
        btn_hist.bind(on_press=lambda x: setattr(self.manager, 'current', 'history'))
        grid_menu.add_widget(btn_hist)

        btn_sett = Button(text="პარამეტრები", font_name=FONT_PATH, font_size=16)
        btn_sett.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        grid_menu.add_widget(btn_sett)

        layout.add_widget(grid_menu)
        self.add_widget(layout)


class TranslatorScreen(Screen, GeorgianFlagBackgroundMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_georgian_bg(self)
        
        root_scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        btn_back = Button(text="უკან", font_name=FONT_PATH, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        
        lang_layout = GridLayout(cols=3, size_hint_y=None, height=50, spacing=5)
        languages = tuple(LANGUAGES_MAP.keys()) if 'LANGUAGES_MAP' in globals() else ('Georgian', 'English')
        self.spinner_lang1 = Spinner(text='Georgian', values=languages, font_name=FONT_PATH)
        btn_swap = Button(text="<=>", font_name=FONT_PATH, size_hint_x=None, width=60)
        btn_swap.bind(on_press=self.swap_languages)
        self.spinner_lang2 = Spinner(text='English', values=languages, font_name=FONT_PATH)
        
        lang_layout.add_widget(self.spinner_lang1)
        lang_layout.add_widget(btn_swap)
        lang_layout.add_widget(self.spinner_lang2)
        layout.add_widget(lang_layout)

        self.input_box = TextInput(text="გამარჯობა, როგორ ხარ?", font_name=FONT_PATH, size_hint_y=None, height=100)
        layout.add_widget(self.input_box)
        
        btn_action = Button(text="თარგმნა", font_name=FONT_PATH, size_hint_y=None, height=45)
        btn_action.bind(on_press=self.do_translate)
        layout.add_widget(btn_action)

        self.res_box = TextInput(text="", font_name=FONT_PATH, readonly=True, size_hint_y=None, height=100)
        layout.add_widget(self.res_box)
        root_scroll.add_widget(layout)
        self.add_widget(root_scroll)

    def swap_languages(self, instance):
        t1 = self.spinner_lang1.text
        self.spinner_lang1.text = self.spinner_lang2.text
        self.spinner_lang2.text = t1

    def do_translate(self, instance):
        text = self.input_box.text.strip()
        if not text:
            return
        target = LANGUAGES_MAP.get(self.spinner_lang2.text, 'en') if 'LANGUAGES_MAP' in globals() else 'en'
        
        try:
            headers = {"X-API-Key": API_SECRET_KEY} if 'API_SECRET_KEY' in globals() else {}
            res = requests.post(
                f"{BACKEND_URL}/translate/", 
                json={"text": text, "target_lang": target}, 
                headers=headers, 
                timeout=3
            )
            if res.status_code == 200:
                self.res_box.text = res.json().get('translation', '')
            else:
                self.res_box.text = f"სერვერის შეცდომა: {res.status_code}"
        except requests.exceptions.ConnectionError:
            self.res_box.text = "სერვერი გამორთულია (Connection Error)."
        except requests.exceptions.Timeout:
            self.res_box.text = "სერვერმა პასუხი დააგვიანა (Timeout)."
        except Exception as e:
            self.res_box.text = f"შეცდომა: {str(e)}"


class DialogueScreen(Screen, GeorgianFlagBackgroundMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_georgian_bg(self)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        btn_back = Button(text="უკან", font_name=FONT_PATH, size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(btn_back)
        
        layout.add_widget(Label(text="AI დიალოგი", font_name=FONT_PATH, color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=30))
        
        self.chat_history = TextInput(text="", font_name=FONT_PATH, readonly=True, size_hint=(1, 0.6))
        layout.add_widget(self.chat_history)
