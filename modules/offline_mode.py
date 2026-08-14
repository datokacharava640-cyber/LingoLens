class OfflineEngine:
    def __init__(self):
        self.is_active = False

    def toggle(self):
        self.is_active = not self.is_active
        return self.is_active
