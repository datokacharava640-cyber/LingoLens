from fastapi import FastAPI, File, Form, UploadFile
import google.generativeai as genai

app = FastAPI()

# ჩასვი შენი რეალური Google Gemini API გასაღები აქ:
genai.configure(api_key="ჩასვი_შენი_gemini_api_key_აქ")

@app.post("/translate")
async def translate_text(data: dict):
    text = data.get("text", "")
    target_lang = data.get("target_lang", "en")
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Translate the following text to {target_lang}: {text}"
    response = model.generate_content(prompt)
    
    translated = response.text if response and response.text else text
    
    return {"translated_text": translated}

@app.post("/translate-image")
async def translate_image(file: UploadFile = File(...), target_lang: str = Form("ka")):
    contents = await file.read()
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    image_part = {"mime_type": file.content_type, "data": contents}
    response = model.generate_content([image_part, f"Extract text from this image and translate it to {target_lang}."])
    
    translated = response.text if response and response.text else "სურათი ვერ დამუშავდა"
    
    return {"translated_text": translated}
