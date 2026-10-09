from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

API_SECRET_KEY = "lingolens-secret-key-2026"

@app.post("/api/v1/process")
async def process_data(x_api_key: str = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized API Key")
    return {"status": "success", "message": "მონაცემები წარმატებით დამუშავდა!"}
