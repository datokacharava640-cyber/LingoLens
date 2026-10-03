from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from ocr_service import process_image_ocr

app = FastAPI()

# CORS-ის ჩართვა მობილური და ვებ კლიენტებისთვის
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/translate-image/")
async def translate_image(
    file: UploadFile = File(...),
    source_lang: str = Form("eng"),
    target_lang: str = Form("ka")
):
    contents = await file.read()
    result = process_image_ocr(contents, source_lang, target_lang)
    return result
