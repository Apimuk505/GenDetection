import os
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import random
load_dotenv()

AIORNOT_API_KEY = os.getenv("AIORNOT_API_KEY", "")
AIORNOT_URL = "https://api.aiornot.com/v1/reports/image"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post("/analyse")
async def analyse(file: UploadFile = File(...)):
    if not AIORNOT_API_KEY or AIORNOT_API_KEY.startswith("ใส่"):
        raise HTTPException(status_code=500, detail="Internal server error (configuration missing)")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large (max 20 MB)")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                AIORNOT_URL,
                headers={"Authorization": f"Bearer {AIORNOT_API_KEY}"},
                files={"object": (file.filename, content, file.content_type)},
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # ซ่อนว่ามีการเรียก API ออกไปข้างนอก
            raise HTTPException(status_code=e.response.status_code, detail="Analysis failed. Please try again.")
        except httpx.RequestError:
            # ซ่อนคำว่า detection service
            raise HTTPException(status_code=502, detail="Analysis engine is currently offline. Please try again later.")

    data = resp.json()
    report = data.get("report", data)

    verdict = (report.get("verdict") or "").lower()
    is_ai = verdict == "ai"
    ai_conf = report.get("ai", {}).get("confidence", 1.0 if is_ai else 0.0)
    pct = round(ai_conf * 100)
    

    ran = random.randint(10,20)
    pct = min(pct, 70+70*(ran / 100))
    return {
        "is_ai": is_ai,
        "ai_pct": pct,
        "verdict": "AI Generated" if is_ai else "Likely Real",
    }
