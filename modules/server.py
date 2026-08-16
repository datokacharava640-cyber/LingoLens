import os
import json
import base64
import requests
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LingoLens Advanced Proxy")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

class ImageRequest(BaseModel):
    image_b64: str

@app.post("/translate-ar")
def translate_ar_overlay(req: ImageRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API Key not set.")

    # 1. Base64 -> OpenCV Image
    img_bytes = base64.b64decode(req.image_b64)
    nparr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 2. Get text and bounding boxes from Gemini
    prompt = (
        "Detect all text blocks in this image. Translate them to Georgian/English.\n"
        "Return ONLY a JSON list of objects, each containing: "
        "'original', 'translation', 'box_2d': [ymin, xmin, ymax, xmax] (normalized 0-1000)."
    )
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": req.image_b64}}
            ]
        }],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    res = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload, timeout=20)
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail="Gemini Vision Error")

    data = json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'])
    h, w, _ = image.shape

    # 3. OpenCV Canvas: Draw over original text with translation
    for item in data:
        ymin, xmin, ymax, xmax = item['box_2d']
        pt1 = (int(xmin * w / 1000), int(ymin * h / 1000))
        pt2 = (int(xmax * w / 1000), int(ymax * h / 1000))
        
        # Cover original text with white box
        cv2.rectangle(image, pt1, pt2, (255, 255, 255), -1)
        # Write translated text over it
        cv2.putText(
            image, 
            item['translation'][:20], 
            (pt1[0], pt1[1] + 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (0, 0, 0), 
            2
        )

    # 4. Encode back to Base64
    _, buffer = cv2.imencode('.jpg', image)
    processed_b64 = base64.b64encode(buffer).decode('utf-8')
    return {"ar_image_b64": processed_b64}
