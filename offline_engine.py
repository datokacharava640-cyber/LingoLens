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
            if token.isalnum():
                clean_word = token.lower()
                translated_word = self.dictionary.get(clean_word, token)
                translated_tokens.append(translated_word)
            else:
                translated_tokens.append(token)

        # ტექსტის სწორად აწყობა (სასვენი ნიშნების დაშორების კონტროლით)
        result_parts = []
        for i, token in enumerate(translated_tokens):
            # თუ მიმდინარე ტოკენი სიტყვაა და წინაც სიტყვა იყო, აუცილებლად ვუყრით სფეისს
            if i > 0 and token.isalnum() and translated_tokens[i-1].isalnum():
                result_parts.append(" ")
            # თუ მიმდინარე ტოკენი სასვენი ნიშანია (მაგ. წერტილი ან მძიმე), სფეისს არ ვუწერთ წინ
            result_parts.append(token)

        return "".join(result_parts)
