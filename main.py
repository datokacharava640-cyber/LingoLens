# ==============================================================================
# LingoLens AI
# Copyright (c) 2026 Dato Kacharava. All rights reserved.
#
# This software is licensed under the MIT License.
# See the LICENSE file in the root directory for full license information.
# ==============================================================================

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
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard

import config
from utils.translator import translate_text, analyze_image_and_translate
from utils.tts_engine import speak_text
from ui.window_manager import MovableWindow
from ui.dialogue_window import DialogueWidget
from ui.camera_widget import CameraWidget

HISTORY_FILE = "translation_history.json"
SETTINGS_FILE = "settings.json"

class LingoLensDesktopApp(App):
    def build(self):
        # ავტომატური ნებართვები ამოღებულია ჩართვისას გაყინვის თავიდან ასაცილებლად
        self.root_layout = FloatLayout()

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
        # შეცვლილია ღილაკი, რომ ჯერ ნებართვა შეამოწმოს და ისე გახსნას
        btn_camera = Button(text="კამერა / OCR", font_name=font, on_press=self.open_camera_with_check)
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

    def has_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def save_to_history(self, original, translated):
        history = self.load_history()
        history.append({"original": original, "translated": translated})
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("History save error:", e)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    # ნებართვების მოთხოვნა საჭიროებისამებრ (On-Demand)
    def request_camera_permission_on_demand(self, callback_func):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                
                perms = [
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.INTERNET,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ]
                
                if hasattr(Permission, 'READ_MEDIA_IMAGES'):
                    perms.append(Permission.READ_MEDIA_IMAGES)
                if hasattr(Permission, 'READ_MEDIA_AUDIO'):
                    perms.append(Permission.READ_MEDIA_AUDIO)

                def callback(permissions, grant_results):
                    # უზრუნველყოფს ფანჯრის გახსნას ნებართვის სტატუსის მიუხედავად
                    callback_func()

                request_permissions(perms, callback)
            except Exception as e:
                print("Permissions error:", e)
                callback_func()
        else:
            callback_func()

    def copy_to_clipboard(self, text):
        if text and text.strip():
            Clipboard.copy(text)

    def share_text(self, text):
        if not text or not text.strip():
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

    def safe_speak(self, text):
        if text and text.strip():
            speak_text(text)

    # 1. თარგმანი (ონლაინ AI + ოფლაინ ძრავი)
    def open_translator(self, instance=None, initial_text="", initial_result="", status_text=""):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        lang_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.15)
        
        if hasattr(config, 'LANGUAGES') and getattr(config, 'LANGUAGES'):
            lang_map = config.LANGUAGES
        else:
            lang_map = {
                "ქართული": "ka", "English": "en", "Русский": "ru", "Español": "es", 
                "Deutsch": "de", "Français": "fr", "Italiano": "it", "Türkçe": "tr", 
                "中文": "zh", "العربية": "ar", "Ukranian": "uk", "Polski": "pl"
            }
        
        sp_src = Spinner(text="ქართული", values=list(lang_map.keys()), font_name=font)
        sp_target = Spinner(text="English", values=list(lang_map.keys()), font_name=font)
        
        lang_box.add_widget(sp_src)
        lang_box.add_widget(Label(text="➔", size_hint_x=0.2, font_name=font))
        lang_box.add_widget(sp_target)

        inp = TextInput(text=initial_text, hint_text="ტექსტი...", font_name=font, multiline=True)
        out = TextInput(text=initial_result, hint_text="თარგმანი...", font_name=font, readonly=True, multiline=True)
        status_lbl = Label(text=status_text, size_hint_y=0.1, font_name=font)
        
        btn_trans = Button(text="თარგმნა", font_name=font, size_hint_y=0.15)
        
        action_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.15)
        btn_copy = Button(text="Copy", font_name=font, on_press=lambda x: self.copy_to_clipboard(out.text))
        btn_share = Button(text="Share", font_name=font, on_press=lambda x: self.share_text(out.text))
        btn_listen = Button(text="მოსმენა", font_name=font, on_press=lambda x: self.safe_speak(out.text))
        
        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_listen)

        def handle_translation(btn_inst):
            text_to_translate = inp.text.strip()
            if not text_to_translate:
                return

            src_code = lang_map.get(sp_src.text, "ka")
            target_code = lang_map.get(sp_target.text, "en")

            if self.has_internet():
                status_lbl.text = 'მუშავდება (Online AI)...'
                prompt = f"Translate accurately from {sp_src.text} to {sp_target.text}: {text_to_translate}"
                
                def on_res(res):
                    res_text = str(res) if res else "შეცდომა თარგმნისას"
                    Clock.schedule_once(lambda dt: setattr(out, 'text', res_text))
                    Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', ''))
                    if res:
                        self.save_to_history(text_to_translate, res_text)

                translate_text(prompt, text_to_translate, src_code, target_code, on_res)
            else:
                status_lbl.text = 'ოფლაინ რეჟიმი...'
                try:
                    from offline_engine import translate_offline
                    offline_res = translate_offline(text_to_translate, src_code, target_code)
                    out.text = offline_res
                    status_lbl.text = 'თარგმნილია ოფლაინში'
                    self.save_to_history(text_to_translate, offline_res)
                except Exception as e:
                    status_lbl.text = 'ოფლაინ ძრავი მიუწვდომელია'
                    print("Offline translation error:", e)

        btn_trans.bind(on_press=handle_translation)

        box.add_widget(lang_box)
        box.add_widget(inp)
        box.add_widget(btn_trans)
        box.add_widget(status_lbl)
        box.add_widget(out)
        box.add_widget(action_box)

        win = MovableWindow(title="LingoLens თარგმანი", content_widget=box, pos=(20, 80))
        win.size = (340, 500)
        self.root_layout.add_widget(win)
        return inp, out, status_lbl

    def open_dialogue(self, instance):
        try:
            dialogue_content = DialogueWidget()
            win = MovableWindow(title="LingoLens დიალოგი", content_widget=dialogue_content, pos=(30, 60))
            win.size = (340, 520)
            self.root_layout.add_widget(win)
        except Exception as e:
            print("Dialogue Window Error:", e)

    # 2. გრამატიკის შემოწმება (ონლაინ + ოფლაინ)
    def open_grammar(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        inp = TextInput(hint_text="შესამოწმებელი ტექსტი...", font_name=font)
        out = TextInput(hint_text="შედეგი...", font_name=font, readonly=True)
        status_lbl = Label(text="", size_hint_y=0.1, font_name=font)
        btn_check = Button(text="შემოწმება", font_name=font, size_hint_y=0.15)

        action_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.15)
        btn_copy = Button(text="Copy", font_name=font, on_press=lambda x: self.copy_to_clipboard(out.text))
        btn_share = Button(text="Share", font_name=font, on_press=lambda x: self.share_text(out.text))
        btn_listen = Button(text="მოსმენა", font_name=font, on_press=lambda x: self.safe_speak(out.text))
        
        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_listen)

        def handle_grammar(btn_inst):
            text_to_check = inp.text.strip()
            if not text_to_check:
                return

            if self.has_internet():
                status_lbl.text = 'მოწმდება (Online AI)...'
                prompt = f"Correct the grammar and improve the clarity of the following text: {text_to_check}"
                
                def on_res(res):
                    res_text = str(res) if res else "შეცდომა"
                    Clock.schedule_once(lambda dt: setattr(out, 'text', res_text))
                    Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', ''))

                translate_text(prompt, text_to_check, "ka", "en", on_res)
            else:
                status_lbl.text = 'ოფლაინ შემოწმება...'
                try:
                    from offline_engine import check_grammar_offline
                    res_offline = check_grammar_offline(text_to_check)
                    out.text = res_offline
                    status_lbl.text = 'შემოწმებულია ოფლაინში'
                except Exception as e:
                    status_lbl.text = 'ოფლაინ გრამატიკა მიუწვდომელია'
                    print("Offline grammar error:", e)

        btn_check.bind(on_press=handle_grammar)

        box.add_widget(inp)
        box.add_widget(btn_check)
        box.add_widget(status_lbl)
        box.add_widget(out)
        box.add_widget(action_box)

        win = MovableWindow(title="გრამატიკის შემოწმება", content_widget=box, pos=(40, 100))
        win.size = (340, 480)
        self.root_layout.add_widget(win)

    # კამერის გახსნის დამხმარე მეთოდი ნებართვის შესამოწმებლად
    def open_camera_with_check(self, instance):
        self.request_camera_permission_on_demand(lambda: self.open_camera(instance))

    # 3. კამერა / OCR (Android Native Intent)
    def open_camera(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        try:
            box = BoxLayout(orientation='vertical', padding=5, spacing=5)
            cam_content = CameraWidget()
            
            btn_gallery = Button(text="გალერეიდან არჩევა (OCR)", font_name=font, size_hint_y=0.15)
            
            def open_gallery(btn_inst):
                if platform == 'android':
                    try:
                        from jnius import autoclass, activity
                        Intent = autoclass('android.content.Intent')
                        PythonActivity = autoclass('org.kivy.android.PythonActivity')
                        
                        intent = Intent(Intent.ACTION_PICK)
                        intent.setType("image/*")
                        
                        def on_activity_result(request_code, result_code, intent_data):
                            if request_code == 1001 and result_code == -1 and intent_data:
                                uri = intent_data.getData()
                                if uri:
                                    activity_obj = PythonActivity.mActivity
                                    cursor = activity_obj.getContentResolver().query(uri, None, None, None, None)
                                    if cursor:
                                        cursor.moveToFirst()
                                        idx = cursor.getColumnIndex("_data")
                                        if idx != -1:
                                            image_path = cursor.getString(idx)
                                            cursor.close()
                                            Clock.schedule_once(lambda dt: self.on_gallery_select([image_path]))
                                            return
                                        cursor.close()
                                    Clock.schedule_once(lambda dt: self.on_gallery_select([uri.toString()]))

                        activity.bind(on_activity_result=on_activity_result)
                        PythonActivity.mActivity.startActivityForResult(intent, 1001)
                    except Exception as e:
                        print("Native Gallery error:", e)
                        try:
                            from plyer import filechooser
                            filechooser.open_file(on_selection=self.on_gallery_select)
                        except Exception as ex:
                            print("Plyer error:", ex)
                else:
                    try:
                        from plyer import filechooser
                        filechooser.open_file(on_selection=self.on_gallery_select)
                    except Exception as e:
                        print("Desktop filechooser error:", e)

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
            
            inp, out, status_lbl = self.open_translator(
                initial_text="[სურათი ატვირთულია]", 
                status_text="სურათი მუშავდება (OCR)..."
            )

            def on_ocr_complete(res):
                res_text = str(res) if res else "ტექსტი ვერ ამოიცნო"
                Clock.schedule_once(lambda dt: setattr(out, 'text', res_text))
                Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', ''))

            analyze_image_and_translate(image_path, "ka", on_ocr_complete)

    # 4. ისტორია
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

    # 5. პარამეტრები
    def open_settings(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        lbl = Label(text="Gemini API Key:", font_name=font, size_hint_y=0.15)
        
        current_key = ""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    current_key = json.load(f).get("api_key", "")
            except Exception:
                pass

        inp_key = TextInput(text=current_key, hint_text="შეიყვანეთ API Key...", font_name=font, multiline=False)
        btn_save = Button(text="შენახვა", font_name=font, size_hint_y=0.2)
        status_lbl = Label(text="", font_name=font, size_hint_y=0.15)

        copyright_lbl = Label(
            text="LingoLens AI v6.0.1\n© 2026 Dato Kacharava\nყველა უფლება დაცულია.",
            font_name=font,
            size_hint_y=0.2,
            halign="center"
        )

        def save_key(btn_inst):
            key = inp_key.text.strip()
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump({"api_key": key}, f)
                config.GEMINI_API_KEY = key
                status_lbl.text = "წარმატებით შენახდა!"
            except Exception as e:
                status_lbl.text = "შეცდომა შენახვისას"

        btn_save.bind(on_press=save_key)

        box.add_widget(lbl)
        box.add_widget(inp_key)
        box.add_widget(btn_save)
        box.add_widget(status_lbl)
        box.add_widget(copyright_lbl)

        win = MovableWindow(title="პარამეტრები / უფლებები", content_widget=box, pos=(50, 120))
        win.size = (320, 350)
        self.root_layout.add_widget(win)


if __name__ == "__main__":
    LingoLensDesktopApp().run()
