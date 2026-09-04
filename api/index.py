from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from gtts import gTTS
import io

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
def text_to_speech(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        lang = req.lang.split("_")[0].lower()
        
        # gTTS ქართულ ენას (ka) სრულად უჭერს მხარს
        tts = gTTS(text=req.text, lang=lang, slow=False)
        
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        return Response(content=fp.read(), media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
