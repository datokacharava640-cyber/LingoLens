import os
import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import openai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

@app.post("/stt-translate")
async def stt_translate(
    file: UploadFile = File(...),
    src_lang: str = Form(...),
    target_lang: str = Form(...)
):
    try:
        audio_bytes = await file.read()
        audio_file = io.BytesIO(audio_bytes)
        
        # ინარჩუნებს ატვირთული ფაილის სახელს ან ნაგულისხმევად ანიჭებს "audio.wav"-ს
        audio_file.name = file.filename or "audio.wav"

        # ენის კოდის ISO 639-1 ფორმატში გადაყვანა (მაგ. zh-CN -> zh, ka-GE -> ka)
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
                    "content": f"You are a professional translator. Translate the given text accurately from language '{src_lang}' to '{target_lang}'. Do not add commentary or notes."
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
