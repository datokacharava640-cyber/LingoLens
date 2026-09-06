import io
import asyncio
import re
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from deep_translator import GoogleTranslator
import edge_tts
from PIL import Image
import pytesseract

app = FastAPI(title="LingoLens API")

# CORS კონფიგურაცია
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

# გაფართოებული მსოფლიო ენების ხმების რუკა Edge-TTS-ისთვის
VOICE_MAPPING = {
    "ka": "ka-GE-EkaNeural",       # ქართული
    "en": "en-US-AriaNeural",      # ინგლისური
    "ru": "ru-RU-SvetlanaNeural",  # რუსული
    "de": "de-DE-KatjaNeural",     # გერმანული
    "fr": "fr-FR-DeniseNeural",    # ფრანგული
    "es": "es-ES-ElviraNeural",    # ესპანური
    "it": "it-IT-ElsaNeural",      # იტალიური
    "pt": "pt-BR-FranciscaNeural", # პორტუგალიური
    "zh": "zh-CN-XiaoxiaoNeural",  # ჩინური (მანდარინი)
    "ja": "ja-JP-NanamiNeural",    # იაპონური
    "ko": "ko-KR-SunHiNeural",     # კორეული
    "ar": "ar-SA-ZariyahNeural",   # არაბული
    "tr": "tr-TR-AhmetNeural",     # თურქული
    "uk": "uk-UA-PolinaNeural",    # უკრაინული
    "el": "el-GR-AthinaNeural",    # ბერძნული
    "he": "he-IL-AvriNeural",      # ებრაული
    "hi": "hi-IN-SwaraNeural",     # ჰინდი
    "nl": "nl-NL-ColetteNeural",   # ჰოლანდიური
    "pl": "pl-PL-ZofiaNeural",     # პოლონური
    "sv": "sv-SE-SofieNeural",     # შვედური
    "az": "az-AZ-BanuNeural",      # აზერბაიჯანული
    "hy": "hy-AM-AnahitNeural",    # სომხური
}

# Tesseract OCR ენების შესაბამისობის რუკა
OCR_LANG_MAPPING = {
    "ka": "kat",
    "en": "eng",
    "ru": "rus",
    "de": "deu",
    "fr": "fra",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "zh": "chi_sim",
    "ja": "jpn",
    "ko": "kor",
    "ar": "ara",
    "tr": "tur",
    "uk": "ukr",
    "el": "ell",
    "he": "heb",
    "hi": "hin",
    "nl": "nld",
    "pl": "pol",
    "sv": "swe",
    "az": "aze",
    "hy": "hye",
}

def analyze_grammar(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    ატარებს მსოფლიო ენებისა და ქართული ტექსტის გრამატიკულ და სტრუქტურულ ანალიზს
    """
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    # წინადადებების დათვლა სასვენი ნიშნების მიხედვით
    sentences = [s for s in re.split(r'[\.\!\?\n]+', text) if s.strip()]
    sentence_count = len(sentences) if sentences else 1

    analysis_lines = [
        f"📊 [გრამატიკული და სტრუქტურული ანალიზი]",
        f"• მიმართულება: {src_lang.upper()} ➔ {tgt_lang.upper()}",
        f"• სიტყვების რაოდენობა: {word_count}",
        f"• სიმბოლოების რაოდენობა: {char_count}",
        f"• წინადადებების რაოდენობა: {sentence_count}",
        f"• საშუალო სიტყვის სიგრძე: {round(char_count / word_count, 1) if word_count else 0} სიმბოლო"
    ]

    # ქართული ენისთვის სპეციფიკური ანალიზი
    if src_lang == "ka":
        vowels = "აეიოუ"
        ka_vowel_count = sum(1 for char in text if char in vowels)
        analysis_lines.append(f"• ხმოვნების რაოდენობა (ქართული): {ka_vowel_count}")

    return "\n".join(analysis_lines)

@app.get("/")
@app.get("/api/index")
async def root_check():
    return {"status": "online", "message": "LingoLens API is running successfully!"}

@app.post("/api/index")
async def translate(req: TranslationRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        src = req.source_lang.split("_")[0].lower() if req.source_lang != "auto" else "auto"
        tgt = req.target_lang.split("_")[0].lower()

        translator = GoogleTranslator(source=src, target=tgt)
        translated_text = translator.translate(req.text)

        grammar_analysis = ""
        if req.mode == "grammar":
            grammar_analysis = analyze_grammar(req.text, src, tgt)

        return {
            "translated_text": translated_text,
            "grammar_analysis": grammar_analysis,
            "source_lang": src,
            "target_lang": tgt
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

@app.post("/api/tts")
async def text_to_speech(req: TTSRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        lang = req.lang.split("_")[0].lower()
        voice = VOICE_MAPPING.get(lang, "en-US-AriaNeural")

        communicate = edge_tts.Communicate(req.text, voice)
        mp3_fp = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_fp.write(chunk["data"])

        mp3_fp.seek(0)
        return Response(content=mp3_fp.getvalue(), media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.post("/api/ocr_translate")
async def ocr_translate(
    file: UploadFile = File(...),
    source_lang: str = Form("auto"),
    target_lang: str = Form("en")
):
    """
    იღებს ფოტოს, ამოიცნობს ტექსტს მრავალენოვანი OCR მხარდაჭერით და თარგმნის
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="ატვირთული ფაილი უნდა იყოს სურათი (image/*)")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        src = source_lang.split("_")[0].lower() if source_lang != "auto" else "auto"
        tgt = target_lang.split("_")[0].lower()

        # განვსაზღვროთ OCR ენა (თუ auto-ზეა, ნაგულისხმევად იყენებს eng+kat+rus)
        ocr_lang = OCR_LANG_MAPPING.get(src, "eng+kat+rus")

        try:
            ocr_text = pytesseract.image_to_string(image, lang=ocr_lang)
        except Exception:
            ocr_text = pytesseract.image_to_string(image, lang="eng")

        if not ocr_text.strip():
            return {
                "original_text": "",
                "translated_text": "[ფოტოზე ტექსტი ვერ ამოიცნო]",
                "grammar_analysis": "",
                "source_lang": src,
                "target_lang": tgt
            }

        translator = GoogleTranslator(source=src, target=tgt)
        translated_text = translator.translate(ocr_text)
        grammar_analysis = analyze_grammar(ocr_text, src, tgt)

        return {
            "original_text": ocr_text.strip(),
            "translated_text": translated_text,
            "grammar_analysis": grammar_analysis,
            "source_lang": src,
            "target_lang": tgt
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR Translation Error: {str(e)}")
