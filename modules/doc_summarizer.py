import os
import requests
from modules.config import Config

try:
    import pypdf
except ImportError:
    pypdf = None


class DocumentSummarizer:
    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(Config, 'GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def extract_text_from_file(self, file_path):
        """კითხულობს ტექსტს PDF ან TXT ფაილიდან"""
        text = ""
        if not os.path.exists(file_path):
            return "შეცდომა: ფაილი ვერ მოიძებნა."

        try:
            if file_path.endswith('.pdf'):
                if not pypdf:
                    return "შეceდომა: pypdf ბიბლიოთეკა არ არის დაინსტალირებული."
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            else:
                return "მხოლოდ .pdf და .txt ფორმატებია მხარდაჭერილი."
        except Exception as e:
            return f"ფაილის წაკითხვის შეცდომა: {str(e)}"

        return text.strip()

    def summarize_and_translate(self, text, target_language="Georgian"):
        """Gemini AI-ით ტექსტის დაკონსპექტება და თარგმნა"""
        if not text:
            return "ტექსტი ცარიელია."

        # იღებს მხოლოდ პირველ 4000 სიმბოლოს სწრაფი დამუშავებისთვის
        trimmed_text = text[:4000]

        prompt = (
            f"Analyze and summarize the following document content.\n"
            f"Provide a concise summary in bullet points in {target_language}.\n"
            f"Highlight key facts, takeaways, and insights.\n\n"
            f"Document Text:\n{trimmed_text}"
        )

        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        endpoint = f"{self.api_url}?key={self.api_key}"

        try:
            response = requests.post(endpoint, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"AI შეცდომა (Status {response.status_code}): ვერ მოხერხდა რეზიუმირება."
        except Exception as e:
            return f"ქსელური შეცდომა: {str(e)}"
