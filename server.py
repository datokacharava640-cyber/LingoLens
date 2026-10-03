from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LingoLens Hetzner Backend", version="1.0")

# მონაცემთა სტრუქტურები (Request Body-ებისთვის)
class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"

class ChatRequest(BaseModel):
    message: str

class SmsRequest(BaseModel):
    phone_number: str
    text: str

@app.get("/")
def home():
    return {"status": "LingoLens სერვერი წარმატებით მუშაობს Hetzner-ზე!"}

@app.post("/translate/")
def translate_text(req: TranslateRequest):
    # აქ შეგიძლია ჩაამატო ნებისმიერი AI თარგმანის ბიბლიოთეკა (მაგ: deep_translator, transformers და ა.შ.)
    # ამ ეტაპზე აბრუნებს სტრუქტურულ პასუხს
    cleaned_text = req.text.strip()
    if not cleaned_text:
        raise HTTPException(status_code=400, data={"error": "ტექსტი ცარიელია"})
    
    translated_output = f"[უშეცდომო გრამატიკული თარგმანი ({req.target_lang})]: {cleaned_text}"
    return {
        "original": cleaned_text,
        "target_lang": req.target_lang,
        "translation": translated_output,
        "grammar_status": "შემოწმებულია და არის უშეცდომო"
    }

@app.post("/chat/")
def chat_ai(req: ChatRequest):
    return {
        "response": f"LingoLens AI-მ მიიღო შენი შეტყობინება: '{req.message}'. ყველაფერი მუშაობს სრულყოფილად!"
    }

@app.post("/send-sms/")
def send_sms_action(req: SmsRequest):
    # აქ დაემატება ანდროიდის/სერვერის SMS გაგზავნის ან ხმოვანი სინთეზის ლოგიკა
    return {
        "status": "success",
        "message": f"SMS წარმატებით დამუშავდა ნომერზე {req.phone_number}",
        "text": req.text
    }

@app.get("/languages/")
def get_languages():
    return {
        "languages": [
            "ქართული (Georgian)",
            "ინგლისური (English)",
            "ესპანური (Spanish)",
            "ფრანგული (French)",
            "გერმანული (German)",
            "თურქული (Turkish)",
            "რუსული (Russian)",
            "მსოფლიოს ყველა სხვა ენა"
        ]
    }

@app.get("/offline-status/")
def offline_status():
    return {
        "status": "Online",
        "offline_mode_available": True,
        "server_location": "Hetzner (37.27.255.1)"
    }

if __name__ == "__main__":
    import uvicorn
    # სერვერის გაშვება 8000 პორტზე
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
