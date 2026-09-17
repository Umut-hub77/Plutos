"""
backend.py — Plutos Web (FAZ 1 iskeleti)
------------------------------------------
Bu, dashboard.py'nin (Streamlit) GERÇEK bir HTML/CSS/JS web sitesine dönüştürülme
sürecinin İLK FAZI'dır. Tüm 2500+ satırlık uygulamayı (LSTM tahmin, FIRE hesaplayıcı,
Markowitz optimizasyonu, WhatsApp botu, Backtest laboratuvarı vb.) tek seferde taşımak
yerine, önce sağlam bir temel kuruyoruz:

  ✅ Faz 1 (BU DOSYA): Gerçek giriş/kayıt (aynı SQLite veritabanı + bcrypt), Ana Sayfa
     (XU100 endeksi + en çok yükselen/düşen), salt-okunur portföy görünümü.
  ⏳ Faz 2 (sonraki adım): Emir Ver (demo), Fiyat Alarmları, İzleme Listesi.
  ⏳ Faz 3: Stratejik Analiz, Piyasa Tarayıcı, Sektör Karşılaştırma (grafikli).
  ⏳ Faz 4: AI Gelecek (LSTM), Backtest, Portföy Optimizasyonu, FIRE, WhatsApp Botu.

Neden fazlara bölünüyor: Streamlit'te "bedava" gelen şeyler (form state, session,
otomatik yeniden çizim) web'de elle (JS ile fetch/render) yazılmak zorunda. Modül
sayısı çok olduğu için hepsini aynı anda taşımak riskli; küçük, çalışan parçalar
halinde ilerlemek daha güvenli.

Çalıştırmak için:
    cd web
    pip install fastapi uvicorn
    uvicorn backend:app --reload --port 8000
Sonra tarayıcıda: http://localhost:8000
"""

import os
import sys
import secrets
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- dashboard.py ile AYNI db.py / auth_utils.py / data_engine.py'yi kullan ---
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # üst klasör (delivery/)
from db import get_user, upsert_user, init_db
from auth_utils import verify_password, hash_password, needs_rehash

import yfinance as yf


def son_gecerli_satirlar(df):
    """
    data_engine.py'deki aynı fonksiyonun bağımsız kopyası — orijinali streamlit'i
    modül seviyesinde import ettiği için (data_engine.py -> import streamlit),
    bu hafif API'de streamlit'e hiç ihtiyaç duymamak için burada tekrar tanımlandı.
    Borsa kapalıyken/seans öncesinde eklenen "taslak" (Close NaN ya da Volume 0) satırları eler.
    """
    if df is None or df.empty:
        return df
    temiz = df
    if 'Close' in temiz.columns:
        temiz = temiz[temiz['Close'].notna()]
    if 'Volume' in temiz.columns and not temiz.empty:
        gecerli_hacim = temiz[(temiz['Volume'].notna()) & (temiz['Volume'] > 0)]
        if not gecerli_hacim.empty:
            temiz = gecerli_hacim
    return temiz

app = FastAPI(title="Plutos API — Faz 1")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

init_db()

# ---------------------------------------------------------------------------
# Basit oturum yönetimi (Faz 1 için yeterli; üretimde JWT/HttpOnly cookie önerilir)
# ---------------------------------------------------------------------------
SESSIONS: dict[str, dict] = {}  # token -> {"email": ..., "exp": datetime}
SESSION_TTL_SAAT = 12


def _token_uret(email: str) -> str:
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {"email": email, "exp": datetime.utcnow() + timedelta(hours=SESSION_TTL_SAAT)}
    return token


def _oturum_dogrula(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Oturum bulunamadı, lütfen giriş yapın.")
    token = authorization.removeprefix("Bearer ").strip()
    kayit = SESSIONS.get(token)
    if not kayit or kayit["exp"] < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Oturum süresi doldu, tekrar giriş yapın.")
    return kayit["email"]


# ---------------------------------------------------------------------------
# Fiyat yardımcıları (dashboard.py'deki hizli_veri_cek ile AYNI, kanıtlanmış yöntem)
# ---------------------------------------------------------------------------
_price_cache: dict[str, tuple[datetime, object]] = {}
_CACHE_TTL_SN = 900


def _hizli_fiyat_gecmisi(sembol: str):
    simdi = datetime.utcnow()
    if sembol in _price_cache:
        zaman, veri = _price_cache[sembol]
        if (simdi - zaman).total_seconds() < _CACHE_TTL_SN:
            return veri
    try:
        hist = yf.Ticker(f"{sembol}.IS").history(period="5d")
        hist = son_gecerli_satirlar(hist)
    except Exception:
        hist = None
    _price_cache[sembol] = (simdi, hist)
    return hist


ANA_SAYFA_TARAMA_LISTESI = [
    "THYAO", "AKBNK", "GARAN", "ISCTR", "KCHOL", "SASA", "EREGL", "BIMAS", "ASELS", "TUPRS",
    "SISE", "PETKM", "FROTO", "TOASO", "TCELL", "YKBNK", "VAKBN", "HALKB", "PGSUS", "MGROS",
]


# ---------------------------------------------------------------------------
# Şemalar
# ---------------------------------------------------------------------------
class GirisIstek(BaseModel):
    email: str
    password: str


class KayitIstek(BaseModel):
    email: str
    password: str
    ad: str = ""
    soyad: str = ""


# ---------------------------------------------------------------------------
# Auth uçları
# ---------------------------------------------------------------------------
@app.post("/api/login")
def login(istek: GirisIstek):
    kullanici = get_user(istek.email.strip().lower())
    if not kullanici or not verify_password(istek.password, kullanici["password"]):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    if needs_rehash(kullanici["password"]):
        kullanici["password"] = hash_password(istek.password)
        upsert_user(istek.email.strip().lower(), kullanici)

    token = _token_uret(istek.email.strip().lower())
    return {"token": token, "ad": kullanici.get("ad", ""), "soyad": kullanici.get("soyad", "")}


@app.post("/api/register")
def register(istek: KayitIstek):
    email = istek.email.strip().lower()
    if get_user(email):
        raise HTTPException(status_code=400, detail="Bu e-posta ile zaten bir hesap var.")
    upsert_user(email, {
        "ad": istek.ad, "soyad": istek.soyad, "dt": None,
        "password": hash_password(istek.password),
        "watchlist": [], "portfolio": {},
        "virtual_cash": 100000.0, "trade_log": [], "price_alarms": [],
    })
    token = _token_uret(email)
    return {"token": token, "ad": istek.ad, "soyad": istek.soyad}


# ---------------------------------------------------------------------------
# Ana Sayfa verisi
# ---------------------------------------------------------------------------
@app.get("/api/market-overview")
def market_overview():
    endeks = {"deger": None, "degisim": None}
    hatalar = []

    idx_hist = _hizli_fiyat_gecmisi("XU100")
    if idx_hist is not None and len(idx_hist) >= 2:
        endeks["deger"] = float(idx_hist["Close"].iloc[-1])
        onceki = float(idx_hist["Close"].iloc[-2])
        endeks["degisim"] = (endeks["deger"] / onceki - 1) * 100
    else:
        hatalar.append("XU100 verisi alınamadı.")

    yukselen_dusen = []
    for s in ANA_SAYFA_TARAMA_LISTESI:
        hist = _hizli_fiyat_gecmisi(s)
        if hist is None or len(hist) < 2:
            continue
        son = float(hist["Close"].iloc[-1])
        onceki = float(hist["Close"].iloc[-2])
        if onceki <= 0:
            continue
        yukselen_dusen.append({"hisse": s, "fiyat": son, "degisim": (son / onceki - 1) * 100})

    yukselen_dusen.sort(key=lambda x: x["degisim"], reverse=True)
    return {
        "endeks": endeks,
        "en_cok_yukselen": yukselen_dusen[:5],
        "en_cok_dusen": sorted(yukselen_dusen, key=lambda x: x["degisim"])[:5],
        "hatalar": hatalar,
    }


# ---------------------------------------------------------------------------
# Portföy (salt okunur — Faz 1)
# ---------------------------------------------------------------------------
@app.get("/api/portfolio")
def portfolio(authorization: str | None = Header(default=None)):
    email = _oturum_dogrula(authorization)
    kullanici = get_user(email)
    if not kullanici:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    pozisyonlar = []
    toplam_deger = 0.0
    for hisse, poz in (kullanici.get("portfolio") or {}).items():
        hist = _hizli_fiyat_gecmisi(hisse)
        fiyat = float(hist["Close"].iloc[-1]) if hist is not None and not hist.empty else poz.get("maliyet", 0)
        deger = fiyat * poz.get("lot", 0)
        toplam_deger += deger
        pozisyonlar.append({
            "hisse": hisse, "lot": poz.get("lot", 0), "maliyet": poz.get("maliyet", 0),
            "guncel_fiyat": fiyat, "piyasa_degeri": deger,
        })

    sanal_bakiye = float(kullanici.get("virtual_cash", 100000.0))
    return {
        "virtual_cash": sanal_bakiye,
        "pozisyonlar": pozisyonlar,
        "pozisyon_degeri": toplam_deger,
        "toplam_varlik": sanal_bakiye + toplam_deger,
    }


# ---------------------------------------------------------------------------
# Statik dosyalar (frontend) — en sonda mount edilir ki /api/* önce eşleşsin
# ---------------------------------------------------------------------------
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.get("/")
def anasayfa_dosyasi():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")
