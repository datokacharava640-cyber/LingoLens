import threading
import json
import os
import socket
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard

# ლოკალური იმპორტები
import config
from utils.translator import translate_text
from utils.tts_engine import speak_text 
from ui.window_manager import MovableWindow
from ui.dialogue_window import DialogueWidget
from ui.camera_widget import CameraWidget 

HISTORY_FILE = "translation_history.json"

class LingoLensDesktopApp(App):
    def build(self):
        self.request_android_permissions()
        self.root_layout = FloatLayout()

        # მთავარი მენიუ (3 სვეტი უკეთესი განლაგებისთვის)
        menu_grid = GridLayout(
            cols=2, 
            spacing=12, 
            padding=15, 
            size_hint=(0.9, 0.8), 
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        font = getattr(config, 'FONT_PATH', None)

        btn_translator = Button(text="თარგმანი\n(Translator)", font_name=font, on_press=self.open_translator)
        btn_dialogue = Button(text="დიალოგი\n(Live Dialogue)", font_name=font, on_press=self.open_dialogue)
        btn_grammar = Button(text="გრამატიკა\n(Grammar AI)", font_name=font, on_press=self.open_grammar)
        btn_camera = Button(text="კამერა / OCR", font_name=font, on_press=self.open_camera)
        btn_history = Button(text="ისტორია\n(History)", font_name=font, on_press=self.open_history)
        btn_settings = Button(text="პარამეტრები\n(Settings)", font_name=font, on_press=self.open_settings)

        menu_grid.add_widget(btn_translator)
        menu_grid.add_widget(btn_dialogue)
        menu_grid.add_widget(btn_grammar)
        menu_grid.add_widget(btn_camera)
        menu_grid.add_widget(btn_history)
        menu_grid.add_widget(btn_settings)

        self.root_layout.add_widget(menu_grid)
        return self.root_layout

    # 1. ინტერნეტის შემოწმება
    def has_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    # 2. ისტორიის შენახვის ფუნქცია
    def save_to_history(self, original, translated):
        history = self.load_history()
        history.append({"original": original, "translated": translated})
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("History save error:", e)

    # 3. ისტორიის წაკითხვის ფუნქცია
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def request_android_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA, 
                    Permission.INTERNET,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_MEDIA_IMAGES
                ])
            except Exception as e:
                print("Permissions error:", e)

    def copy_to_clipboard(self, text):
        if text.strip():
            Clipboard.copy(text)

    def share_text(self, text):
        if not text.strip():
            return
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')
                
                intent = Intent()
                intent.setAction(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, String(text))
                
                chooser = Intent.createChooser(intent, String("Share text via"))
                PythonActivity.mActivity.startActivity(chooser)
            except Exception as e:
                print("Share error:", e)
        else:
            Clipboard.copy(text)

    # თარგმანი (ისტორიის შენახვით)
    def open_translator(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        inp = TextInput(hint_text="ტექსტი...", font_name=font, multiline=True)
        out = TextInput(hint_text="თარგმანი...", font_name=font, readonly=True, multiline=True)
        status_lbl = Label(text="", size_hint_y=0.1, font_name=font)
        
        btn_trans = Button(text="თარგმნა", font_name=font, size_hint_y=0.2)
        
        action_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.2)
        btn_copy = Button(text="Copy", font_name=font, on_press=lambda x: self.copy_to_clipboard(out.text))
        btn_share = Button(text="Share", font_name=font, on_press=lambda x: self.share_text(out.text))
        btn_listen = Button(text="მოსმენა", font_name=font, on_press=lambda x: speak_text(out.text))
        
        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_listen)

        def run_trans_async():
            if not self.has_internet():
                Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', 'შეამოწმეთ ინტერნეტი!'))
                return

            text_to_translate = inp.text.strip()
            if text_to_translate:
                Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', 'მუშავდება...'))
                prompt = f"Translate from ka to en: {text_to_translate}"
                
                def on_res(res):
                    Clock.schedule_once(lambda dt: setattr(out, 'text', res))
                    Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', ''))
                    self.save_to_history(text_to_translate, res)

                translate_text(prompt, text_to_translate, "ka", "en", on_res)

        def on_click_trans(btn_inst):
            threading.Thread(target=run_trans_async, daemon=True).start()

        btn_trans.bind(on_press=on_click_trans)

        box.add_widget(inp)
        box.add_widget(btn_trans)
        box.add_widget(status_lbl)
        box.add_widget(out)
        box.add_widget(action_box)

        win = MovableWindow(title="LingoLens თარგმანი", content_widget=box, pos=(20, 80))
        win.size = (340, 480)
        self.root_layout.add_widget(win)

    # დიალოგი
    def open_dialogue(self, instance):
        dialogue_content = DialogueWidget()
        win = MovableWindow(title="LingoLens დიალოგი", content_widget=dialogue_content, pos=(30, 60))
        win.size = (340, 520)
        self.root_layout.add_widget(win)

    # გრამატიკა
    def open_grammar(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        inp = TextInput(hint_text="შესამოწმებელი ტექსტი...", font_name=font)
        out = TextInput(hint_text="შედეგი...", font_name=font, readonly=True)
        status_lbl = Label(text="", size_hint_y=0.1, font_name=font)
        btn_check = Button(text="შემოწმება", font_name=font, size_hint_y=0.2)

        action_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.2)
        btn_copy = Button(text="Copy", font_name=font, on_press=lambda x: self.copy_to_clipboard(out.text))
        btn_share = Button(text="Share", font_name=font, on_press=lambda x: self.share_text(out.text))
        btn_listen = Button(text="მოსმენა", font_name=font, on_press=lambda x: speak_text(out.text))
        
        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_listen)

        def run_grammar_async():
            if not self.has_internet():
                Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', 'შეამოწმეთ ინტერნეტი!'))
                return

            text_to_check = inp.text.strip()
            if text_to_check:
                Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', 'მოწმდება...'))
                prompt = f"Correct grammar: {text_to_check}"
                
                def on_res(res):
                    Clock.schedule_once(lambda dt: setattr(out, 'text', res))
                    Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', ''))

                translate_text(prompt, text_to_check, "ka", "en", on_res)

        def on_click_check(btn_inst):
            threading.Thread(target=run_grammar_async, daemon=True).start()

        btn_check.bind(on_press=on_click_check)

        box.add_widget(inp)
        box.add_widget(btn_check)
        box.add_widget(status_lbl)
        box.add_widget(out)
        box.add_widget(action_box)

        win = MovableWindow(title="გრამატიკის შემოწმება", content_widget=box, pos=(40, 100))
        win.size = (340, 480)
        self.root_layout.add_widget(win)

    # კამერა / OCR
    def open_camera(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        try:
            box = BoxLayout(orientation='vertical', padding=5, spacing=5)
            cam_content = CameraWidget()
            
            btn_gallery = Button(text="გალერეიდან არჩევა", font_name=font, size_hint_y=0.15)
            
            def open_gallery(btn_inst):
                if platform == 'android':
                    try:
                        from plyer import filechooser
                        filechooser.open_file(on_selection=self.on_gallery_select)
                    except Exception as e:
                        print("Gallery error:", e)

            btn_gallery.bind(on_press=open_gallery)

            box.add_widget(cam_content)
            box.add_widget(btn_gallery)

            win = MovableWindow(title="კამერა / OCR", content_widget=box, pos=(30, 50))
            win.size = (340, 500)
            self.root_layout.add_widget(win)
        except Exception as e:
            print("Camera error:", e)

    def on_gallery_select(self, selection):
        if selection and len(selection) > 0:
            image_path = selection[0]
            print("Selected gallery image:", image_path)

    # 4. ისტორიის ფანჯარა
    def open_history(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        scroll = ScrollView(size_hint=(1, 0.85))
        hist_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        hist_layout.bind(minimum_height=hist_layout.setter('height'))

        history_data = self.load_history()

        if not history_data:
            hist_layout.add_widget(Label(text="ისტორია ცარიელია", font_name=font, size_hint_y=None, height=40))
        else:
            for item in reversed(history_data):
                txt = f"• {item.get('original', '')} ➔ {item.get('translated', '')}"
                lbl = Label(text=txt, font_name=font, size_hint_y=None, height=40, text_size=(300, None))
                hist_layout.add_widget(lbl)

        scroll.add_widget(hist_layout)

        btn_clear = Button(text="ისტორიის გასუფთავება", font_name=font, size_hint_y=0.15)
        
        def clear_hist(btn_inst):
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            hist_layout.clear_widgets()
            hist_layout.add_widget(Label(text="ისტორია ცარიელია", font_name=font, size_hint_y=None, height=40))

        btn_clear.bind(on_press=clear_hist)

        box.add_widget(scroll)
        box.add_widget(btn_clear)

        win = MovableWindow(title="თარგმანების ისტორია", content_widget=box, pos=(30, 70))
        win.size = (340, 480)
        self.root_layout.add_widget(win)

    # პარამეტრები
    def open_settings(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        lbl = Label(text="API Key კონფიგურაცია:", font_name=font, size_hint_y=0.2)
        inp_key = TextInput(hint_text="შეიყვანეთ API Key...", font_name=font, multiline=False)
        btn_save = Button(text="შენახვა", font_name=font, size_hint_y=0.25)
        status_lbl = Label(text="", font_name=font, size_hint_y=0.2)

        def save_key(btn_inst):
            key = inp_key.text.strip()
            if key:
                os.environ['API_KEY'] = key
                status_lbl.text = "შენახულია!"

        btn_save.bind(on_press=save_key)

        box.add_widget(lbl)
        box.add_widget(inp_key)
        box.add_widget(btn_save)
        box.add_widget(status_lbl)

        win = MovableWindow(title="პარამეტრები", content_widget=box, pos=(50, 120))
        win.size = (320, 300)
        self.root_layout.add_widget(win)


if __name__ == "__main__":
    LingoLensDesktopApp().run()
