from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

app = FastAPI(
    title="Global Server Core",
    description="Enterprise-grade autonomous server",
    version="1.0.0",
)

# ავტორიზაციის ჰედერი და დაშვებული გასაღებები
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# აქ ვწერთ ყველა იმ სანდო გასაღებს, რომელთა გამოყენების უფლებაც აქვთ მოწყობილობებს
VALID_API_KEYS = {"lingolens-secret-key-2026", "global-device-key-xyz"}


def verify_api_key(api_key: str = Security(api_key_header)):
  if api_key in VALID_API_KEYS:
    return api_key
  raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Access denied: Invalid or missing API Key",
  )


@app.get("/")
def health_check():
  return {"status": "online", "system": "operational"}


@app.post("/api/v1/process")
def process_data(data: dict, api_key: str = Security(verify_api_key)):
  # ეს არის დაცული ადგილი, სადაც ნებისმიერი მოწყობილობა გამოგზავნის მონაცემებს
  return {
      "status": "success",
      "message": (
          "Data received and processed seamlessly without interruption"
      ),
      "payload": data,
  }
