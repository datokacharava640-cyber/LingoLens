# ==========================================
# LingoLens AI - Movable Window Manager UI (Fully Fixed & Working)
# ==========================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
import config


class MovableWindow(FloatLayout):

    def __init__(self, title="Window", content_widget=None, pos=(20, 50), **kwargs):
        super(MovableWindow, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(340), dp(480))
        self.pos = pos

        # უსაფრთხო შრიფტის განსაზღვრა
        self.font = getattr(config, "GEORGIAN_FONT_NAME", getattr(config, "FONT_PATH", None))

        # მთავარი კონტეინერი ფონითა და ჩარჩოთი
        main_box = BoxLayout(orientation="vertical", size_hint=(1, 1))
        
        with main_box.canvas.before:
            Color(0.1, 0.1, 0.13, 0.95)  # მუქი ფონი ფანჯრისთვის
            self.bg_rect = Rectangle(size=main_box.size, pos=main_box.pos)
        main_box.bind(pos=self._update_bg_rect, size=self._update_bg_rect)

        # სათაურის ველი (მხოლოდ აქედან მოხდება ფანჯრის გადაადგილება)
        self.header_layout = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(45), padding=dp(5)
        )

        # ვიზუალური ფონი სათაურისთვის
        with self.header_layout.canvas.before:
            Color(0.18, 0.18, 0.25, 1)  # მუქი ელფერი ჰედერისათვის
            self.header_rect = Rectangle(size=self.header_layout.size, pos=self.header_layout.pos)
        self.header_layout.bind(pos=self._update_header_rect, size=self._update_header_rect)

        lbl_title = Label(
            text=title, font_name=self.font, bold=True, color=(1, 1, 1, 1), halign="left"
        )
        # იმისათვის, რომ ლეიბლმა მარცხნივ გაასწოროს ტექსტი სწორად
        lbl_title.bind(size=lambda s, w: setattr(s, 'text_size', w))
        self.header_layout.add_widget(lbl_title)

        # დახურვის ღილაკი
        btn_close = Button(
            text="X",
            size_hint_x=None,
            width=dp(40),
            font_name=self.font,
            background_color=(0.8, 0.2, 0.2, 1),
        )
        btn_close.bind(on_press=self.close_window)
        self.header_layout.add_widget(btn_close)

        main_box.add_widget(self.header_layout)

        # კონტენტის დამატება
        if content_widget:
            main_box.add_widget(content_widget)

        self.add_widget(main_box)

        # დრაგინგისთვის (გადაადგილებისთვის) საჭირო ცვლადები
        self.dragging = False
        self.dx = 0
        self.dy = 0

    def _update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_header_rect(self, instance, value):
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size

    def close_window(self, instance):
        if self.parent:
            self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        # ვამოწმებთ, ეხება თუ არა შეხება ზუსტად სათაურის (Header) არის
        if self.header_layout.collide_point(*touch.pos):
            self.dragging = True
            touch.grab(self)
            self.dx = touch.x - self.x
            self.dy = touch.y - self.y
            return True
        return super(MovableWindow, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        # თუ სათაურიდან ვქაჩავთ, ვცვლით ფანჯრის პოზიციას
        if self.dragging and touch.grab_current == self:
            self.x = touch.x - self.dx
            self.y = touch.y - self.dy
            return True
        return super(MovableWindow, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            self.dragging = False
            touch.ungrab(self)
            return True
        return super(MovableWindow, self).on_touch_up(touch)
