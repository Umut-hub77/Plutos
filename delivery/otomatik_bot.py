import json
import yfinance as yf
import numpy as np
from twilio.rest import Client
from auth_utils import get_secret

# 1. AYARLARI OKUMA
# Sırlar (SID/Token) artık .env dosyasından okunur, JSON'a yazılmaz.
# Hassas olmayan ayarlar (numaralar) hâlâ whatsapp_ayarlar.json'da kalabilir.
AYAR_DOSYASI = "whatsapp_ayarlar.json" 

try:
    with open(AYAR_DOSYASI, "r") as f:
        ayarlar = json.load(f)

    tw_sid = get_secret("TWILIO_SID").replace(" ", "")
    tw_token = get_secret("TWILIO_TOKEN").replace(" ", "")
    tw_from = (ayarlar.get("tw_from") or get_secret("TWILIO_FROM")).replace(" ", "")
    tw_to = ayarlar.get("tw_to", "").replace(" ", "")

    if not tw_sid or not tw_token:
        print("Hata: Ayarlar dosyasında API bilgileri eksik!")
        exit()

    client = Client(tw_sid, tw_token)
    
    # 2. MARKOWITZ HEDGED ALTIN ORAN HESAPLAMASI (Otomatik)
    hisseler = ["FROTO", "TUPRS", "ENJSA", "MGROS", "THYAO", "GLDTR"] 
    raw = yf.download([f"{s}.IS" for s in hisseler], period="5y")['Close'].ffill().bfill().dropna()
    
    toplam_gun = len(raw)
    y_getiri = (raw.iloc[-1] / raw.iloc[0]) ** (252 / toplam_gun) - 1
    
    rets = raw.pct_change().dropna()
    max_dd = (raw / raw.cummax() - 1.0).min()
    cov_matrix = rets.cov() * 252
    
    n_ports = 10000
    results = np.zeros((4, n_ports))
    weights_list = []
    gecerli = 0
    
    for i in range(n_ports):
        w = np.random.dirichlet(np.ones(len(hisseler)), size=1)[0]
        if np.any(w > 0.35) or w[hisseler.index("GLDTR")] < 0.10: continue
            
        weights_list.append(w)
        p_cagr = np.sum(w * y_getiri)
        p_risk = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
        p_dd = np.sum(w * max_dd)
        p_score = p_cagr / abs(p_dd) # Calmar
        
        results[0, gecerli] = p_cagr
        results[1, gecerli] = p_risk
        results[2, gecerli] = p_dd
        results[3, gecerli] = p_score
        gecerli += 1
        
    best_idx = np.argmax(results[3, :gecerli])
    o_w, o_g, o_r, o_dd = weights_list[best_idx], results[0, best_idx], results[1, best_idx], results[2, best_idx]
    
    # 3. WHATSAPP MESAJI DERLEME VE GÖNDERME
    msg = "*Otonom Kuantitatif Rapor*\n\n"
    for i, h in enumerate(hisseler):
        msg += f"{'🛡️' if h=='GLDTR' else '🔸'} *{h}:* % {o_w[i]*100:.1f}\n"
        
    msg += f"\n Beklenen Yıllık Büyüme (CAGR): *% {o_g*100:.1f}*\n"
    msg += f" Yıllık Oynaklık (Risk): *% {o_r*100:.1f}*\n"
    msg += "🤖 _Sunucu tetiklemesi başarılı._"
    
    client.messages.create(from_=f"whatsapp:{tw_from}", body=msg, to=f"whatsapp:{tw_to}")
    print("Mesaj başarıyla fırlatıldı!")

except Exception as e:
    print(f"Kritik Hata Oluştu: {e}")