"""
predict_stock.py
-----------------
train_universal_lstm.py ile eğitilmiş TEK modeli kullanarak,
seçtiğiniz herhangi bir BIST hissesi için bir sonraki günün fiyat tahminini üretir.

Kullanım (terminalden):
    python predict_stock.py AKBNK
    python predict_stock.py THYAO.IS
    python predict_stock.py            (sembol girmezseniz sorar)
"""

import sys
import pickle
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler

from ml_engine import LSTMModel, MLEngine

engine = MLEngine()


def normalize_ticker(t):
    t = t.strip().upper()
    return t if t.endswith(".IS") else t + ".IS"


def load_artifacts():
    with open("feature_list.pkl", "rb") as f:
        meta = pickle.load(f)
    with open("scalers.pkl", "rb") as f:
        scalers = pickle.load(f)

    lstm = LSTMModel(file_path="lstm_model.h5")
    lstm.model_yukle()  # eğitilmiş evrensel modeli diskten yükler
    return lstm, scalers, meta["features"], meta["window_size"]


def build_features(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df["Close"]
    df["RSI"] = engine.calculate_rsi(close)
    df["EMA20"] = engine.calculate_ema(close, 20)
    df["EMA50"] = engine.calculate_ema(close, 50)
    macd_line, signal_line, _ = engine.calculate_macd(close)
    df["MACD"] = macd_line
    df["MACD_Signal"] = signal_line
    df.dropna(inplace=True)
    return df


def predict_next_close(ticker, lstm, scalers, features, window_size):
    ticker = normalize_ticker(ticker)
    print(f"\n{ticker} için güncel veri indiriliyor...")

    df = yf.download(ticker, period="1y", progress=False)
    if df.empty:
        print(f"HATA: '{ticker}' için veri bulunamadı. Sembolü kontrol edin.")
        return None

    df = build_features(df)
    if len(df) < window_size:
        print("HATA: Yeterli geçmiş veri yok (indikatör ısınma süresi + pencere için).")
        return None

    # Bu hisse eğitimde kullanıldıysa kendi scaler'ını kullan (tutarlılık için en doğrusu).
    # Kullanılmadıysa (yeni/farklı bir hisse), güncel veriyle ANINDA yeni bir scaler fit ediyoruz.
    if ticker in scalers:
        scaler = scalers[ticker]
        print("(Eğitimde kullanılan hisseye özel scaler bulundu.)")
    else:
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaler.fit(df[features].values)
        print("(Bu hisse eğitim setinde yoktu, güncel veriyle yeni scaler oluşturuldu.)")

    scaled = scaler.transform(df[features].values)
    last_window = scaled[-window_size:]  # son 60 gün
    last_window = np.expand_dims(last_window, axis=0)  # (1, 60, num_features)

    pred_scaled = lstm.tahmin_uret(last_window)[0][0]

    # Sadece Close (0. sütun) için ters ölçekleme
    dummy = np.zeros((1, len(features)))
    dummy[0, 0] = pred_scaled
    pred_real = scaler.inverse_transform(dummy)[0, 0]

    last_close = df["Close"].iloc[-1]
    change_pct = (pred_real - last_close) / last_close * 100

    print(f"\n--- {ticker} TAHMİN SONUCU ---")
    print(f"Son kapanış        : {last_close:.2f}")
    print(f"Tahmini sonraki gün : {pred_real:.2f}")
    print(f"Beklenen değişim    : {change_pct:+.2f}%")

    return {
        "ticker": ticker,
        "last_close": float(last_close),
        "predicted_close": float(pred_real),
        "change_pct": float(change_pct),
    }


if __name__ == "__main__":
    lstm, scalers, features, window_size = load_artifacts()

    if len(sys.argv) > 1:
        secilen_hisse = sys.argv[1]
    else:
        secilen_hisse = input("Tahmin almak istediğiniz hisse kodu (örn. AKBNK): ")

    predict_next_close(secilen_hisse, lstm, scalers, features, window_size)