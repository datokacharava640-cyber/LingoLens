from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# შენი უკვე არსებული სერვისების იმპორტი (თუ ფაილები ერთ დონეზეა)
# import chat_service
# import ocr_service
# import sms_service

app = FastAPI(title="LingoLens Hetzner Backend", version="2.0")

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
    return {"status": "LingoLens Hetzner Server is running perfectly!"}

@app.post("/translate/")
def translate_text(req: TranslateRequest):
    # აქ შეგიძლია ჩართო შენი translate_image.py ან სხვა თარგმანის ლოგიკა
    cleaned_text = req.text.strip()
    return {
        "original": cleaned_text,
        "target_lang": req.target_lang,
        "translation": f"[უშეცდომო გრამატიკული თარგმანი]: {cleaned_text}",
        "status": "success"
    }

@app.post("/chat/")
def chat_ai(req: ChatRequest):
    # აქ დააკავშირებ chat_service.py-ს
    return {
        "response": f"LingoLens AI დიალოგი: პასუხი შეტყობინებაზე '{req.message}'"
    }

@app.post("/send-sms/")
def send_sms_action(req: SmsRequest):
    # აქ დააკავშირებ sms_service.py-ს
    return {
        "status": "success",
        "message": f"SMS დამუშავდა ნომერზე: {req.phone_number}"
    }

@app.get("/languages/")
def get_languages():
    return {
        "languages": ["ქართული", "English", "Español", "Français", "Deutsch", "Türkçe", "Русский", "მსოფლიოს ყველა ენა"]
    }

@app.get("/offline-status/")
def offline_status():
    return {"status": "Online", "offline_ready": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
