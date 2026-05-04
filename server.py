from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import sqlite3
import os

app = FastAPI()

# ✅ Bunları birazdan Gumroad'dan alıp dolduracağız
GUMROAD_PRODUCT_ID = "BURAYA_PRODUCT_ID"
GUMROAD_API_KEY = "BURAYA_GUMROAD_API_KEY"

class LicenseRequest(BaseModel):
    license_key: str
    hardware_id: str

# ✅ Render uyumlu veritabanı
conn = sqlite3.connect("licenses.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS licenses (
    license_key TEXT PRIMARY KEY,
    hardware_id TEXT
)
""")
conn.commit()

@app.get("/")
def root():
    return {"durum": "Blackjack Lisans Sunucu Çalışıyor ✅"}

@app.post("/verify")
def verify_license(data: LicenseRequest):

    # 1️⃣ Gumroad doğrulama
    gumroad_response = requests.post(
        "https://api.gumroad.com/v2/licenses/verify",
        data={
            "product_id": GUMROAD_PRODUCT_ID,
            "license_key": data.license_key
        }
    )

    gumroad_data = gumroad_response.json()

    if not gumroad_data.get("success"):
        raise HTTPException(status_code=400, detail="Geçersiz lisans")

    # 2️⃣ Daha önce aktive edilmiş mi kontrol
    cursor.execute(
        "SELECT hardware_id FROM licenses WHERE license_key=?",
        (data.license_key,)
    )
    result = cursor.fetchone()

    if result:
        # Lisans daha önce kullanılmış
        if result[0] == data.hardware_id:
            return {"valid": True}
        else:
            raise HTTPException(
                status_code=403,
                detail="Bu lisans başka bilgisayarda aktif"
            )
    else:
        # İlk aktivasyon
        cursor.execute(
            "INSERT INTO licenses (license_key, hardware_id) VALUES (?, ?)",
            (data.license_key, data.hardware_id)
        )
        conn.commit()
        return {"valid": True}