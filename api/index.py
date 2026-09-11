import os
import io
from fastapi import FastAPI, UploadFile, File, Form
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

# OpenAI API Key ხმის ამოცნობისთვის (Whisper)
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
        audio_file.name = "audio.wav"

        # 1. ხმის ტექსტად გარდაქმნა Whisper-ის საშუალებით
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=src_lang if src_lang != 'zh-CN' else 'zh'
        )
        extracted_text = transcript.text

        if not extracted_text.strip():
            return {"extracted_text": "", "translated_text": ""}

        # 2. ტექსტის თარგმნა (GPT-4o / GPT-3.5)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate from {src_lang} to {target_lang} accurately."},
                {"role": "user", "content": extracted_text}
            ]
        )
        translated_text = response.choices[0].message.content.strip()

        return {
            "extracted_text": extracted_text,
            "translated_text": translated_text
        }
    except Exception as e:
        return {"error": str(e)}, 500
