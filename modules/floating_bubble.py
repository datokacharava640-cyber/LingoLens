# modules/floating_bubble.py

class FloatingBubbleService:
    def __init__(self):
        self.is_active = False

    def toggle_bubble(self):
        self.is_active = not self.is_active
        state = "ACTIVE 🟢" if self.is_active else "DISABLED 🔴"
        return f"🎈 Screen Overlay Bubble: {state}\n(Floating bubble enables quick translation over WhatsApp/TikTok)"

    def translate_screen_text(self, text):
        if not text:
            return "🎈 Floating Bubble: No text detected on screen."
        return f"🎈 Quick Screen Translate: {text}"
