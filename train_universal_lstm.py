"""
train_universal_lstm.py
------------------------
BIST_TICKERS listesindeki TÜM hisselerin verisiyle TEK bir evrensel LSTM modeli eğitir.

Neden tek model?
- Her hisseye ayrı model eğitmek (500 model) hem çok uzun sürer hem de disk/bakım
  açısından pratik değildir.
- Bunun yerine model, RSI/EMA/MACD gibi normalize edilmiş göstergelerden "genel"
  fiyat hareketi kalıplarını öğrenir. Tahmin anında hangi hisseyi seçerseniz,
  o hissenin kendi (ölçeklenmiş) verisi bu tek modele verilir.

ÖNEMLİ: Her hisse kendi MinMaxScaler'ı ile ölçeklenir (fiyatlar çok farklı
seviyelerde olduğu için). Bu scaler'lar 'scalers.pkl' içine kaydedilir ve
predict_stock.py tahmin yaparken bunları kullanır.

Çıktılar:
  - lstm_model.h5   -> eğitilmiş evrensel model (LSTMModel.model_kaydet ile)
  - scalers.pkl      -> {ticker: MinMaxScaler} sözlüğü
  - feature_list.pkl -> kullanılan özelliklerin sırası (predict.py için şart)
"""

import pickle
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler

from ml_engine import LSTMModel, MLEngine
from bist_tickers import BIST_TICKERS

# --------------------------------------------------
# AYARLAR
# --------------------------------------------------
PERIOD = "5y"
WINDOW_SIZE = 60
FEATURES = ["Close", "RSI", "EMA20", "EMA50", "MACD", "MACD_Signal"]  # Close ilk sırada kalmalı
MIN_ROWS_REQUIRED = WINDOW_SIZE + 30  # indikatör ısınması + en az birkaç pencere

engine = MLEngine()


def fetch_and_engineer(ticker):
    """Bir hisse için veri indirir + indikatörleri hesaplar. Yetersizse None döner."""
    try:
        df = yf.download(ticker, period=PERIOD, progress=False)
        if df.empty:
            return None
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

        if len(df) < MIN_ROWS_REQUIRED:
            return None
        return df[FEATURES]
    except Exception as e:
        print(f"  [ATLANDI] {ticker}: {e}")
        return None


def create_sequences(dataset, window_size):
    X, y = [], []
    for i in range(window_size, len(dataset)):
        X.append(dataset[i - window_size:i, :])
        y.append(dataset[i, 0])  # Close (normalize)
    return np.array(X), np.array(y)


# --------------------------------------------------
# TÜM HİSSELER İÇİN VERİ TOPLA
# --------------------------------------------------
all_X, all_y = [], []
scalers = {}
basarili, atlanan = 0, 0

print(f"Toplam {len(BIST_TICKERS)} hisse taranacak...\n")

for i, ticker in enumerate(BIST_TICKERS, 1):
    print(f"[{i}/{len(BIST_TICKERS)}] {ticker} işleniyor...")
    df_feat = fetch_and_engineer(ticker)
    if df_feat is None:
        atlanan += 1
        continue

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(df_feat.values)
    scalers[ticker] = scaler  # tahmin aşamasında bu hisseye özel scaler lazım olacak

    X, y = create_sequences(scaled, WINDOW_SIZE)
    if len(X) == 0:
        atlanan += 1
        continue

    all_X.append(X)
    all_y.append(y)
    basarili += 1

print(f"\nBAŞARILI: {basarili} hisse | ATLANAN: {atlanan} hisse")

if basarili == 0:
    raise RuntimeError("Hiçbir hisseden yeterli veri toplanamadı. İnternet/ticker sembollerini kontrol edin.")

# --------------------------------------------------
# TÜM HİSSELERİN PENCERELERİNİ BİRLEŞTİR (POOLING)
# --------------------------------------------------
X_all = np.concatenate(all_X, axis=0)
y_all = np.concatenate(all_y, axis=0)
print(f"Toplam örnek (tüm hisseler birleşik): {X_all.shape}")

# Karıştır (aynı hissenin ardışık pencereleri birbirine çok benzediği için önemli)
rng = np.random.default_rng(42)
perm = rng.permutation(len(X_all))
X_all, y_all = X_all[perm], y_all[perm]

# Train / test ayır
split_idx = int(len(X_all) * 0.9)
X_train, X_test = X_all[:split_idx], X_all[split_idx:]
y_train, y_test = y_all[:split_idx], y_all[split_idx:]
print(f"Eğitim: {X_train.shape[0]} örnek | Test: {X_test.shape[0]} örnek")

# --------------------------------------------------
# EVRENSEL MODELİ KUR VE EĞİT
# --------------------------------------------------
num_features = X_train.shape[2]

lstm = LSTMModel(file_path="lstm_model.h5")
lstm.model_kur(num_features=num_features)
lstm.model_egit(X_train, y_train, epochs=25, batch_size=64)

# --------------------------------------------------
# TEST PERFORMANSI (normalize uzayda genel MAE — hisseler farklı ölçekte
# olduğu için gerçek TL'ye çevirmek burada anlamlı değil, tek tek predict_stock.py'de yapılır)
# --------------------------------------------------
if len(X_test) > 0:
    preds = lstm.model.predict(X_test).flatten()
    mae_normalized = np.mean(np.abs(preds - y_test))
    print(f"\nTest seti normalize MAE: {mae_normalized:.4f} (0-1 ölçeğinde)")

# --------------------------------------------------
# SCALER'LARI VE ÖZELLİK LİSTESİNİ KAYDET
# --------------------------------------------------
with open("scalers.pkl", "wb") as f:
    pickle.dump(scalers, f)

with open("feature_list.pkl", "wb") as f:
    pickle.dump({"features": FEATURES, "window_size": WINDOW_SIZE}, f)

print("\nEvrensel model 'lstm_model.h5' olarak kaydedildi.")
print("Hisse bazlı scaler'lar 'scalers.pkl' içine kaydedildi.")
print("predict_stock.py ile artık istediğiniz hisseyi seçip tahmin alabilirsiniz.")