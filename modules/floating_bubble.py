from kivy.utils import platform

class FloatingBubbleService:
    def __init__(self):
        self.is_active = False

    def start_bubble(self):
        if platform == 'android':
            from jnius import autoclass
            # Android Service Integration for Screen Overlay
            PythonService = autoclass('org.kivy.android.PythonService')
            self.is_active = True
            print("Floating Bubble Service Started")

    def stop_bubble(self):
        self.is_active = False
