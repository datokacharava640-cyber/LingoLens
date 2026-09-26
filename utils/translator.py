import requests
import json
import os
import config

def translate_text(prompt, original_text, src_lang, target_lang, callback):
    """ტექსტის თარგმნა Gemini API-ს ან Vercel ბექენდის გავლით"""
    try:
        api_key = getattr(config, 'GEMINI_API_KEY', '')
        
        # თუ ბექენდია ჩართული
        if getattr(config, 'BACKEND_URL', ''):
            url = config.BACKEND_URL
            res = requests.post(url, json={"prompt": prompt}, timeout=15)
            res_data = res.json()
            result = res_data.get("result", "ვერ მოხერხდა პასუხის მიღება")
            callback(result)
            return

        # პირდაპირი API მოთხოვნა თუ გასაღები არსებობს
        if api_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json"}
            
            res = requests.post(url, json=payload, headers=headers, timeout=15)
            res_data = res.json()
            
            if "candidates" in res_data and res_data["candidates"]:
                parts = res_data["candidates"][0].get("content", {}).get("parts", [])
                if parts:
                    callback(parts[0].get("text", ""))
                    return
        
        callback("შეცდომა: API Key ან Backend URL არ არის მითითებული.")
    except Exception as e:
        callback(f"ქსელური შეცდომა: {str(e)}")

def analyze_image_and_translate(image_path, target_lang, callback):
    """სურათიდან ტექსტის ამოცნობა და თარგმნა"""
    try:
        # აქ შეგიძლიათ დაამატოთ OCR ლოგიკა ან გააგზავნოთ სურათი ბექენდზე
        callback("სურათის ანალიზის მოდული მზად არის.")
    except Exception as e:
        callback(f"OCR შეცდომა: {str(e)}")
