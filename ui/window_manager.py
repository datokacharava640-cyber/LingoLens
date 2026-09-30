# ==========================================
# LingoLens AI - Movable Window Manager UI
# ==========================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
import config


class MovableWindow(FloatLayout):

  def __init__(self, title="Window", content_widget=None, pos=(20, 50), **kwargs):
    super(MovableWindow, self).__init__(**kwargs)
    self.size_hint = (None, None)
    self.size = (340, 480)
    self.pos = pos

    # მთავარი კონტეინერი
    main_box = BoxLayout(orientation="vertical", size_hint=(1, 1))

    # სათაურის ველი
    header_layout = BoxLayout(
        orientation="horizontal", size_hint_y=0.1, padding=5
    )
    font = getattr(config, "FONT_PATH", None)

    # ვიზუალური ფონი სათაურისთვის
    with header_layout.canvas.before:
      Color(0.15, 0.15, 0.2, 1)  # მუქი ელფერი ჰედერისათვის
      self.rect = Rectangle(size=header_layout.size, pos=header_layout.pos)
    header_layout.bind(
        pos=self._update_rect, size=self._update_rect
    )  # ზომების ავტომატური განახლება

    lbl_title = Label(
        text=title, font_name=font, bold=True, color=(1, 1, 1, 1), halign="left"
    )
    header_layout.add_widget(lbl_title)

    # დახურვის ღილაკი
    btn_close = Button(
        text="X",
        size_hint_x=None,
        width=40,
        font_name=font,
        background_color=(0.8, 0.2, 0.2, 1),
    )
    btn_close.bind(on_press=self.close_window)
    header_layout.add_widget(btn_close)

    main_box.add_widget(header_layout)

    # კონტენტის დამატება
    if content_widget:
      main_box.add_widget(content_widget)

    self.add_widget(main_box)

  def _update_rect(self, instance, value):
    """სათაურის ფონის ზომის განახლება ლეიაუთის ცვლილებისას"""
    self.rect.pos = instance.pos
    self.rect.size = instance.size

  def close_window(self, instance):
    if self.parent:
      self.parent.remove_widget(self)

  def on_touch_down(self, touch):
    # ვამოწმებთ, ეხება თუ არა შეხება ფანჯრის არეს
    if self.collide_point(*touch.pos):
      touch.grab(self)
      self.dx = touch.x - self.x
      self.dy = touch.y - self.y
      return super(MovableWindow, self).on_touch_down(touch)
    return super(MovableWindow, self).on_touch_down(touch)

  def on_touch_move(self, touch):
    # თუ შეხება დაჭერილია ამ ფანჯარაზე, ვცვლით მის პოზიციას
    if touch.grab_current == self:
      self.x = touch.x - self.dx
      self.y = touch.y - self.dy
      return True
    return super(MovableWindow, self).on_touch_move(touch)

  def on_touch_up(self, touch):
    if touch.grab_current == self:
      touch.ungrab(self)
      return True
    return super(MovableWindow, self).on_touch_up(touch)
