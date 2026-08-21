from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
import math

class GeorgianFlagWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_flag, size=self.update_flag)
        self.wave_phase = 0
        Clock.schedule_interval(self.animate_wave, 1 / 30.0)

    def animate_wave(self, dt):
        self.wave_phase += dt * 3
        self.update_flag()

    def update_flag(self, *args):
        self.canvas.clear()
        x, y = self.x, self.y
        w, h = self.width, self.height

        if w <= 0 or h <= 0:
            return

        with self.canvas:
            # თეთრი ფონი
            Color(1, 1, 1, 1)
            Rectangle(pos=(x, y), size=(w, h))

            # წითელი ფერი
            Color(1, 0, 0, 1)

            # ცენტრალური დიდი ჯვარი
            cross_thickness = min(w, h) * 0.2
            # ვერტიკალური
            Rectangle(pos=(x + (w - cross_thickness) / 2, y), size=(cross_thickness, h))
            # ჰორიზონტალური
            Rectangle(pos=(x, y + (h - cross_thickness) / 2), size=(w, cross_thickness))

            # 4 მცირე ჯვრის დახატვა ოთხივე კუთხეში
            quad_w = (w - cross_thickness) / 2
            quad_h = (h - cross_thickness) / 2
            small_thick = cross_thickness * 0.3
            small_len = min(quad_w, quad_h) * 0.4

            centers = [
                (x + quad_w / 2, y + quad_h * 1.5 + cross_thickness), # ზედა მარცხენა
                (x + quad_w * 1.5 + cross_thickness, y + quad_h * 1.5 + cross_thickness), # ზედა მარჯვენა
                (x + quad_w / 2, y + quad_h / 2), # ქვედა მარცხენა
                (x + quad_w * 1.5 + cross_thickness, y + quad_h / 2) # ქვედა მარჯვენა
            ]

            for cx, cy in centers:
                # ანიმაციური რხევა (ტალღის ეფექტი)
                offset = math.sin(self.wave_phase + (cx / w) * 3) * (h * 0.02)
                cy_anim = cy + offset
                
                # მცირე ჯვრები (Bolnisi Cross style)
                Rectangle(pos=(cx - small_len / 2, cy_anim - small_thick / 2), size=(small_len, small_thick))
                Rectangle(pos=(cx - small_thick / 2, cy_anim - small_len / 2), size=(small_thick, small_len))
