from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

# Importina ireo rakitra ao amin'ny folder utils, ui, sy config
import config
from utils.translator import translate_text
from utils.tts_engine import speak_text  # raha mampiasa TTS
from ui.window_manager import MovableWindow
from ui.dialogue_window import DialogueWidget
from ui.camera_widget import CameraWidget  # raha efa misy ny camera widget

class LingoLensDesktopApp(App):
    def build(self):
        self.root_layout = FloatLayout()

        # Grid ho an'ny menu lehibe
        menu_grid = GridLayout(
            cols=2, 
            spacing=15, 
            padding=20, 
            size_hint=(0.85, 0.75), 
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        font = getattr(config, 'FONT_PATH', None)

        # Bokotra ho an'ny fampiharana kely
        btn_translator = Button(text="თარგმანი\n(Translator)", font_name=font, on_press=self.open_translator)
        btn_dialogue = Button(text="დიალოგი\n(Live Dialogue)", font_name=font, on_press=self.open_dialogue)
        btn_grammar = Button(text="გრამატიკა\n(Grammar AI)", font_name=font, on_press=self.open_grammar)
        btn_camera = Button(text="კამერა\n(Camera OCR)", font_name=font, on_press=self.open_camera)
        btn_settings = Button(text="პარამეტრები\n(Settings)", font_name=font)

        menu_grid.add_widget(btn_translator)
        menu_grid.add_widget(btn_dialogue)
        menu_grid.add_widget(btn_grammar)
        menu_grid.add_widget(btn_camera)
        menu_grid.add_widget(btn_settings)

        self.root_layout.add_widget(menu_grid)
        return self.root_layout

    # 1. Translator Window
    def open_translator(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        inp = TextInput(hint_text="ტექსტი...", font_name=font, multiline=True)
        out = TextInput(hint_text="თარგმანი...", font_name=font, readonly=True, multiline=True)
        
        btn_trans = Button(text="თარგმნა", font_name=font, size_hint_y=0.2)
        
        def run_trans(btn_inst):
            if inp.text.strip():
                prompt = f"Translate from ka to en: {inp.text}"
                translate_text(
                    prompt, inp.text, "ka", "en", 
                    lambda res: Clock.schedule_once(lambda dt: setattr(out, 'text', res))
                )

        btn_trans.bind(on_press=run_trans)

        box.add_widget(inp)
        box.add_widget(btn_trans)
        box.add_widget(out)

        win = MovableWindow(title="LingoLens თარგმანი", content_widget=box, pos=(40, 120))
        self.root_layout.add_widget(win)

    # 2. Dialogue Window (mampiasa dialogue_window.py)
    def open_dialogue(self, instance):
        dialogue_content = DialogueWidget()
        win = MovableWindow(title="LingoLens დიალოგი", content_widget=dialogue_content, pos=(30, 60))
        win.size = (340, 520)
        self.root_layout.add_widget(win)

    # 3. Grammar Check Window
    def open_grammar(self, instance):
        font = getattr(config, 'FONT_PATH', None)
        box = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        inp = TextInput(hint_text="შესამოწმებელი ტექსტი...", font_name=font)
        out = TextInput(hint_text="შედეგი...", font_name=font, readonly=True)
        btn_check = Button(text="შემოწმება", font_name=font, size_hint_y=0.2)

        def run_grammar(btn_inst):
            if inp.text.strip():
                prompt = f"Correct grammar: {inp.text}"
                translate_text(
                    prompt, inp.text, "ka", "en", 
                    lambda res: Clock.schedule_once(lambda dt: setattr(out, 'text', res))
                )

        btn_check.bind(on_press=run_grammar)

        box.add_widget(inp)
        box.add_widget(btn_check)
        box.add_widget(out)

        win = MovableWindow(title="გრამატიკის შემოწმება", content_widget=box, pos=(80, 160))
        self.root_layout.add_widget(win)

    # 4. Camera Window (mampiasa camera_widget.py)
    def open_camera(self, instance):
        try:
            cam_content = CameraWidget()
            win = MovableWindow(title="კამერა OCR", content_widget=cam_content, pos=(50, 100))
            win.size = (350, 450)
            self.root_layout.add_widget(win)
        except Exception as e:
            print("Camera error:", e)

if __name__ == "__main__":
    LingoLensDesktopApp().run()
