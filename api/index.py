from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from gtts import gTTS
import base64
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

@app.get("/")
@app.get("/api/index")
def root_check():
    return {"status": "online", "message": "LingoLens API is running successfully!"}

@app.post("/api/index")
def translate(req: TranslationRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        # ენის 2-ასოიანი კოდის უზრუნველყოფა
        src = req.source_lang.split("_")[0].lower() if req.source_lang != "auto" else "auto"
        tgt = req.target_lang.split("_")[0].lower()

        # თარგმნა deep-translator-ით (უფასო და სტაბილური)
        translated_text = GoogleTranslator(source=src, target=tgt).translate(req.text)

        # გრამატიკული რეჟიმის იმიტაცია / დამუშავება
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
