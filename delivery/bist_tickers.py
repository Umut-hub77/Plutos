"""
bist_tickers.py
----------------
BIST hisse listesi. yfinance için sonuna ".IS" ekli haldedir.

NOT: Bu liste BIST100'ü kapsıyor (~100 hisse). Borsa İstanbul'da işlem gören
TÜM hisseler (~500) için:
  1) Borsa İstanbul'un resmi sitesinden (borsaistanbul.com) veya
     bir veri sağlayıcıdan (ör. isyatirim.com.tr) güncel şirket kodları listesini
     CSV olarak indirin.
  2) Aşağıdaki BIST_TICKERS listesine ekleyin ya da bu listeyi tamamen bir
     CSV dosyasından okuyacak şekilde değiştirin (örnek fonksiyon en altta).

Liste ne kadar büyürse eğitim o kadar uzun sürer; GPU yoksa önce BIST100 ile
test edip sisteme güvendikten sonra genişletmenizi öneririm.
"""

BIST_TICKERS = [
    "AEFES.IS","AGHOL.IS","AKBNK.IS","AKFGY.IS","AKSA.IS","AKSEN.IS","ALARK.IS",
    "ALFAS.IS","ARCLK.IS","ASELS.IS","ASTOR.IS","AYDEM.IS","BERA.IS","BIMAS.IS",
    "BRSAN.IS","BRYAT.IS","BUCIM.IS","CANTE.IS","CCOLA.IS","CIMSA.IS","DOAS.IS",
    "ECILC.IS","ECZYT.IS","EGEEN.IS","EKGYO.IS","ENERY.IS","ENJSA.IS","ENKAI.IS",
    "EREGL.IS","EUPWR.IS","FROTO.IS","GARAN.IS","GESAN.IS","GUBRF.IS","HALKB.IS",
    "HEKTS.IS","ISCTR.IS","ISMEN.IS","IZMDC.IS","KARSN.IS","KAYSE.IS","KCHOL.IS",
    "KLSER.IS","KMPUR.IS","KONTR.IS","KONYA.IS","KORDS.IS","KOZAA.IS","KOZAL.IS",
    "KRDMD.IS","MAVI.IS","MGROS.IS","MIATK.IS","ODAS.IS","OTKAR.IS","OYAKC.IS",
    "PENTA.IS","PETKM.IS","PGSUS.IS","QUAGR.IS","SAHOL.IS","SASA.IS","SISE.IS",
    "SKBNK.IS","SMRTG.IS","SOKM.IS","TAVHL.IS","TCELL.IS","THYAO.IS","TKFEN.IS",
    "TOASO.IS","TSKB.IS","TTKOM.IS","TTRAK.IS","TUKAS.IS","TUPRS.IS","TURSG.IS",
    "ULKER.IS","VAKBN.IS","VESBE.IS","VESTL.IS","YEOTK.IS","YKBNK.IS","ZOREN.IS",
]


def load_tickers_from_csv(csv_path, column="ticker", suffix=".IS"):
    """
    Tam BIST listesini bir CSV'den okumak isterseniz kullanın.
    CSV'de örn. bir 'ticker' kolonu olmalı: AKBNK, GARAN, THYAO ... (BIST kodu, .IS olmadan)
    """
    import pandas as pd
    df = pd.read_csv(csv_path)
    codes = df[column].astype(str).str.strip().str.upper()
    return [c if c.endswith(suffix) else c + suffix for c in codes]