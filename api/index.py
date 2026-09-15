import os
import io
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import openai

# Rate Limiter-ის ინიციალიზაცია (IP-ზე დაფუძნებით)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit Vercel-ის Timeout-ის თავიდან ასაცილებლად


@app.post("/stt-translate")
@limiter.limit("30/minute")
async def stt_translate(
    request: Request,
    file: UploadFile = File(...),
    src_lang: str = Form(...),
    target_lang: str = Form(...)
):
    try:
        audio_bytes = await file.read()

        # ფაილის ზომის შემოწმება (მაქს. 5MB)
        if len(audio_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file size exceeds 5MB limit."
            )

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = file.filename or "audio.wav"

        # ენის კოდის ISO 639-1 ფორმატში გადაყვანა (მაგ. zh-CN -> zh)
        whisper_lang = src_lang.split('-')[0].lower() if src_lang else None

        # 1. ხმის ტექსტად გარდაქმნა Whisper-ით
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=whisper_lang
        )
        extracted_text = transcript.text

        if not extracted_text.strip():
            return {"extracted_text": "", "translated_text": ""}

        # 2. ტექსტის თარგმნა GPT-4o-mini-თ
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate the given text accurately from '{src_lang}' to '{target_lang}'. Return only the translation, no commentary."
                },
                {"role": "user", "content": extracted_text}
            ],
            temperature=0.3
        )
        translated_text = response.choices[0].message.content.strip()

        return {
            "extracted_text": extracted_text,
            "translated_text": translated_text
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/translate-text")
@limiter.limit("40/minute")
async def translate_text(
    request: Request,
    text: str = Form(...),
    src_lang: str = Form(...),
    target_lang: str = Form(...)
):
    """პირდაპირი ტექსტის თარგმნა"""
    try:
        if not text.strip():
            return {"translated_text": ""}

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a translator. Translate text accurately from '{src_lang}' to '{target_lang}'. Output only translated text."
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return {"translated_text": response.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/ocr-translate")
@limiter.limit("20/minute")
async def ocr_translate(
    request: Request,
    file: UploadFile = File(...),
    target_lang: str = Form(...)
):
    """Live OCR — ფოტოდან ტექსტის ამოცნობა და თარგმნა Vision მოდელით"""
    try:
        image_bytes = await file.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extract any text visible in this image and translate it to '{target_lang}'. "
                                    f"Respond strictly in this format:\nEXTRACTED: <original text>\nTRANSLATED: <translated text>"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()
        
        extracted = ""
        translated = ""

        for line in content.split("\n"):
            if line.startswith("EXTRACTED:"):
                extracted = line.replace("EXTRACTED:", "").strip()
            elif line.startswith("TRANSLATED:"):
                translated = line.replace("TRANSLATED:", "").strip()

        return {
            "extracted_text": extracted,
            "translated_text": translated or content
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
