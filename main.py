from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from ocr_service import process_image_ocr

# თუ იყენებ სხვა ფაილებს, შეგიძლია აქედანვე დააკავშირო:
# from languages import get_supported_languages
# from offline_engine import process_offline_ocr

app = FastAPI(title="LingoLens API", version="1.0")

# CORS-ის ჩართვა მობილური აპლიკაციისა და ვებ კლიენტებისთვის
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "LingoLens სერვერი წარმატებით მუშაობს!"}

@app.post("/translate-image/")
async def translate_image(
    file: UploadFile = File(...),
    source_lang: str = Form("eng"),
    target_lang: str = Form("ka")
):
    contents = await file.read()
    # ოკრ-ისა და თარგმნის პროცესის გამოძახება ocr_service-დან
    result = process_image_ocr(contents, source_lang, target_lang)
    return result

# აქ შეგიძლია დაამატო სხვა როუტერებიც (მაგალითად ენების სიისთვის)
# @app.get("/languages")
# def supported_languages():
#     return get_supported_languages()
