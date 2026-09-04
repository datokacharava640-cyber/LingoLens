import io
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from deep_translator import GoogleTranslator
import edge_tts

app = FastAPI()

# CORS ნებართვები
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "en"
    mode: str = "standard"

class TTSRequest(BaseModel):
    text: str
    lang: str = "ka"

# ენების ხმების რუკა Edge-TTS-ისთვის
VOICE_MAPPING = {
    "ka": "ka-GE-EkaNeural",       # ქართული (ქალი)
    "en": "en-US-AriaNeural",      # ინგლისური
    "ru": "ru-RU-SvetlanaNeural",  # რუსული
    "de": "de-DE-KatjaNeural",     # გერმანული
    "fr": "fr-FR-DeniseNeural",    # ფრანგული
    "es": "es-ES-ElviraNeural",    # ესპანური
    "tr": "tr-TR-AhmetNeural",     # თურქული
    "uk": "uk-UA-PolinaNeural",    # უკრაინული
}

@app.get("/")
@app.get("/api/index")
def root_check():
    return {"status": "online", "message": "LingoLens API is running successfully!"}

@app.post("/api/index")
def translate(req: TranslationRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        src = req.source_lang.split("_")[0].lower() if req.source_lang != "auto" else "auto"
        tgt = req.target_lang.split("_")[0].lower()

        translated_text = GoogleTranslator(source=src, target=tgt).translate(req.text)

        grammar_analysis = ""
        if req.mode == "grammar":
            grammar_analysis = f"სიტყვების რაოდენობა: {len(req.text.split())} | ენა: {src.upper()} -> {tgt.upper()}"

        return {
            "translated_text": translated_text,
            "grammar_analysis": grammar_analysis,
            "source_lang": src,
            "target_lang": tgt
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
async def text_to_speech(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        lang = req.lang.split("_")[0].lower()
        
        # თუ ენა რუკაშია აირჩევს შესაბამის ხმას, თუ არა - ნაგულისხმევად ინგლისურს
        voice = VOICE_MAPPING.get(lang, "en-US-AriaNeural")

        communicate = edge_tts.Communicate(req.text, voice)
        
        mp3_fp = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_fp.write(chunk["data"])

        mp3_fp.seek(0)
        return Response(content=mp3_fp.read(), media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
