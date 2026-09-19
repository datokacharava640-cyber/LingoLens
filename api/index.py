import os
import io
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import openai
import google.generativeai as genai

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="LingoLens AI Engine")
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

MAX_FILE_SIZE = 5 * 1024 * 1024


@app.post("/translate-text")
@limiter.limit("40/minute")
async def translate_text(
    request: Request,
    text: str = Form(...),
    src_lang: str = Form("auto"),
    target_lang: str = Form(...)
):
    if not text.strip():
        return {"translated_text": ""}

    src_instruction = f"from '{src_lang}'" if src_lang != "auto" else "by auto-detecting the source language"
    prompt = f"Translate the given text {src_instruction} to '{target_lang}'. Ensure the translation is grammatically flawless and fluent. Output ONLY the translated text without commentary:\n\n{text}"

    # 1. სცადე OpenAI
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return {"translated_text": response.choices[0].message.content.strip()}
        except Exception as e:
            print(f"[OpenAI Fallback Triggered]: {e}")

    # 2. Fallback Gemini AI-ზე
    if gemini_model:
        try:
            res = gemini_model.generate_content(prompt)
            return {"translated_text": res.text.strip()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini error: {e}")

    raise HTTPException(status_code=500, detail="No AI service available.")


@app.post("/explain-grammar")
@limiter.limit("20/minute")
async def explain_grammar(
    request: Request,
    text: str = Form(...),
    target_lang: str = Form("ka")
):
    """ფუნქცია: გრამატიკული ანალიზი და განმარტება"""
    if not text.strip():
        return {"explanation": ""}

    prompt = (
        f"Analyze the grammar, structure, and key vocabulary of the following text: '{text}'. "
        f"Provide a clear, brief, educational explanation in language code '{target_lang}'. "
        f"Keep it well-formatted with bullet points."
    )

    if client:
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            return {"explanation": res.choices[0].message.content.strip()}
        except Exception:
            pass

    if gemini_model:
        try:
            res = gemini_model.generate_content(prompt)
            return {"explanation": res.text.strip()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=500, detail="Grammar AI unavailable.")


@app.post("/stt-translate")
@limiter.limit("30/minute")
async def stt_translate(
    request: Request,
    file: UploadFile = File(...),
    src_lang: str = Form("auto"),
    target_lang: str = Form(...)
):
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Audio file too large.")

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = file.filename or "audio.wav"

        whisper_lang = src_lang.split('-')[0].lower() if src_lang and src_lang != "auto" else None

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=whisper_lang
        )
        extracted_text = transcript.text

        if not extracted_text.strip():
            return {"extracted_text": "", "translated_text": ""}

        src_instruction = f"from '{src_lang}'" if src_lang != "auto" else "by auto-detecting language"
        trans_res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": f"Translate accurately {src_instruction} to '{target_lang}'. Ensure high grammatical accuracy. Output only translation."
            }, {"role": "user", "content": extracted_text}],
            temperature=0.3
        )
        
        return {
            "extracted_text": extracted_text,
            "translated_text": trans_res.choices[0].message.content.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr-translate")
@limiter.limit("20/minute")
async def ocr_translate(
    request: Request,
    file: UploadFile = File(...),
    target_lang: str = Form(...)
):
    try:
        image_bytes = await file.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Detect text and translate to '{target_lang}'. Ensure grammatically correct translation. Respond as:\nEXTRACTED: <text>\nTRANSLATED: <translation>"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()
        
        extracted, translated = "", ""
        for line in content.split("\n"):
            if "EXTRACTED:" in line:
                extracted = line.split("EXTRACTED:", 1)[1].strip()
            elif "TRANSLATED:" in line:
                translated = line.split("TRANSLATED:", 1)[1].strip()

        return {"extracted_text": extracted, "translated_text": translated or content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
