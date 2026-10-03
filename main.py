from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ocr_service import process_image_ocr
from chat_service import process_chat_message
from sms_service import send_sms_notification

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
async def translate_image(
    file: UploadFile = File(...),
    source_lang: str = Form("eng"),
    target_lang: str = Form("ka")
):
    contents = await file.read()
    return process_image_ocr(contents, source_lang, target_lang)

@app.post("/chat/")
async def chat_endpoint(request: ChatRequest):
    return process_chat_message(request.message)

@app.post("/send-sms/")
async def send_sms_endpoint(request: SmsRequest):
    return send_sms_notification(request.phone_number, request.text)
