import os
import json
import requests
import xml.etree.ElementTree as ET

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# API Anahtarını doğrudan buraya yapıştır (Daha sonra auth_utils.get_secret mantığına geçirebilirsin)
GEMINI_API_KEY = "AQ.Ab8RN6IC00pUyFVy-84kJqBoH3JnxyHf5IJ2VE3IySRoGa48lg" 
MODEL_NAME = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """Sen Lumina Quant AI'sın; Borsa İstanbul (BIST) hisseleri ve halka arzlar
konusunda kullanıcıya bilgilendirici, veri temelli analiz sunan bir finansal analiz asistanısın.
Lumina Quant Terminal uygulamasının içine gömülüsün.

KURALLAR:
- Kullanıcı genel olarak yeni halka arzları sorarsa, sadece şirket isimlerini listeleme. Haberlerden elde ettiğin bilgilerle şirketlerin ne iş yaptığını (hikayesini), faaliyet alanını ve varsa talep toplama verilerini (lot, büyüklük vb.) madde madde, detaylı bir analiz formatında sun. Çok eski tarihli haberleri analizden dışla.
- Sen bir yatırım danışmanı DEĞİLSİN. Asla kesin "al" / "sat" talimatı verme; bunun yerine
  indikatörlerin ve gerçek verinin ne gösterdiğini tarafsızca açıkla.
- Elindeki araçları (tool) kullanarak GERÇEK veri çek; hiçbir fiyat/rakam/haber uydurma.
  Bir soruyu araç kullanmadan tahminle yanıtlamak yerine ilgili aracı çağır.
- Kısa, net, madde işaretli ve sade Türkçe yanıt ver. Gereksiz uzatma, emoji'yi ölçülü kullan.
- Her analiz içeren yanıtın SONUNA kısaca şunu ekle: "_Bu bir yatırım tavsiyesi değildir._"
- Kullanıcı portföyünü sorarsa portfoy_ozeti aracını kullan.
- Kullanıcı belirli bir hisse hakkında soru sorarsa hisse_teknik_analiz aracını, gerekirse
  ek olarak hisse_haber_analizi aracını da kullan.
- Kullanıcı halka arz (IPO) sorarsa halka_arz_haberleri aracını kullan; bu aracın haber
  bazlı olduğunu ve resmi bir takvim olmadığını belirt.
- Bir araç "hata" alanı dönerse bunu kullanıcıya nazikçe ilet, veri uydurma.
- Haberlerini öncelikli olarak KAP haberlerinden çek.
"""

if GEMINI_AVAILABLE:
    bist_tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="hisse_teknik_analiz",
                    description="Bir BIST hissesinin güncel fiyatını, PD/DD oranını, RSI/EMA20/EMA50/MACD indikatörlerini, tespit edilen grafik formasyonunu ve otomatik üretilmiş yatırımcı yorumunu döndürür.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "sembol": types.Schema(type=types.Type.STRING, description="BIST hisse kodu, örn. THYAO")
                        },
                        required=["sembol"]
                    )
                ),
                types.FunctionDeclaration(
                    name="hisse_haber_analizi",
                    description="Bir BIST hissesiyle ilgili en güncel haber başlıklarını ve basit duyarlılık (sentiment) skorunu döndürür.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "sembol": types.Schema(type=types.Type.STRING, description="BIST hisse kodu, örn. THYAO")
                        },
                        required=["sembol"]
                    )
                ),
                types.FunctionDeclaration(
                    name="portfoy_ozeti",
                    description="Giriş yapmış kullanıcının kayıtlı portföyündeki tüm pozisyonları (lot, maliyet) döndürür."
                ),
                types.FunctionDeclaration(
                    name="halka_arz_haberleri",
                    description="BIST'te güncel/yaklaşan halka arzlarla ilgili en son haber başlıklarını döndürür.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "sirket_adi": types.Schema(type=types.Type.STRING, description="Opsiyonel: belirli bir şirket/halka arz için, örn. 'Reeder'.")
                        }
                    )
                )
            ]
        )
    ]
else:
    bist_tools = []

# ---------------------------------------------------------------------------
# ARAÇ (TOOL) UYGULAMALARI (Orijinal Kodlarından Kurtarılan Kısım)
# ---------------------------------------------------------------------------

def _hisse_teknik_analiz(sembol, data_engine, ml_engine):
    sembol = sembol.upper().replace(".IS", "").strip()
    try:
        df = data_engine.get_historical_data(f"{sembol}.IS", period="6mo", interval="1d")
        if df is None or df.empty or len(df) < 30:
            return {"hata": f"{sembol} için yeterli fiyat verisi bulunamadı."}

        close_col = "Close" if "Close" in df.columns else "close"
        close = df[close_col]

        price, pb = data_engine.get_stock_price_and_pb(sembol)
        if not price:
            price = float(close.iloc[-1])

        rsi = float(ml_engine.calculate_rsi(close).iloc[-1])
        ema20 = float(ml_engine.calculate_ema(close, 20).iloc[-1])
        ema50 = float(ml_engine.calculate_ema(close, 50).iloc[-1])
        macd_line, signal_line, _ = ml_engine.calculate_macd(close)

        pattern_name, _slope, _corr = ml_engine.detect_pattern_advanced(close.values[-30:])
        comment, status = ml_engine.generate_investment_comment(
            price, rsi, ema20, ema50, float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), pattern_name
        )

        return {
            "sembol": sembol,
            "güncel_fiyat": round(price, 2),
            "pd_dd": round(pb, 2) if pb else "veri yok",
            "rsi": round(rsi, 1),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "macd_durumu": "AL" if macd_line.iloc[-1] > signal_line.iloc[-1] else "SAT",
            "tespit_edilen_formasyon": pattern_name,
            "otomatik_yorum": comment,
            "genel_durum": status,
        }
    except Exception as e:
        return {"hata": f"{sembol} analiz edilirken bir sorun oluştu: {e}"}


def _hisse_haber_analizi(sembol, data_engine, ml_engine):
    sembol = sembol.upper().replace(".IS", "").strip()
    try:
        haberler = data_engine.get_stock_news(sembol)
        if not haberler:
            return {"sembol": sembol, "haberler": [], "not": "Güncel haber bulunamadı."}
        etiket, skor = ml_engine.analyze_sentiment(haberler)
        return {
            "sembol": sembol,
            "haber_basliklari": [h.get("title", "") for h in haberler],
            "duyarlilik": etiket,
            "duyarlilik_skoru": skor,
        }
    except Exception as e:
        return {"hata": f"{sembol} haberleri çekilirken bir sorun oluştu: {e}"}


def _portfoy_ozeti(session_state):
    kullanici = session_state.get("giris_yapan_kullanici")
    if not kullanici:
        return {"hata": "Kullanıcı girişi bulunamadı."}
    portfoy = kullanici.get("portfolio", {})
    if not portfoy:
        return {"not": "Portföyde henüz kayıtlı hisse yok."}
    return {"pozisyonlar": portfoy}


def _halka_arz_haberleri(sirket_adi=None):
    try:
        sorgu = f"{sirket_adi} halka arz when:7d" if sirket_adi else '"SPK bülteni" OR "talep toplama" yeni halka arz when:7d'
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(sorgu)}&hl=tr-TR&gl=TR&ceid=TR:tr"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code != 200:
            return {"hata": "Halka arz haberlerine şu an ulaşılamadı."}
        root = ET.fromstring(r.content)
        basliklar = [item.find("title").text for item in root.findall(".//item")[:8]]
        return {"sorgu": sorgu, "haber_basliklari": basliklar,
                "not": "Bu sonuçlar haber taramasıdır, resmi bir halka arz takvimi değildir."}
    except Exception as e:
        return {"hata": f"Halka arz haberleri çekilirken sorun oluştu: {e}"}


def _tool_dispatch(name, tool_input, ctx):
    if name == "hisse_teknik_analiz":
        return _hisse_teknik_analiz(tool_input.get("sembol", ""), ctx["data_engine"], ctx["ml_engine"])
    if name == "hisse_haber_analizi":
        return _hisse_haber_analizi(tool_input.get("sembol", ""), ctx["data_engine"], ctx["ml_engine"])
    if name == "portfoy_ozeti":
        return _portfoy_ozeti(ctx["session_state"])
    if name == "halka_arz_haberleri":
        return _halka_arz_haberleri(tool_input.get("sirket_adi"))
    return {"hata": f"Bilinmeyen araç: {name}"}


# ---------------------------------------------------------------------------
# GEMINI YÖNETİMİ VE SOHBET DÖNGÜSÜ
# ---------------------------------------------------------------------------

def asistan_hazir_mi():
    return GEMINI_AVAILABLE and bool(GEMINI_API_KEY)

def sohbet_yaniti_uret(mesaj_gecmisi, data_engine, ml_engine, session_state):
    if not GEMINI_AVAILABLE:
        return "⚠️ HATA: 'google-genai' kütüphanesi import edilemedi. Lütfen kurulumu kontrol edin."

    client = genai.Client(api_key=GEMINI_API_KEY)
    ctx = {"data_engine": data_engine, "ml_engine": ml_engine, "session_state": session_state}

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=bist_tools,
        temperature=0.2
    )

    formatted_history = []
    if len(mesaj_gecmisi) > 1:
        for m in mesaj_gecmisi[:-1]:
            role = "user" if m["role"] == "user" else "model"
            formatted_history.append(
                types.Content(role=role, parts=[types.Part.from_text(text=m["content"])])
            )

    chat = client.chats.create(
        model=MODEL_NAME,
        config=config,
        history=formatted_history
    )

    son_mesaj = mesaj_gecmisi[-1]["content"] if mesaj_gecmisi else "Merhaba"

    try:
        response = chat.send_message(son_mesaj)

        for _ in range(5):
            if not response.function_calls:
                return response.text

            function_responses = []
            for fc in response.function_calls:
                name = fc.name
                args = fc.args

                sonuc = _tool_dispatch(name, args, ctx)

                function_responses.append(
                    types.Part.from_function_response(
                        name=name,
                        response={"result": sonuc}
                    )
                )

            response = chat.send_message(function_responses)

        return "Analiz birden fazla adım gerektirdi ve tamamlanamadı."

    except Exception as e:
        return f"⚠️ AI Asistan hatası: {e}"