from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ocr_service import process_image_ocr
from chat_service import process_chat_message
from sms_service import send_sms_notification
import translate_image  # დამატებულია ახალი მოდული

# დამატებითი მოდულები
import languages
import offline_engine

app = FastAPI(title="LingoLens API", version="1.0")

# CORS-ის დაშვება მობილური და ვებ კლიენტებისთვის
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class SmsRequest(BaseModel):
    phone_number: str
    text: str

@app.get("/")
def read_root():
    return {"message": "LingoLens სერვერი წარმატებით მუშაობს!"}

@app.post("/translate-image/")
async def translate_image_endpoint(
    file: UploadFile = File(...),
    source_lang: str = Form("eng"),
    target_lang: str = Form("ka")
):
    contents = await file.read()
    # შეგიძლიათ გამოიყენოთ ან ocr_service ან translate_image მოდული, 
    # იმის მიხედვით თუ სად რა ფუნქცია გაქვთ გაწერილი:
    try:
        if hasattr(translate_image, "process_image"):
            return translate_image.process_image(contents, source_lang, target_lang)
    except Exception:
        pass
    return process_image_ocr(contents, source_lang, target_lang)

@app.post("/chat/")
async def chat_endpoint(request: ChatRequest):
    return process_chat_message(request.message)

@app.post("/send-sms/")
async def send_sms_endpoint(request: SmsRequest):
    return send_sms_notification(request.phone_number, request.text)

# ენების სიის მიღების ენდპოინტი
@app.get("/languages/")
def get_supported_languages():
    try:
        return {"success": True, "languages": languages.get_languages()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ოფლაინ ძრავის სტატუსის ან დამუშავების ენდპოინტი
@app.get("/offline-status/")
def offline_status():
    try:
        return {"success": True, "status": offline_engine.check_status()}
    except Exception as e:
        return {"success": False, "error": str(e)}
