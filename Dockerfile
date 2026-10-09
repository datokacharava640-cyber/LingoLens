FROM python:3.11-slim

# ვამონტაჟებთ სისტემურ პაკეტებს და Tesseract OCR-ს
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ვამატებთ და ვპაკეტებთ დამოკიდებულებებს
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ვქაჩავთ პროექტის დანარჩენ ფაილებს
COPY . .

# სერვერის გაშვება Hetzner-ისთვის (8000 პორტზე და server.py ფაილით)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
