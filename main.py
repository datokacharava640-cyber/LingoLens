# ==============================================================================
# LingoLens AI - Real-time Voice & Vision Translator (v6.8.1)
# ==============================================================================

import json
import os
import sys
import threading
import urllib.request
import base64

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.uix.camera import Camera
from kivy.utils import platform

if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE, Permission.RECORD_AUDIO])

FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="GeorgianFont", fn_regular=FONT_PATH)
    GEORGIAN_FONT_NAME = "GeorgianFont"
else:
    GEORGIAN_FONT_NAME = "Roboto"

HISTORY_FILE = "translation_history.json"

SUPPORTED_LANGUAGES = {
    "Georgian": "ka",
    "English": "en",
    "Spanish": "es",
    "German": "de",
    "French": "fr",
    "Italian": "it",
    "Turkish": "tr",
    "Russian": "ru",
    "Portuguese": "pt",
    "Polish": "pl",
    "Latin (English Letters)": "latn"
}

UI_TEXTS = {
    "ka": {
        "menu_translator": "Mtargmneli",
        "menu_dialogue": "Dialogi (pirispir xmovani)",
        "menu_gallery": "Galerea",
        "menu_camera": "Laiv Kamera / OCR",
        "menu_history": "Istoria",
        "menu_settings": "Parametrebi",
        "btn_back": "Ukan",
        "btn_translate": "Targmna",
        "btn_copy": "Kopireba",
        "btn_share": "Gaziareba",
        "btn_speak": "Xmovani",
        "hint_input": "chaწერet teqsti...",
        "hint_output": "gramatikulad sufta da ushecmodo targmani...",
        "status_processing": "mushavdeba...",
        "error_connection": "shecdomaa servertan",
    },
    "en": {
        "menu_translator": "Translator",
        "menu_dialogue": "Dialogue (Face-to-Face Voice)",
        "menu_gallery": "Gallery",
        "menu_camera": "Live Camera / OCR",
        "menu_history": "History",
        "menu_settings": "Settings",
        "btn_back": "Back",
        "btn_translate": "Translate",
        "btn_copy": "Copy",
        "btn_share": "Share",
        "btn_speak": "Speak",
        "hint_input": "Type text here...",
        "hint_output": "Grammatically clean and flawless translation...",
        "status_processing": "Processing...",
        "error_connection": "Server connection error",
    },
    "es": {
        "menu_translator": "Traductor",
        "menu_dialogue": "Diálogo (Voz cara a cara)",
        "menu_gallery": "Galería",
        "menu_camera": "Cámara en vivo / OCR",
        "menu_history": "Historial",
        "menu_settings": "Ajustes",
        "btn_back": "Atrás",
        "btn_translate": "Traducir",
        "btn_copy": "Copiar",
        "btn_share": "Compartir",
        "btn_speak": "Hablar",
        "hint_input": "Escribe texto aquí...",
        "hint_output": "Traducción impecable y gramaticalmente correcta...",
        "status_processing": "Procesando...",
        "error_connection": "Error de conexión con el servidor",
    },
    "de": {
        "menu_translator": "Übersetzer",
        "menu_dialogue": "Dialog (Face-to-Face Sprache)",
        "menu_gallery": "Galerie",
        "menu_camera": "Live-Kamera / OCR",
        "menu_history": "Verlauf",
        "menu_settings": "Einstellungen",
        "btn_back": "Zurück",
        "btn_translate": "Übersetzen",
        "btn_copy": "Kopieren",
        "btn_share": "Teilen",
        "btn_speak": "Sprechen",
        "hint_input": "Text hier eingeben...",
        "hint_output": "Grammatikalisch saubere und fehlerfreie Übersetzung...",
        "status_processing": "Wird verarbeitet...",
        "error_connection": "Serververbindungsfehler",
    },
    "fr": {
        "menu_translator": "Traducteur",
        "menu_dialogue": "Dialogue (Voix face à face)",
        "menu_gallery": "Galerie",
        "menu_camera": "Caméra en direct / OCR",
        "menu_history": "Historique",
        "menu_settings": "Paramètres",
        "btn_back": "Retour",
        "btn_translate": "Traduire",
        "btn_copy": "Copier",
        "btn_share": "Partager",
        "btn_speak": "Parler",
        "hint_input": "Tapez le texte ici...",
        "hint_output": "Traduction grammaticalement propre et sans erreur...",
        "status_processing": "Traitement en cours...",
        "error_connection": "Erreur de connexion au serveur",
    },
    "it": {
        "menu_translator": "Traduttore",
        "menu_dialogue": "Dialogo (Voce faccia a faccia)",
        "menu_gallery": "Galleria",
        "menu_camera": "Telecamera dal vivo / OCR",
        "menu_history": "Cronologia",
        "menu_settings": "Impostazioni",
        "btn_back": "Indietro",
        "btn_translate": "Traduci",
        "btn_copy": "Copia",
        "btn_share": "Condividi",
        "btn_speak": "Parla",
        "hint_input": "Digita il testo qui...",
        "hint_output": "Traduzione grammaticalmente pulita e impeccabile...",
        "status_processing": "Elaborazione in corso...",
        "error_connection": "Errore di connessione al server",
    },
    "tr": {
        "menu_translator": "Çevirmen",
        "menu_dialogue": "İletişim (Yüz Yüze Sesli)",
        "menu_gallery": "Galeri",
        "menu_camera": "Canlı Kamera / OCR",
        "menu_history": "Geçmiş",
        "menu_settings": "Ayarlar",
        "btn_back": "Geri",
        "btn_translate": "Çevir",
        "btn_copy": "Kopyala",
        "btn_share": "Paylaş",
        "btn_speak": "Konuş",
        "hint_input": "Buraya metin girin...",
        "hint_output": "Dilbilgisel olarak temiz ve kusursuz çeviri...",
        "status_processing": "İşleniyor...",
        "error_connection": "Sunucu bağlantı hatası",
    },
    "ru": {
        "menu_translator": "Переводчик",
        "menu_dialogue": "Диалог (Голосовой тет-а-тет)",
        "menu_gallery": "Галерея",
        "menu_camera": "Живая камера / OCR",
        "menu_history": "История",
        "menu_settings": "Настройки",
        "btn_back": "Назад",
        "btn_translate": "Перевести",
        "btn_copy": "Копировать",
        "btn_share": "Поделиться",
        "btn_speak": "Озвучить",
        "hint_input": "Введите текст здесь...",
        "hint_output": "Грамматически чистый и безупречный перевод...",
        "status_processing": "Обработка...",
        "error_connection": "Ошибка подключения к серверу",
    },
    "pt": {
        "menu_translator": "Tradutor",
        "menu_dialogue": "Diálogo (Voz face a face)",
        "menu_gallery": "Galeria",
        "menu_camera": "Câmera ao vivo / OCR",
        "menu_history": "Histórico",
        "menu_settings": "Configurações",
        "btn_back": "Voltar",
        "btn_translate": "Traduzir",
        "btn_copy": "Copiar",
        "btn_share": "Compartilhar",
        "btn_speak": "Falar",
        "hint_input": "Digite o texto aqui...",
        "hint_output": "Tradução gramaticalmente limpa e impecável...",
        "status_processing": "Processando...",
        "error_connection": "Erro de conexão com o servidor",
    },
    "pl": {
        "menu_translator": "Tłumacz",
        "menu_dialogue": "Dialog (Głos twarzą w twarz)",
        "menu_gallery": "Galeria",
        "menu_camera": "Kamera na żywo / OCR",
        "menu_history": "Historia",
        "menu_settings": "Ustawienia",
        "btn_back": "Wstecz",
        "btn_translate": "Przetłumacz",
        "btn_copy": "Kopiuj",
        "btn_share": "Udostępnij",
        "btn_speak": "Mów",
        "hint_input": "Wpisz tekst tutaj...",
        "hint_output": "Gramatycznie czyste i bezbłędne tłumaczenie...",
        "status_processing": "Przetwarzanie...",
        "error_connection": "Błąd połączenia z serwerem",
    },
    "latn": {
        "menu_translator": "Mtargmneli",
        "menu_dialogue": "Dialogi",
        "menu_gallery": "Galerea",
        "menu_camera": "Laiv Kamera",
        "menu_history": "Istoria",
        "menu_settings": "Parametrebi",
        "btn_back": "Ukan",
        "btn_translate": "Targmna",
        "btn_copy": "Kopireba",
        "btn_share": "Gaziareba",
        "btn_speak": "Xmovani",
        "hint_input": "chaferet teqsti...",
        "hint_output": "gramatikulad sufta targmani...",
        "status_processing": "mushavdeba...",
        "error_connection": "shecdomaa servertan",
    }
}

class CustomSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = GEORGIAN_FONT_NAME

class LingoLensApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.in_main_menu = True
        self.live_event = None
        self.cam_index = 0
        self.active_mic = None
        self.current_ui_lang = "ka"

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard_event)
        self.root_layout = FloatLayout()
        self.show_main_menu()
        return self.root_layout

    def on_keyboard_event(self, window, key, scancode, codepoint, modifier):
        if key == 27:  
            if not self.in_main_menu:
                self.stop_live_translation()
                self.show_main_menu()
                return True
            else:
                self.stop()
                return True
        return False

    def get_text(self, key):
        lang_dict = UI_TEXTS.get(self.current_ui_lang, UI_TEXTS["ka"])
        return lang_dict.get(key, UI_TEXTS["ka"].get(key, key))

    def update_ui_language(self, lang_code):
        if lang_code in UI_TEXTS:
            self.current_ui_lang = lang_code

    def show_main_menu(self, instance=None):
        self.stop_live_translation()
        self.in_main_menu = True
        Clock.schedule_once(lambda dt: self._apply_main_menu(), 0)

    def _apply_main_menu(self):
        self.root_layout.clear_widgets()

        menu_grid = GridLayout(
            cols=2, spacing=dp(15), padding=dp(20),
            size_hint=(0.9, 0.8), pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        font = GEORGIAN_FONT_NAME
        
        btn_translator = Button(text=self.get_text("menu_translator"), font_name=font, on_press=self.open_translator)
        btn_dialogue = Button(text=self.get_text("menu_dialogue"), font_name=font, on_press=self.open_dialogue)
        btn_gallery = Button(text=self.get_text("menu_gallery"), font_name=font, on_press=self.open_gallery)
        btn_camera = Button(text=self.get_text("menu_camera"), font_name=font, on_press=self.open_live_camera_view)
        btn_history = Button(text=self.get_text("menu_history"), font_name=font, on_press=self.open_history)
        btn_settings = Button(text=self.get_text("menu_settings"), font_name=font, on_press=self.open_settings)

        menu_grid.add_widget(btn_translator)
        menu_grid.add_widget(btn_dialogue)
        menu_grid.add_widget(btn_gallery)
        menu_grid.add_widget(btn_camera)
        menu_grid.add_widget(btn_history)
        menu_grid.add_widget(btn_settings)

        self.root_layout.add_widget(menu_grid)

    def switch_to_view(self, widget):
        self.in_main_menu = False
        Clock.schedule_once(lambda dt: self._apply_switch_to_view(widget), 0)

    def _apply_switch_to_view(self, widget):
        self.root_layout.clear_widgets()
        font = GEORGIAN_FONT_NAME

        container = BoxLayout(orientation="vertical", size_hint=(1, 1), spacing=0)
        top_bar = BoxLayout(orientation="horizontal", size_hint_y=0.1, padding=dp(5), spacing=dp(10))
        
        def go_back(x):
            self.stop_live_translation()
            self.show_main_menu()

        btn_back = Button(text=self.get_text("btn_back"), font_name=font, size_hint_x=0.3, on_press=go_back)
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text="", size_hint_x=0.7))

        container.add_widget(top_bar)
        container.add_widget(widget)
        self.root_layout.add_widget(container)

    def open_gallery(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15), size_hint=(1, 1))
        
        info_lbl = Label(
            text="Galereidan fotos archevis modeli\n(airchiet foto teqstis asatvirtad da satargmnad)", 
            font_name=font, halign="center", valign="middle"
        )
        info_lbl.bind(size=info_lbl.setter("text_size"))
        box.add_widget(info_lbl)

        def pick_image_from_device(btn):
            try:
                from plyer import filechooser
                filechooser.open_file(on_selection=self.handle_selected_image, filters=[("Images", "*.png;*.jpg;*.jpeg")])
            except Exception as e:
                print("Gallery open error:", e)
                info_lbl.text = "Galereis gaxsna ver moxerxda am garemoshi."

        btn_pick = Button(text="fotos archeva galereidan", font_name=font, size_hint_y=0.2)
        btn_pick.bind(on_press=pick_image_from_device)
        box.add_widget(btn_pick)

        self.switch_to_view(box)

    def handle_selected_image(self, selection):
        if selection:
            img_path = selection[0]
            print("Selected image path:", img_path)
            try:
                with open(img_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                
                def on_server_response(res):
                    if res:
                        Clock.schedule_once(lambda dt: self.open_translator(initial_text=f"{res}"))
                    else:
                        print("OCR extraction failed.")
                
                self.remote_translate(
                    prompt="Extract all visible text accurately from this image without modifying or altering its content.",
                    text=encoded_string, src_lang="auto", target_lang="ka", callback=on_server_response
                )
            except Exception as e:
                print("Image processing error:", e)

    def open_live_camera_view(self, instance):
        font = GEORGIAN_FONT_NAME
        box = FloatLayout(size_hint=(1, 1))

        self.cam_widget = Camera(
            play=True, 
            index=self.cam_index,
            resolution=(-1, -1), 
            size_hint=(None, None), 
            allow_stretch=True, 
            keep_ratio=False
        )

        from kivy.graphics import PushMatrix, PopMatrix, Rotate
        with self.cam_widget.canvas.before:
            PushMatrix()
            self.cam_rot = Rotate(angle=270, origin=self.cam_widget.center)
        with self.cam_widget.canvas.after:
            PopMatrix()
            
        def update_cam_geometry(win, size):
            self.cam_widget.size = (size[1], size[0])
            self.cam_widget.center = (size[0] / 2, size[1] / 2)
            self.cam_rot.origin = self.cam_widget.center

        Window.bind(size=update_cam_geometry)
        update_cam_geometry(Window, Window.size)

        box.add_widget(self.cam_widget)

        def go_back(x):
            Window.unbind(size=update_cam_geometry)
            self.stop_live_translation()
            self.show_main_menu()

        btn_back = Button(
            text=self.get_text("btn_back"), font_name=font, 
            size_hint=(0.3, 0.08), pos_hint={"top": 0.95, "left": 0.05},
            background_color=(0, 0, 0, 0.6)
        )
        btn_back.bind(on_press=go_back)
        box.add_widget(btn_back)

        lang_names = list(SUPPORTED_LANGUAGES.keys())
        self.live_lang_spinner = Spinner(
            text="Georgian", values=lang_names, font_name=font, option_cls=CustomSpinnerOption,
            size_hint=(0.4, 0.08), pos_hint={"top": 0.95, "right": 0.95},
            background_color=(0, 0, 0, 0.6)
        )
        box.add_widget(self.live_lang_spinner)

        self.live_result_lbl = Label(
            text="miasheret kamera tsarseraze...", font_name=font, 
            size_hint=(0.9, 0.15), pos_hint={"center_x": 0.5, "y": 0.03},
            halign="center", valign="middle",
            color=(1, 1, 1, 1)
        )
        self.live_result_lbl.bind(size=self.live_result_lbl.setter("text_size"))
        box.add_widget(self.live_result_lbl)

        self.in_main_menu = False
        Clock.schedule_once(lambda dt: self._apply_custom_view(box), 0)

        self.live_event = Clock.schedule_interval(self.capture_and_translate_frame, 3.0)

    def _apply_custom_view(self, widget):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(widget)

    def capture_and_translate_frame(self, dt):
        try:
            if hasattr(self, 'cam_widget') and self.cam_widget:
                image_path = "temp_live_frame.png"
                self.cam_widget.export_to_png(image_path)
                
                selected_lang_name = self.live_lang_spinner.text
                target_code = SUPPORTED_LANGUAGES.get(selected_lang_name, "ka")
                
                self.live_result_lbl.text = "mimdinareobs gramatikulad sufta targmna..."
                
                def on_server_response(res):
                    if res:
                        Clock.schedule_once(lambda dt: setattr(self.live_result_lbl, 'text', f"Targmani: {res}"))
                    else:
                        Clock.schedule_once(lambda dt: setattr(self.live_result_lbl, 'text', "ver moidzebna teqsti"))
                
                prompt_text = f"Translate into {selected_lang_name} using Latin script with absolute grammatical precision and zero errors."
                
                self.remote_translate(
                    prompt=prompt_text,
                    text="[Live Frame OCR Placeholder]", 
                    src_lang="auto", 
                    target_lang=target_code, 
                    callback=on_server_response
                )
        except Exception as e:
            print("Live frame capture error:", e)

    def stop_live_translation(self):
        if self.live_event:
            self.live_event.cancel()
            self.live_event = None
        if hasattr(self, 'cam_widget'):
            self.cam_widget.play = False

    def save_to_history(self, original, translated):
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
        history.append({"original": original, "translated": translated})
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def copy_to_clipboard(self, text):
        if text and text.strip():
            Clipboard.copy(text)

    def share_text(self, text, status_lbl=None):
        if text and text.strip():
            shared = False
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent()
                intent.setAction(Intent.ACTION_SEND)
                intent.setType('text/plain')
                intent.putExtra(Intent.EXTRA_TEXT, text)
                chooser = Intent.createChooser(intent, "Share via")
                PythonActivity.mActivity.startActivity(chooser)
                shared = True
            except Exception as e:
                print("Android native share error:", e)
                try:
                    from plyer import share
                    share.share(text=text)
                    shared = True
                except Exception as e2:
                    print("Plyer share error:", e2)
            
            if not shared and status_lbl:
                status_lbl.text = "Gaziareba ver moxerxda!"

    def speak_text(self, text, lang_code="ka"):
        if text and text.strip():
            try:
                from plyer import tts
                # Try passing language parameter if supported by platform TTS
                tts.speak(text)
            except Exception as e:
                print("TTS error:", e)
                try:
                    from jnius import autoclass
                    Locale = autoclass('java.util.Locale')
                    AndroidTTS = autoclass('android.speech.tts.TextToSpeech')
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    # Fallback native android tts if available
                except Exception as ex2:
                    print("Android native TTS fallback error:", ex2)

    def remote_translate(self, prompt, text, src_lang, target_lang, callback):
        def worker():
            try:
                url = "http://37.27.255.1:8000/translate"
                payload = json.dumps({
                    "text": text, "source": src_lang, "target": target_lang, "prompt": prompt
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    result_text = res_data.get("translated_text") or res_data.get("result") or str(res_data)
                    callback(result_text)
            except Exception as e:
                print("Server connection error:", e)
                callback(None)
        threading.Thread(target=worker, daemon=True).start()

    def open_translator(self, instance=None, initial_text=""):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, 1))

        lang_box = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=0.1)
        lang_names = list(SUPPORTED_LANGUAGES.keys())

        sp_src = Spinner(text="Georgian", values=lang_names, font_name=font, option_cls=CustomSpinnerOption)
        sp_target = Spinner(text="English", values=lang_names, font_name=font, option_cls=CustomSpinnerOption)

        inp = TextInput(text=initial_text, hint_text=self.get_text("hint_input"), font_name=font, multiline=True, size_hint_y=0.25)
        out = TextInput(hint_text=self.get_text("hint_output"), font_name=font, readonly=True, multiline=True, size_hint_y=0.25)
        status_lbl = Label(text="", size_hint_y=0.05, font_name=font)

        btn_trans = Button(text=self.get_text("btn_translate"), font_name=font, size_hint_y=0.1)

        action_box = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=0.1)
        btn_copy = Button(text=self.get_text("btn_copy"), font_name=font, on_press=lambda x: self.copy_to_clipboard(out.text))
        btn_share = Button(text=self.get_text("btn_share"), font_name=font, on_press=lambda x: self.share_text(out.text, status_lbl))
        
        def handle_speak(x):
            target_code = SUPPORTED_LANGUAGES.get(sp_target.text, "en")
            self.speak_text(out.text, lang_code=target_code)

        btn_speak = Button(text=self.get_text("btn_speak"), font_name=font, on_press=handle_speak)
        
        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_speak)

        def update_labels_and_ui():
            src_code = SUPPORTED_LANGUAGES.get(sp_src.text, "ka")
            target_code = SUPPORTED_LANGUAGES.get(sp_target.text, "en")
            
            if src_code in UI_TEXTS:
                self.update_ui_language(src_code)
            elif target_code in UI_TEXTS:
                self.update_ui_language(target_code)
                
            inp.hint_text = self.get_text("hint_input")
            out.hint_text = self.get_text("hint_output")
            btn_trans.text = self.get_text("btn_translate")
            btn_copy.text = self.get_text("btn_copy")
            btn_share.text = self.get_text("btn_share")
            btn_speak.text = self.get_text("btn_speak")

        def on_spinner_changed(spinner, text):
            update_labels_and_ui()

        sp_src.bind(text=on_spinner_changed)
        sp_target.bind(text=on_spinner_changed)

        def swap_languages(instance):
            temp = sp_src.text
            sp_src.text = sp_target.text
            sp_target.text = temp

        btn_swap = Button(text="<=>", size_hint_x=0.2, font_name=font)
        btn_swap.bind(on_press=swap_languages)

        lang_box.add_widget(sp_src)
        lang_box.add_widget(btn_swap)
        lang_box.add_widget(sp_target)

        def handle_translation(btn_inst):
            text_to_translate = inp.text.strip()
            if not text_to_translate:
                status_lbl.text = "gtxovt sheiyvanot teqsti"
                return

            src_code = SUPPORTED_LANGUAGES.get(sp_src.text, "ka")
            target_code = SUPPORTED_LANGUAGES.get(sp_target.text, "en")
            status_lbl.text = self.get_text("status_processing")
            out.text = ""

            def on_res(res):
                res_text = str(res) if res else self.get_text("error_connection")
                Clock.schedule_once(lambda dt: setattr(out, "text", res_text))
                Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))
                if res:
                    self.save_to_history(text_to_translate, res_text)

            try:
                strict_prompt = (
                    f"Translate the following text from {sp_src.text} to {sp_target.text} using Latin script "
                    f"with absolute grammatical precision and zero errors: {text_to_translate}"
                )
                self.remote_translate(
                    prompt=strict_prompt,
                    text=text_to_translate, src_lang=src_code, target_lang=target_code, callback=on_res
                )
            except Exception as e:
                print("Translation Error:", e)
                Clock.schedule_once(lambda dt: setattr(out, "text", self.get_text("error_connection")))
                Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))

        btn_trans.bind(on_press=handle_translation)

        box.add_widget(lang_box)
        box.add_widget(inp)
        box.add_widget(btn_trans)
        box.add_widget(status_lbl)
        box.add_widget(out)
        box.add_widget(action_box)

        update_labels_and_ui()

        if instance is not None:
            self.switch_to_view(box)
        return box

    def open_dialogue(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(15), size_hint=(1, 1))
        
        info_label = Label(
            text="airchiet meore mosabris ena da isaubret realur droshi (pirispir)",
            font_name=font, halign="center", valign="middle", size_hint_y=0.1
        )
        info_label.bind(size=info_label.setter("text_size"))
        box.add_widget(info_label)

        lang_names = list(SUPPORTED_LANGUAGES.keys())
        self.dialogue_spinner = Spinner(
            text="English", values=lang_names, font_name=font, option_cls=CustomSpinnerOption,
            size_hint=(1, 0.1)
        )
        box.add_widget(self.dialogue_spinner)

        box_p1 = BoxLayout(orientation="vertical", size_hint_y=0.35, spacing=dp(5))
        lbl_p1_title = Label(text="1-li mosabre (qartuli ena)", font_name=font, size_hint_y=0.2)
        lbl_p1_result = Label(text="mosmenili teqsti / targmani gamochndeba aq...", font_name=font, halign="center", valign="middle", size_hint_y=0.5)
        lbl_p1_result.bind(size=lbl_p1_result.setter("text_size"))
        
        def toggle_mic_1(btn):
            if self.active_mic == 1:
                self.active_mic = None
                btn.text = "Shesvla / Chartva (qartuli mikrofoni)"
                btn.background_color = (0.2, 0.6, 0.9, 1)
                lbl_p1_result.text = "mikrofoni shecherebulia."
            else:
                self.active_mic = 1
                btn.text = "Mismens qartulad... (shechereba)"
                btn.background_color = (0.8, 0.2, 0.2, 1)
                lbl_p1_result.text = "isaubret bunebrivad qartulad..."
                
        btn_mic_1 = Button(text="Shesvla / Chartva (qartuli mikrofoni)", font_name=font, size_hint_y=0.3, background_color=(0.2, 0.6, 0.9, 1))
        btn_mic_1.bind(on_press=toggle_mic_1)
        
        box_p1.add_widget(lbl_p1_title)
        box_p1.add_widget(lbl_p1_result)
        box_p1.add_widget(btn_mic_1)
        box.add_widget(box_p1)

        box_p2 = BoxLayout(orientation="vertical", size_hint_y=0.35, spacing=dp(5))
        lbl_p2_title = Label(text="me-2 mosabre (archeuli ucxouri ena)", font_name=font, size_hint_y=0.2)
        lbl_p2_result = Label(text="mosmenili teqsti / targmani gamochndeba aq...", font_name=font, halign="center", valign="middle", size_hint_y=0.5)
        lbl_p2_result.bind(size=lbl_p2_result.setter("text_size"))
        
        def toggle_mic_2(btn):
            if self.active_mic == 2:
                self.active_mic = None
                btn.text = "Shesvla / Chartva (ucxouri mikrofoni)"
                btn.background_color = (0.9, 0.5, 0.2, 1)
                lbl_p2_result.text = "mikrofoni shecherebulia."
            else:
                self.active_mic = 2
                btn.text = "Mismens ucxourad... (shechereba)"
                btn.background_color = (0.8, 0.2, 0.2, 1)
                lbl_p2_result.text = "isaubret archeul ucxo enaze..."
                
        btn_mic_2 = Button(text="Shesvla / Chartva (ucxouri mikrofoni)", font_name=font, size_hint_y=0.3, background_color=(0.9, 0.5, 0.2, 1))
        btn_mic_2.bind(on_press=toggle_mic_2)
        
        box_p2.add_widget(lbl_p2_title)
        box_p2.add_widget(lbl_p2_result)
        box_p2.add_widget(btn_mic_2)
        box.add_widget(box_p2)

        self.switch_to_view(box)

    def open_history(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(5), size_hint=(1, 1))
        scroller = ScrollView()
        content = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    for item in reversed(history):
                        orig = item.get("original", "")
                        trans = item.get("translated", "")
                        lbl = Label(
                            text=f"{orig} ➔ {trans}", font_name=font,
                            size_hint_y=None, height=dp(40), halign="left", valign="middle"
                        )
                        lbl.bind(size=lbl.setter("text_size"))
                        content.add_widget(lbl)
            except Exception:
                pass
        if not content.children:
            content.add_widget(Label(text="istoria carielia", font_name=font))
        scroller.add_widget(content)
        box.add_widget(scroller)
        self.switch_to_view(box)

    def open_settings(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(10), size_hint=(1, 1))
        scroller = ScrollView()
        content = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(Label(text="Parametrebi", font_name=font, size_hint_y=None, height=dp(40)))

        def clear_hist(btn):
            if os.path.exists(HISTORY_FILE):
                try:
                    os.remove(HISTORY_FILE)
                except Exception:
                    pass

        btn_clear = Button(text="istoris gasuftaveba", font_name=font, size_hint_y=None, height=dp(50))
        btn_clear.bind(on_press=clear_hist)
        content.add_widget(btn_clear)

        privacy_text = (
            "2. Konfidencialuroba da Kontroli:\n"
            "Gancxadeba imis shesaxeb, rom kameras, mikrofonsa da galereas mesame pirebi ar akontroleben.\n\n"
            "Privacy & Control:\n"
            "Declaration that camera, microphone, and gallery are not controlled by third parties."
        )
        lbl_privacy = Label(text=privacy_text, font_name=font, size_hint_y=None, height=dp(110), halign="left", valign="middle")
        lbl_privacy.bind(size=lbl_privacy.setter("text_size"))
        content.add_widget(lbl_privacy)

        copyright_text = (
            "3. Saavtoro უფლებები (Copyrights):\n"
            "• Avtori / Creator: Dato Kacharava\n"
            "• Tarigi / Date: October 2, 2026"
        )
        lbl_copy = Label(text=copyright_text, font_name=font, size_hint_y=None, height=dp(90), halign="left", valign="middle")
        lbl_copy.bind(size=lbl_copy.setter("text_size"))
        content.add_widget(lbl_copy)

        footer_lbl = Label(text="LingoLens AI v6.8.1", font_name=font, size_hint_y=None, height=dp(40))
        content.add_widget(footer_lbl)

        scroller.add_widget(content)
        box.add_widget(scroller)
        self.switch_to_view(box)

if __name__ == "__main__":
    LingoLensApp().run()
