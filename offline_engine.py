import re

class OfflineEngine:
    def __init__(self):
        # ლექსიკონი (შეგიძლია გააფართოო ან ჩატვირთო JSON ფაილიდან)
        self.dictionary = {
            "hello": "გამარჯობა",
            "world": "სამყარო",
            "camera": "კამერა",
            "translation": "თარგმანი",
            "good": "კარგი",
            "morning": "დილა"
        }

    def translate(self, text: str, src='en', tgt='ka') -> str:
        if not text or not text.strip():
            return ""

        # regex-ით სიტყვების და სასვენი ნიშნების განცალკევება
        tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
        
        translated_tokens = []
        for token in tokens:
            # თუ სიმბოლო სიტყვაა
            if token.isalnum():
                clean_word = token.lower()
                # ლექსიკონში მოძებნა, თუ ვერ იპოვა - ტოვებს ორიგინალს
                translated_word = self.dictionary.get(clean_word, token)
                translated_tokens.append(translated_word)
            else:
                # სასვენი ნიშნები და პრობელები რჩება უცვლელი
                translated_tokens.append(token)

        # ტექსტის აწყობა (სასვენი ნიშნების სწორი დაშორებით)
        result = ""
        for i, token in enumerate(translated_tokens):
            if i > 0 and token.isalnum() and translated_tokens[i-1].isalnum():
                result += " " + token
            elif i > 0 and token.isalnum():
                result += " " + token
            else:
                result += token

        return result
