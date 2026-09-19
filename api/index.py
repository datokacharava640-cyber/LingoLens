"""
=============================================================================
PROJECT META INFORMATION & AUTHOR CREDITS
=============================================================================
Author / Developer  : Dato Kacharava
Country             : Georgia
Release Date        : September 2026
Project Name        : LingoLens AI - Academic & Translation Suite Backend
Version             : 6.0.0
=============================================================================
"""

import os
import tempfile
from typing import Optional

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import openai
import google.generativeai as genai

# ==========================================
# INITIALIZATION & CONFIGURATION
# ==========================================
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="LingoLens AI API Suite")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys setup
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    gemini_model = None


@app.get("/")
def read_root():
    return {"status": "online", "system": "LingoLens AI Hybrid Backend v6.0"}


# ==========================================
# 1. TEXT TRANSLATION ENDPOINT
# ==========================================
@app.post("/translate-text")
@limiter.limit("60/minute")
async def translate_text(
    request: Request,
    text: str = Form(...),
    src_lang: str = Form("auto"),
    target_lang: str = Form("ka")
):
    if not text.strip():
        return {"translated_text": ""}

    prompt = (
        f"Translate the following text from source language code '{src_lang}' "
        f"to target language code '{target_lang}'. Return ONLY the translation:\n\n{text}"
    )

    # 1. OpenAI Primary
    if client:
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return {"translated_text": res.choices[0].message.content.strip()}
        except Exception as e:
            print(f"[OpenAI Failover]: {e}")

    # 2. Gemini Fallback
    if gemini_model:
        try:
            res = gemini_model.generate_content(prompt)
            return {"translated_text": res.text.strip()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=500, detail="No AI Service Available")


# ==========================================
# 2. OCR TRANSLATION ENDPOINT
# ==========================================
@app.post("/ocr-translate")
@limiter.limit("30/minute")
async def ocr_translate(
    request: Request,
    file: UploadFile = File(...),
    target_lang: str = Form("ka")
):
    try:
        content = await file.read()
        
        # 1. Gemini Vision Primary
        if gemini_model:
            try:
                res = gemini_model.generate_content([
                    {"mime_type": file.content_type or "image/jpeg", "data": content},
                    f"Extract any visible text from this image and translate it to language code '{target_lang}'. "
                    f"Format output as: EXTRACTED: <text>\nTRANSLATED: <translation>"
                ])
                out = res.text.strip()
                extracted, translated = "", ""
                for line in out.splitlines():
                    if line.startswith("EXTRACTED:"):
                        extracted = line.replace("EXTRACTED:", "").strip()
                    elif line.startswith("TRANSLATED:"):
                        translated = line.replace("TRANSLATED:", "").strip()
                
                if not extracted and not translated:
                    translated = out

                return {"extracted_text": extracted, "translated_text": translated}
            except Exception as e:
                print(f"[Gemini Vision Failover]: {e}")

        # 2. OpenAI GPT-4o Vision Fallback
        if client:
            import base64
            b64_img = base64.b64encode(content).decode("utf-8")
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Extract visible text and translate to code '{target_lang}'. Return raw translated text."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }]
            )
            return {"extracted_text": "Extracted Image Text", "translated_text": res.choices[0].message.content.strip()}

        raise HTTPException(status_code=500, detail="Vision AI service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 3. STT & DIALOGUE ENDPOINTS
# ==========================================
@app.post("/stt-translate")
@limiter.limit("30/minute")
async def stt_translate(
    request: Request,
    file: UploadFile = File(...),
    src_lang: str = Form("auto"),
    target_lang: str = Form("ka")
):
    try:
        audio_data = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        extracted_text = ""
        if client:
            with open(tmp_path, "rb") as af:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=af
                )
            extracted_text = transcript.text
        os.remove(tmp_path)

        if not extracted_text:
            return {"extracted_text": "", "translated_text": ""}

        # Translate extracted speech
        tr_res = await translate_text(request, text=extracted_text, src_lang=src_lang, target_lang=target_lang)
        return {"extracted_text": extracted_text, "translated_text": tr_res.get("translated_text", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/live-dialogue")
@limiter.limit("30/minute")
async def live_dialogue(
    request: Request,
    file: UploadFile = File(...),
    lang_a: str = Form("ka"),
    lang_b: str = Form("en"),
    speaker: str = Form("A")
):
    try:
        audio_data = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        input_text = ""
        if client:
            with open(tmp_path, "rb") as af:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=af
                )
            input_text = transcript.text
        os.remove(tmp_path)

        if not input_text:
            return {"original_text": "", "translated_text": "", "speaker": speaker}

        source_lang = lang_a if speaker == "A" else lang_b
        target_lang = lang_b if speaker == "A" else lang_a

        tr_res = await translate_text(request, text=input_text, src_lang=source_lang, target_lang=target_lang)
        return {
            "speaker": speaker,
            "original_text": input_text,
            "translated_text": tr_res.get("translated_text", ""),
            "source_lang": source_lang,
            "target_lang": target_lang
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 4. GRAMMAR EXPLANATION ENDPOINT
# ==========================================
@app.post("/explain-grammar")
@limiter.limit("30/minute")
async def explain_grammar(
    request: Request,
    text: str = Form(...),
    target_lang: str = Form("ka")
):
    if not text.strip():
        return {"explanation": ""}

    prompt = (
        f"Analyze the grammar, structure, and key vocabulary of this text: '{text}'. "
        f"Provide an easy-to-understand grammar explanation in the language corresponding to code '{target_lang}'."
    )

    if client:
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return {"explanation": res.choices[0].message.content.strip()}
        except Exception as e:
            print(f"[Grammar OpenAI Fallback]: {e}")

    if gemini_model:
        try:
            res = gemini_model.generate_content(prompt)
            return {"explanation": res.text.strip()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=500, detail="Grammar AI service unavailable.")


# ==========================================
# 5. ACADEMIC & SCHOOL SUITE ENDPOINT
# ==========================================
@app.post("/academic-assistant")
@limiter.limit("20/minute")
async def academic_assistant(
    request: Request,
    task_type: str = Form(...),  # 'essay', 'summarize', 'paraphrase'
    text: str = Form(...),
    target_lang: str = Form("ka")
):
    """სტუდენტური და სასკოლო აკადემიური ასისტენტი"""
    if not text.strip():
        return {"result": ""}

    if task_type == "essay":
        prompt = (
            f"You are an academic expert. Help write a well-structured essay/assignment/topic based on: '{text}'. "
            f"Include an Introduction, Main Body Arguments, and Conclusion. "
            f"Write the response in the language corresponding to code '{target_lang}'."
        )
    elif task_type == "summarize":
        prompt = (
            f"Summarize the following text into key concepts, main ideas, and structured bullet points. "
            f"Provide the response in language code '{target_lang}':\n\n{text}"
        )
    elif task_type == "paraphrase":
        prompt = (
            f"Rewrite the following text in a professional, formal, and academic tone in language code '{target_lang}':\n\n{text}"
        )
    else:
        prompt = text

    # 1. OpenAI Primary
    if client:
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            return {"result": res.choices[0].message.content.strip()}
        except Exception as e:
            print(f"[Academic OpenAI Fallback]: {e}")

    # 2. Gemini Fallback
    if gemini_model:
        try:
            res = gemini_model.generate_content(prompt)
            return {"result": res.text.strip()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=500, detail="Academic AI service unavailable.")
