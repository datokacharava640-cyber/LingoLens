# Offline Fallback Engine
class OfflineEngine:
    def __init__(self):
        self.dictionary = {
            "hello": "გამარჯობა",
            "world": "სამყარო",
            "camera": "კამერა",
            "translation": "თარგმანი"
        }

    def translate(self, text, src='en', tgt='ka'):
        words = text.lower().split()
        res = [self.dictionary.get(w, w) for w in words]
        return " ".join(res)
