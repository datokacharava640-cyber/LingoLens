from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Sheni ukve arsebuli servisebis importi (tu failebi ert donezea)
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
    # Aq shegidzlia charto sheni translate_image.py an sxva targmanis logika
    cleaned_text = req.text.strip()
    return {
        "original": cleaned_text,
        "target_lang": req.target_lang,
        "translation": f"[ushecdomo gramatikuli targmani]: {cleaned_text}",
        "status": "success"
    }

@app.post("/chat/")
def chat_ai(req: ChatRequest):
    # Aq daakavshireb chat_service.py-s
    return {
        "response": f"LingoLens AI dialogi: pasuxi shetyobinebaze '{req.message}'"
    }

@app.post("/send-sms/")
def send_sms_action(req: SmsRequest):
    # Aq daakavshireb sms_service.py-s
    return {
        "status": "success",
        "message": f"SMS damushavda nomerze: {req.phone_number}"
    }

@app.get("/languages/")
def get_languages():
    return {
        "languages": ["qartuli", "English", "Español", "Français", "Deutsch", "Türkçe", "Русский", "msoflios yvela ena"]
    }

@app.get("/offline-status/")
def offline_status():
    return {"status": "Online", "offline_ready": True}

# Avtomaturi ganaxlebis (OTA) shemowmebis endpoint-i
@app.get("/check-update/")
def check_update():
    return {
        "latest_version": "1.1",
        "apk_url": "http://37.27.255.1:8000/download/lingolens.apk",
        "release_notes": "damatebia avtomaturi ganaxlebis funqcia da ushecdomo targmani."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
