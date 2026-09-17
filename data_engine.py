import pandas as pd
import streamlit as st
import time
import yfinance as yf
import requests
import xml.etree.ElementTree as ET

# tvDatafeed PyPI'de değil, sadece GitHub'dan kurulabiliyor (git gerektiriyor) ve
# resmi olarak bakımı yapılmıyor. Bu yüzden zorunlu bağımlılık yapmak yerine
# opsiyonel hale getirdik: kuruluysa TradingView kanalı kullanılır, kurulu değilse
# (veya kurulum başarısız olduysa) uygulama otomatik olarak sadece Yahoo Finance
# kanalıyla çalışır — hiçbir şey çökmez.
try:
    from tvDatafeed import TvDatafeed, Interval
    TVDATAFEED_AVAILABLE = True
except ImportError:
    TVDATAFEED_AVAILABLE = False


def son_gecerli_satirlar(df):
    """
    Borsa kapalıyken / seans öncesinde yfinance'in eklediği "henüz oluşmamış"
    satırları temizler. İki ayrı belirti olabilir:
      1) Close NaN gelir (en sık görülen durum), VEYA
      2) Close dolu ama Volume 0/NaN gelir — bu, seansın henüz KAPANMADIĞI,
         sadece bir "taslak" satır olduğu anlamına gelir ve fiyat yanıltıcı olabilir.
    Geriye sadece gerçekten kapanmış (Volume > 0) seansların satırları kalır,
    böylece "son satır" her zaman son GERÇEK kapanışı temsil eder.
    """
    if df is None or df.empty:
        return df
    temiz = df
    if 'Close' in temiz.columns:
        temiz = temiz[temiz['Close'].notna()]
    if 'Volume' in temiz.columns and not temiz.empty:
        gecerli_hacim = temiz[(temiz['Volume'].notna()) & (temiz['Volume'] > 0)]
        # Hacim verisi tamamen yoksa (bazı endeks/emtia sembollerinde olabilir)
        # Close filtresiyle yetin; tüm veriyi silmiş olmayalım.
        if not gecerli_hacim.empty:
            temiz = gecerli_hacim
    return temiz


class DataEngine:
    """
    Lumina Quant - Veri Motoru v109.0 (Fix: 0 TL Hatası Giderildi)
    - Google News RSS (Haberler)
    - TradingView + Yahoo (Fiyat Verileri)
    - Hafta Sonu Korumalı Fiyat Çekici
    """
    def __init__(self):
        self.initialize_tv()

    def initialize_tv(self):
        """TradingView Bağlantısını Başlatır (Arka Planda). tvDatafeed kurulu değilse
        sessizce atlar ve Yahoo Finance yedeğine düşer."""
        if not TVDATAFEED_AVAILABLE:
            self.tv = None
            return
        if 'tv_connection' not in st.session_state:
            try:
                st.session_state.tv_connection = TvDatafeed()
            except:
                st.session_state.tv_connection = None
        self.tv = st.session_state.tv_connection

    @st.cache_data(ttl=120, show_spinner=False)
    def get_historical_data(_self, symbol, period='1y', interval='1d'):
        """
        Detaylı Grafik Verisi (TradingView Öncelikli, Yahoo Yedekli)
        """
        clean_symbol = symbol.split('.')[0].upper()
        
        # 1. KANAL: TRADINGVIEW (yalnızca tvDatafeed kuruluysa denenir)
        if TVDATAFEED_AVAILABLE:
            try:
                if _self.tv is None: _self.initialize_tv()

                # Bar sayısı hesaplama (Optimizasyon)
                n_bars = 300
                if interval == '1d':
                    if period == '5y': n_bars = 1300
                    elif period == '1y': n_bars = 260
                    elif period == '6mo': n_bars = 130
                elif interval == '1h': n_bars = 500

                tv_itvl = Interval.in_daily
                if interval == '1h': tv_itvl = Interval.in_1_hour

                # BIST veya ISE borsalarında dene
                for _ in range(2):
                    df = st.session_state.tv_connection.get_hist(symbol=clean_symbol, exchange='BIST', interval=tv_itvl, n_bars=n_bars)
                    if df is None: df = st.session_state.tv_connection.get_hist(symbol=clean_symbol, exchange='ISE', interval=tv_itvl, n_bars=n_bars)

                    if df is not None and not df.empty:
                        return df.rename(columns={'open':'Open', 'high':'High', 'low':'Low', 'close':'Close', 'volume':'Volume'})
                    time.sleep(0.1)
            except: pass

        # 2. KANAL: YAHOO (Fallback - Yedek)
        return _self.get_data_yfinance_direct(symbol, period, interval)

    def get_data_yfinance_direct(self, symbol, period, interval):
        """Yedek Veri Kanalı (Yahoo)"""
        try:
            clean = symbol.split('.')[0].upper()
            df_yf = yf.download(f"{clean}.IS", period=period, interval=interval, progress=False)
            if not df_yf.empty:
                # Multi-level sütun yapısını düzelt
                if isinstance(df_yf.columns, pd.MultiIndex): 
                    df_yf.columns = df_yf.columns.droplevel(1)
                df_yf = df_yf.rename(columns={'Open':'Open', 'High':'High', 'Low':'Low', 'Close':'Close', 'Volume':'Volume'})
                # Seans kapanmadan eklenen "taslak" satırı (Close NaN veya Volume 0) atıyoruz —
                # grafik ve analizler her zaman son GERÇEK kapanışı baz alsın.
                df_yf = son_gecerli_satirlar(df_yf)
                return df_yf
        except: pass
        return pd.DataFrame()

    def get_stock_price_and_pb(self, symbol):
        try:
            clean = symbol.split('.')[0].upper()
            t = yf.Ticker(f"{clean}.IS")
            
            # FIX: period="5d" yaparak hafta sonu/tatil riskini bitiriyoruz.
            # Son 5 günün verisini çekip en sonuncusunu alacağız.
            hist = t.history(period="5d")
            # Seans kapanmadan eklenen "taslak" satırı (Close NaN veya Volume 0) atıyoruz.
            hist = son_gecerli_satirlar(hist)
            
            price = 0.0
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
            else:
                # Fallback: History boşsa download dene
                data = yf.download(f"{clean}.IS", period="5d", progress=False)
                data = son_gecerli_satirlar(data)
                if not data.empty:
                    # Sütun yapısına göre fiyatı yakala
                    if 'Close' in data.columns:
                        price = float(data['Close'].iloc[-1])
                    else:
                        price = float(data.iloc[-1, 0]) # İlk sütunu al

            # PD/DD Oranını Al (Hata verirse 0 dön)
            try:
                pb = t.info.get('priceToBook', 0)
            except: 
                pb = 0
            
            return price, pb
        except:
            # Her şey başarısız olursa
            return 0.0, 0.0

    def get_stock_news(self, symbol):
        """
        GOOGLE NEWS RSS ENTEGRASYONU
        """
        try:
            clean = symbol.split('.')[0].upper()
            # Google News RSS URL (Türkçe)
            url = f"https://news.google.com/rss/search?q={clean}+hisse&hl=tr-TR&gl=TR&ceid=TR:tr"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=4)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                news_list = []
                # İlk 5 haberi çek
                for item in root.findall('.//item')[:5]: 
                    title = item.find('title').text
                    link = item.find('link').text
                    news_list.append({'title': title, 'link': link})
                return news_list
            return []
        except: return []