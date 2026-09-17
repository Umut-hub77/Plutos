import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
from datetime import datetime
import os
import json
import hashlib
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
from scipy.signal import argrelextrema
import streamlit as st
import pandas_ta as ta
import streamlit as st
import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Plutos", layout="wide", page_icon="🪙")

# ---------- Plutos Marka Simgesi (minimal, tek renk, geometrik) ----------
# Bir "coin" (madeni para) çemberi içine oturtulmuş, keskin köşeli P monogramı.
# Tek renk (--gold / asit-lime), stroke tabanlı, dekorasyonsuz -> minimal/high-contrast kimlikle uyumlu.
def plutos_logo_svg(size=30, color="#D7FF4E"):
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="20" cy="20" r="18.5" stroke="{color}" stroke-width="2"/>
        <path d="M15 11.5H21.2C24.5 11.5 27 13.9 27 17C27 20.1 24.5 22.4 21.2 22.4H16.6V28.5H15V11.5Z"
              stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
    </svg>
    """

from auth_utils import hash_password, verify_password, needs_rehash

def hash_credentials(password):
    # NOT: Yeni kayıtlar artık bcrypt+salt ile hash'leniyor (auth_utils.py).
    # Bu fonksiyon geriye dönük uyumluluk için hâlâ duruyor ama doğrudan
    # kullanılmamalı; giriş/kayıt akışında verify_password / hash_password kullanılıyor.
    return hash_password(password)

def yatirim_uyarisi_goster():
    """SPK/mevzuat uyumu: bu ekranda üretilen sinyal, skor ve projeksiyonlar
    yatırım tavsiyesi değildir; bilgilendirme amaçlıdır."""
    st.warning(
        "⚠️ **Yasal Uyarı:** Bu platformdaki içerik, algoritmik sinyal, puan ve projeksiyonlar "
        "yatırım danışmanlığı kapsamında değildir ve yatırım tavsiyesi niteliği taşımaz. "
        "Burada yer alan bilgiler, herhangi bir yatırım aracının alım-satımına yönelik bir "
        "teklif veya öneri olarak yorumlanmamalıdır. Yatırım kararlarınızı kendi araştırmanıza "
        "ve/veya yetkili bir yatırım danışmanına dayandırınız.",
        icon="⚠️",
    )

def uygula_global_css():
    """
    Lumina Quant — Tasarım Sistemi
    ================================
    Uygulamanın TEK CSS kaynağı. Önceden iki ayrı yerde (bu fonksiyon + dosyanın
    ortasında ikinci bir st.markdown bloğu) çakışan/parçalı stiller vardı; ikisi
    birleştirildi ki tüm ekranlarda (giriş, sidebar, tablar, tablolar, uyarılar,
    metrikler, formlar) tutarlı tek bir görsel dil olsun.

    Kimlik: "İstanbul quant terminali" — derin lacivert zemin + antika altın vurgu
    (jenerik fintech mavi/yeşilinden kaçınmak için bilinçli seçim; altın hem BIST
    kültüründe hem portföydeki GLDTR gibi enstrümanlarda karşılığı olan bir referans).
    Tipografi: başlıklarda karakterli bir serif (Fraunces), arayüzde Inter,
    fiyat/ticker gibi verilerde JetBrains Mono.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

        :root {
            --bg: #08080A;
            --bg-elevated: #0C0C0F;
            --surface: #131316;
            --surface-hover: #1B1B1F;
            --border: #232327;
            --border-strong: #38383F;
            --text: #F7F7F8;
            --text-muted: #9A9AA4;
            --text-faint: #5C5C64;
            --gold: #D7FF4E;
            --gold-strong: #E6FF80;
            --gold-soft: rgba(215, 255, 78, 0.10);
            --green: #22C55E;
            --green-soft: rgba(34, 197, 94, 0.12);
            --red: #F0455C;
            --red-soft: rgba(240, 69, 92, 0.12);
        }

        /* ---------- Zemin & Genel Tipografi ---------- */
        html, body, .stApp {
            background: var(--bg);
            color: var(--text);
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; letter-spacing: -0.01em; }
        code, .stDataFrame, .stMetric, .stMetric [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; }

        /* ---------- Kenar Çubuğu ---------- */
        section[data-testid="stSidebar"] {
            background: var(--bg-elevated);
            border-right: 1px solid var(--border);
        }
        section[data-testid="stSidebar"] .stRadio label { font-size: 14px; }

        /* ---------- Ayırıcı çizgi: altın hairline ---------- */
        hr {
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, var(--border-strong) 20%, var(--border-strong) 80%, transparent) !important;
            margin: 14px 0 22px 0 !important;
        }

        /* ---------- Sekmeler (Tabs) ---------- */
        .stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--border); }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 8px 8px 0 0;
            padding: 10px 18px;
            color: var(--text-muted);
            border: 1px solid transparent;
            border-bottom: none;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover { color: var(--text); background-color: var(--surface); }
        .stTabs [aria-selected="true"] {
            background-color: var(--surface) !important;
            color: var(--gold-strong) !important;
            border: 1px solid var(--border) !important;
            border-bottom: 2px solid var(--gold) !important;
            font-weight: 600;
        }

        /* ---------- Butonlar ---------- */
        .stButton button, .stFormSubmitButton button {
            background-color: var(--surface);
            color: var(--text);
            border: 1px solid var(--border-strong);
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stButton button:hover, .stFormSubmitButton button:hover {
            border-color: var(--gold);
            color: var(--gold-strong);
            background-color: var(--gold-soft);
        }
        /* Birincil aksiyon butonları (type="primary") altın vurgulu */
        .stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {
            background-color: var(--gold) !important;
            border-color: var(--gold) !important;
            color: #14110A !important;
            font-weight: 700;
        }
        .stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover {
            background-color: var(--gold-strong) !important;
            border-color: var(--gold-strong) !important;
        }
        /* Analiz/Tara gibi "action" anahtarlı butonlar: ikincil vurgu (yeşil) */
        button[key*="action"] {
            height: 44px !important;
            padding: 0 28px !important;
            border: 1px solid var(--green) !important;
            background-color: var(--green-soft) !important;
            color: var(--green) !important;
            font-size: 13px !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
        }
        button[key*="action"]:hover { background-color: var(--green) !important; color: #06140D !important; }

        /* İzleme listesi kart-butonları */
        div[data-testid="column"] button {
            white-space: pre-wrap !important;
            height: 110px !important;
            border-radius: 12px !important;
        }

        /* ---------- Girdi Kutuları ---------- */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        .stTextInput input, .stNumberInput input, .stDateInput input {
            background-color: var(--surface) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="input"] > div:focus-within {
            border-color: var(--gold) !important;
            box-shadow: 0 0 0 1px var(--gold) !important;
        }
        span[data-baseweb="tag"] {
            background-color: var(--surface) !important;
            color: var(--gold-strong) !important;
            border: 1px solid var(--border-strong) !important;
            border-radius: 6px !important;
            padding: 4px 8px !important;
            font-size: 13px !important;
        }

        /* ---------- Expander / Panel ---------- */
        div[data-testid="stExpander"] {
            background-color: var(--surface);
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        }

        /* ---------- Uyarılar (info/warning/error/success) ---------- */
        div[data-testid="stAlert"] {
            border-radius: 8px !important;
            border: none !important;
            border-left: 3px solid var(--border-strong) !important;
            background-color: var(--surface) !important;
        }

        /* ---------- Metrikler ---------- */
        div[data-testid="stMetric"] {
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
        }
        div[data-testid="stMetricLabel"] {
            color: var(--text-muted) !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 11px !important;
        }
        div[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700 !important; }

        /* ---------- Tablolar / DataFrame ---------- */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
        }

        /* ---------- Lumina bileşen sınıfları (bolum_basligi, kart, rozet vb.) ---------- */
        .lq-section {
            display: flex; align-items: baseline; gap: 12px;
            margin: 6px 0 4px 0; padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }
        .lq-section-icon { font-size: 22px; line-height: 1; opacity: 0.9; }
        .lq-section-title {
            font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 26px;
            color: var(--text); margin: 0;
        }
        .lq-section-sub { color: var(--text-faint); font-size: 13px; margin-left: 4px; }
        .lq-section::after { content: ""; flex: 1; height: 2px; align-self: flex-end;
            background: linear-gradient(90deg, var(--gold), transparent); margin-bottom: -11px; }

        .lq-card {
            background-color: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; padding: 16px 18px;
        }

        .lq-pill {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 4px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 600;
            letter-spacing: 0.02em;
        }
        .lq-pill-buy { background: var(--green-soft); color: var(--green); border: 1px solid rgba(34,197,94,0.35); }
        .lq-pill-sell { background: var(--red-soft); color: var(--red); border: 1px solid rgba(240,69,92,0.35); }
        .lq-pill-neutral { background: var(--gold-soft); color: var(--gold-strong); border: 1px solid rgba(215,255,78,0.35); }

        /* ---------- Plutos Üst Navbar (site-benzeri sekmeler) ---------- */
        .plutos-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 6px 2px 18px 2px; margin-bottom: 4px;
            border-bottom: 1px solid var(--border);
        }
        .plutos-brand { display: flex; align-items: center; gap: 10px; }
        .plutos-brand span {
            font-family: 'Space Grotesk', sans-serif; font-size: 19px; font-weight: 700;
            color: var(--text); letter-spacing: 0.01em;
        }

        /* Ana kategori sekmeleri (1. seviye) */
        div[role="radiogroup"][aria-label="plutos_cat_nav"] { gap: 4px; border-bottom: 1px solid var(--border); padding-bottom: 0; }
        div[role="radiogroup"][aria-label="plutos_cat_nav"] label {
            border: none !important; background: transparent !important;
            padding: 10px 4px !important; margin-right: 22px !important;
            border-radius: 0 !important; border-bottom: 2px solid transparent !important;
        }
        div[role="radiogroup"][aria-label="plutos_cat_nav"] label div[data-testid="stMarkdownContainer"] p {
            font-family: 'Space Grotesk', sans-serif; font-size: 16px; font-weight: 600;
            color: var(--text-muted);
        }
        div[role="radiogroup"][aria-label="plutos_cat_nav"] label:has(input:checked) {
            border-bottom: 2px solid var(--gold) !important;
        }
        div[role="radiogroup"][aria-label="plutos_cat_nav"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
            color: var(--text) !important;
        }
        div[role="radiogroup"][aria-label="plutos_cat_nav"] label > div:first-child { display: none; }

        /* Alt modül sekmeleri (2. seviye - pill görünümlü) */
        div[role="radiogroup"][aria-label="plutos_mod_nav"] { gap: 8px; margin: 14px 0 10px 0; }
        div[role="radiogroup"][aria-label="plutos_mod_nav"] label {
            border: 1px solid var(--border) !important; background: var(--surface) !important;
            padding: 6px 14px !important; border-radius: 999px !important;
        }
        div[role="radiogroup"][aria-label="plutos_mod_nav"] label div[data-testid="stMarkdownContainer"] p {
            font-size: 13px; font-weight: 500; color: var(--text-muted);
        }
        div[role="radiogroup"][aria-label="plutos_mod_nav"] label:has(input:checked) {
            border-color: var(--gold) !important; background: var(--gold-soft) !important;
        }
        div[role="radiogroup"][aria-label="plutos_mod_nav"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
            color: var(--gold-strong) !important; font-weight: 600;
        }
        div[role="radiogroup"][aria-label="plutos_mod_nav"] label > div:first-child { display: none; }

        /* Bildirim zili butonu */
        button[key="plutos_bell_btn"] {
            border-radius: 999px !important; height: 42px !important; width: 42px !important;
            padding: 0 !important; font-size: 16px !important;
        }

        /* ---------- Hızlı İşlem Kartları (Ana Sayfa) — tablet/mobil fintech uygulamalarında
           yaygın "ikon + etiket" kısayol satırı deseninden ilham alındı ---------- */
        .plutos-hizli-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px; margin: 4px 0 18px 0;
        }
        .plutos-hizli-kart {
            background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
            padding: 16px 10px; text-align: center; cursor: pointer; transition: border-color .15s;
            min-height: 78px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
        }
        .plutos-hizli-kart:hover { border-color: var(--gold); }
        .plutos-hizli-kart .ikon { font-size: 22px; }
        .plutos-hizli-kart .etiket { font-size: 12.5px; color: var(--text-muted); font-weight: 500; }

        button[key^="quickact_"] {
            width: 100%; min-height: 72px !important; background: var(--surface) !important;
            border: 1px solid var(--border) !important; border-radius: 10px !important;
            display: flex !important; flex-direction: column !important; white-space: pre-line !important;
            font-size: 13px !important; line-height: 1.5 !important;
        }
        button[key^="quickact_"]:hover { border-color: var(--gold) !important; color: var(--gold-strong) !important; }

        /* ---------- Tablet & dokunmatik ekran uyumu (≤ 1024px) ---------- */
        @media (max-width: 1024px) {
            .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }

            /* Dokunmatik hedefler en az 44px yüksekliğinde olmalı (erişilebilirlik standardı) */
            div[role="radiogroup"][aria-label="plutos_cat_nav"] label {
                padding: 13px 6px !important; margin-right: 16px !important; font-size: 15px !important;
            }
            div[role="radiogroup"][aria-label="plutos_mod_nav"] {
                overflow-x: auto; flex-wrap: nowrap !important; padding-bottom: 4px;
            }
            div[role="radiogroup"][aria-label="plutos_mod_nav"] label {
                padding: 11px 16px !important; white-space: nowrap;
            }
            .stButton button { min-height: 44px !important; }
            .plutos-header { padding: 14px 16px !important; }
            .lq-section-title { font-size: 21px !important; }
            div[data-testid="stMetricValue"] { font-size: 20px !important; }
        }
    </style>
    """, unsafe_allow_html=True)


def bolum_basligi(baslik, ikon=None, alt_baslik=None):
    """Tüm modüllerde ortak, altın-vurgulu bölüm başlığı (eski st.header(...) yerine)."""
    ikon_html = f'<span class="lq-section-icon">{ikon}</span>' if ikon else ""
    alt_html = f'<span class="lq-section-sub">{alt_baslik}</span>' if alt_baslik else ""
    st.markdown(
        f'<div class="lq-section">{ikon_html}<h2 class="lq-section-title">{baslik}</h2>{alt_html}</div>',
        unsafe_allow_html=True,
    )


def plutos_tablo_stilli(df, yuzde_kolonlari=None, para_kolonlari=None, bar_kolonu=None, notr_para_kolonlari=None):
    """
    st.dataframe için ortak görsel iyileştirme: pozitif değerler yeşil, negatif değerler
    kırmızı + kalın; opsiyonel olarak bir kolona inline bar (pozitif/negatif renkli) eklenir.
    notr_para_kolonlari: yönü olmayan (örn. güncel fiyat) parasal kolonlar — sadece ₺ formatlanır, renklenmez.
    Not: st.dataframe'in canvas tabanlı grid'i CSS değişkeni (var(--...)) çözemediği için
    burada temaya ait renkler bilerek ham hex olarak kullanılıyor.
    """
    yesil, kirmizi = "#22C55E", "#F0455C"

    def _renk(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return ""
        if v > 0:
            return f"color: {yesil}; font-weight: 600;"
        if v < 0:
            return f"color: {kirmizi}; font-weight: 600;"
        return ""

    style = df.style
    if yuzde_kolonlari:
        gecerli = [c for c in yuzde_kolonlari if c in df.columns]
        if gecerli:
            style = style.map(_renk, subset=gecerli).format({c: "{:+.2f}%" for c in gecerli})
    if para_kolonlari:
        gecerli_p = [c for c in para_kolonlari if c in df.columns]
        if gecerli_p:
            style = style.map(_renk, subset=gecerli_p).format({c: "{:,.2f} ₺" for c in gecerli_p})
    if notr_para_kolonlari:
        gecerli_n = [c for c in notr_para_kolonlari if c in df.columns]
        if gecerli_n:
            style = style.format({c: "{:,.2f} ₺" for c in gecerli_n})
    if bar_kolonu and bar_kolonu in df.columns:
        style = style.bar(subset=[bar_kolonu], align="mid", color=[kirmizi, yesil])
    return style


def sinyal_rozeti(metin, tur="neutral"):
    """AL/SAT/TUT gibi sinyalleri tutarlı bir rozet (pill) olarak döndürür."""
    sinif = {"buy": "lq-pill-buy", "sell": "lq-pill-sell"}.get(tur, "lq-pill-neutral")
    return f'<span class="lq-pill {sinif}">{metin}</span>'


# ---------- Grafik (Plotly) Tema Sistemi ----------
LQ_BG = "#0C0C0F"
LQ_SURFACE = "#131316"
LQ_GRID = "#232327"
LQ_TEXT = "#F7F7F8"
LQ_TEXT_MUTED = "#9A9AA4"
LQ_TEXT_FAINT = "#5C5C64"
LQ_GOLD = "#D7FF4E"     # Plutos vurgu rengi (asit-lime, eski adı korunuyor ki geri kalan kod değişmesin)
LQ_GOLD_STRONG = "#E6FF80"
LQ_GREEN = "#089981"   # TradingView standardıyla hizalı — mum grafiğiyle bire bir tutarlı
LQ_RED = "#F23645"
LQ_COLORWAY = [LQ_GOLD, "#5B8DEF", LQ_GREEN, "#B180E0", LQ_RED, "#4AB8C4"]


def lq_grafik_temasi(fig, **overrides):
    """
    Uygulamadaki TÜM Plotly grafiklerinin ortak zemin/ızgara/font/renk paleti.
    Var olan fig.update_layout(...) çağrısından SONRA çağrılır; Plotly update_layout
    çağrıları birikimli olduğu için (merge), önceki height/margin/title gibi
    ayarları BOZMADAN sadece görsel kimliği (arka plan, ızgara, font, renk sırası)
    tüm grafiklere tek noktadan uygular.
    """
    base = dict(
        paper_bgcolor=LQ_SURFACE,
        plot_bgcolor=LQ_SURFACE,
        font=dict(family="Inter, sans-serif", color=LQ_TEXT_MUTED, size=12),
        title_font=dict(family="Space Grotesk, sans-serif", color=LQ_TEXT, size=16),
        colorway=LQ_COLORWAY,
        legend=dict(font=dict(color=LQ_TEXT_MUTED, size=11), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=LQ_BG, bordercolor=LQ_GRID, font=dict(family="JetBrains Mono, monospace", color=LQ_TEXT)),
    )
    base.update(overrides)
    fig.update_layout(**base)
    fig.update_xaxes(gridcolor=LQ_GRID, zerolinecolor=LQ_GRID, linecolor=LQ_GRID)
    fig.update_yaxes(gridcolor=LQ_GRID, zerolinecolor=LQ_GRID, linecolor=LQ_GRID)
    return fig

# --- 1. VERİTABANI VE OTURUM YÖNETİMİ ---
# GÜNCELLEME (Faz 1): Artık users_master_db.json yerine db.py üzerinden gerçek bir
# veritabanı kullanılıyor (yerelde SQLite, üründe DATABASE_URL ile Postgres/Supabase).
# db_yukle()/db_kaydet() imzaları bilerek eskisiyle aynı bırakıldı, böylece bu
# fonksiyonları çağıran hiçbir yer değişmek zorunda kalmadı.
from db import get_all_users_as_dict, upsert_users_from_dict

def db_yukle():
    return get_all_users_as_dict()

def db_kaydet(db):
    upsert_users_from_dict(db)

def get_initial_portfolio():
    return {
        "FROTO": {"lot": 101, "maliyet": 93.45, "hedef": "Temettü"},
        "TUPRS": {"lot": 30, "maliyet": 145.0, "hedef": "Stratejik"},
        "MGROS": {"lot": 15, "maliyet": 460.0, "hedef": "Büyüme"},
        "THYAO": {"lot": 20, "maliyet": 290.0, "hedef": "Küresel"},
        "AKSEN": {"lot": 50, "maliyet": 38.0, "hedef": "Enerji"}
    }

# Session State'i dosyaya bağla
if 'kullanici_db' not in st.session_state:
    st.session_state['kullanici_db'] = db_yukle()

# --- PORTFÖY HAFIZASI (GÜNCEL LİSTEN) ---
if 'portfoy' not in st.session_state:
    st.session_state['portfoy'] = {
        "FROTO": {"lot": 101, "maliyet": 93.45, "hedef": "Temettü"},
        "TUPRS": {"lot": 30, "maliyet": 145.0, "hedef": "Stratejik"},
        "MGROS": {"lot": 15, "maliyet": 460.0, "hedef": "Büyüme"},
        "THYAO": {"lot": 20, "maliyet": 290.0, "hedef": "Küresel"},
        "AKSEN": {"lot": 50, "maliyet": 38.0, "hedef": "Enerji"},
        "EREGL": {"lot": 50, "maliyet": 31.29, "hedef": "Temettü"},
        "ENJSA": {"lot": 15, "maliyet": 109.0, "hedef": "Temettü"}
    }

if 'giris_yapan_kullanici' not in st.session_state:
    st.session_state['giris_yapan_kullanici'] = None

# --- 2. DİNAMİK KARŞILAMA ---
def dinamik_karsilama():
    saat = datetime.datetime.now().hour
    if 5 <= saat < 12: return "Günaydın"
    elif 12 <= saat < 18: return "İyi Günler"
    elif 18 <= saat < 24: return "İyi Akşamlar"
    else: return "İyi Geceler"

# --- 3. KAYIT VE GİRİŞ EKRANI FONKSİYONU ---
def giris_kayit_ekrani():
    st.markdown("""
    <style>
        .lq-hero {
            background: var(--bg-elevated, #0C0C0F);
            border: 1px solid var(--border, #232327);
            border-radius: 8px; padding: 46px 38px; height: 100%;
            position: relative; overflow: hidden;
        }
        .lq-hero::before {
            content: ""; position: absolute; top: -40%; right: -30%;
            width: 320px; height: 320px; border-radius: 50%;
            background: radial-gradient(circle, rgba(215,255,78,0.10), transparent 70%);
        }
        .lq-hero-logo {
            display: flex; align-items: center; gap: 10px; margin-bottom: 28px;
        }
        .lq-hero-logo span {
            font-family: 'Space Grotesk', sans-serif; font-size: 15px; font-weight: 700;
            color: #F7F7F8; letter-spacing: 0.04em; text-transform: uppercase;
        }
        .lq-hero-eyebrow {
            color: #D7FF4E; text-transform: uppercase; letter-spacing: 0.14em;
            font-size: 12px; font-weight: 700; margin-bottom: 14px;
        }
        .lq-hero-title {
            font-family: 'Space Grotesk', sans-serif; font-size: 34px; font-weight: 600;
            color: #F7F7F8; line-height: 1.2; margin-bottom: 14px;
        }
        .lq-hero-desc { color: #9A9AA4; font-size: 14.5px; line-height: 1.7; max-width: 380px; }
        .lq-hero-tickers {
            margin-top: 34px; display: flex; flex-wrap: wrap; gap: 8px;
        }
        .lq-hero-tickers span {
            font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #9A9AA4;
            border: 1px solid #232327; border-radius: 4px; padding: 4px 9px;
        }
        .lq-form-card {
            background: #131316; border: 1px solid #232327; border-radius: 8px;
            padding: 34px 32px; height: 100%;
        }
    </style>
    """, unsafe_allow_html=True)

    col_hero, col_form = st.columns([1, 1], gap="large")

    with col_hero:
        st.markdown(f"""
        <div class="lq-hero">
            <div class="lq-hero-logo">{plutos_logo_svg(28)}<span>Plutos</span></div>
            <div class="lq-hero-eyebrow">Plutos Terminal</div>
            <div class="lq-hero-title">BIST için kurumsal<br>düzeyde bir kokpit.</div>
            <div class="lq-hero-desc">
                Portföyünüzü, teknik sinyalleri ve piyasa taramasını tek ekranda toplayan
                kişisel yatırım terminaliniz. Devam etmek için giriş yapın ya da yeni bir
                hesap oluşturun.
            </div>
            <div class="lq-hero-tickers">
                <span>THYAO</span><span>TUPRS</span><span>FROTO</span><span>AKBNK</span><span>EREGL</span><span>ASELS</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        st.markdown('<div class="lq-form-card">', unsafe_allow_html=True)
        tab_giris, tab_kayit = st.tabs(["Giriş", "Kayıt"])
        
        # KAYIT FORMU 
        with tab_kayit:
            with st.form("kayit_formu", clear_on_submit=True):
                kayit_ad = st.text_input("Adınız*")
                kayit_soyad = st.text_input("Soyadınız*")
                kayit_dt = st.date_input("Doğum Tarihiniz*", min_value=datetime.date(1940, 1, 1))
                kayit_email = st.text_input("E-Posta Adresiniz*")
                kayit_sifre = st.text_input("Şifre*", type="password")
                kayit_buton = st.form_submit_button("Kayıt Ol", use_container_width=True, type="primary")
                
                if kayit_buton:
                    if not kayit_ad or not kayit_soyad or not kayit_email or not kayit_sifre:
                        st.error("Lütfen tüm zorunlu alanları doldurun!")
                    else:
                        st.session_state['kullanici_db'][kayit_email] = {
                            "ad": kayit_ad.strip().title(),
                            "soyad": kayit_soyad.strip().title(),
                            "dt": str(kayit_dt),
                            "password": hash_password(kayit_sifre)  # bcrypt + salt
                        }
                        db_kaydet(st.session_state['kullanici_db']) 
                        st.success("Kayıt Başarılı!")
        
        # GİRİŞ FORMU
        with tab_giris:
            with st.form("giris_formu"):
                giris_email = st.text_input("E-Posta:")
                giris_sifre = st.text_input("Şifre:", type="password")
                giris_buton = st.form_submit_button("Giriş Yap", use_container_width=True, type="primary")
                
                if giris_buton:
                    kayitli_kullanici = st.session_state['kullanici_db'].get(giris_email)
                    stored_hash = kayitli_kullanici.get("password") if kayitli_kullanici else None

                    if kayitli_kullanici and verify_password(giris_sifre, stored_hash):
                        # Şeffaf migration: eski (SHA256/tuzsuz) hash bulunursa
                        # başarılı girişte sessizce bcrypt'e yükselt.
                        if needs_rehash(stored_hash):
                            kayitli_kullanici["password"] = hash_password(giris_sifre)
                            st.session_state['kullanici_db'][giris_email] = kayitli_kullanici
                            db_kaydet(st.session_state['kullanici_db'])

                        st.session_state['giris_yapan_kullanici'] = kayitli_kullanici
                        st.session_state['user_email'] = giris_email
                        st.rerun() 
                    else:
                        st.error("E-posta veya şifre hatalı!")
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================================
# 4. ANA YÖNLENDİRME AKIŞI (ROUTING)
# ==========================================================

# EĞER GİRİŞ YAPILMAMIŞSA
if st.session_state['giris_yapan_kullanici'] is None:
    try: uygula_global_css() 
    except: pass
    giris_kayit_ekrani()
    st.stop()
# EĞER GİRİŞ YAPILMIŞSA
else:
    # Kullanıcı verilerini çek
    kullanici_verisi = st.session_state.get('giris_yapan_kullanici', {})
    
    if 'portfolio' not in st.session_state:
        # Eğer yeni kullanıcıysa veya portföyü yoksa, get_initial_portfolio() ile varsayılanı yükle
        st.session_state.portfolio = kullanici_verisi.get("portfolio", get_initial_portfolio())

    if 'virtual_cash' not in st.session_state:
        st.session_state.virtual_cash = kullanici_verisi.get("virtual_cash", 100000.0)
    if 'trade_log' not in st.session_state:
        st.session_state.trade_log = kullanici_verisi.get("trade_log", [])
    if 'price_alarms' not in st.session_state:
        st.session_state.price_alarms = kullanici_verisi.get("price_alarms", [])

    ad = kullanici_verisi.get("ad", "Kullanıcı")
    soyad = kullanici_verisi.get("soyad", "")
    tam_isim = f"{ad} {soyad}"
    bas_harf = ad[0].upper()

# YAN MENÜ PROFİL KARTI 
st.sidebar.markdown(f"""
    <div style="background: #131316; padding: 16px; border-radius: 8px; border: 1px solid #232327; margin-bottom: 22px; display: flex; align-items: center; gap: 14px;">
        <div style="background: #0C0C0F; color: #D7FF4E; border: 1.5px solid #D7FF4E; border-radius: 50%; min-width: 42px; height: 42px; display: flex; justify-content: center; align-items: center; font-size: 17px; font-weight: 700; font-family: 'Space Grotesk', sans-serif;">
            {bas_harf}
        </div>
        <div>
            <div style="color: #9A9AA4; font-size: 12px;">{dinamik_karsilama()},</div>
            <div style="color: #F7F7F8; font-size: 15px; font-weight: 600;">{tam_isim}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Çıkış Butonu
if st.sidebar.button("Çıkış Yap", use_container_width=True):
    st.session_state['giris_yapan_kullanici'] = None
    st.rerun()

st.sidebar.markdown("<hr>", unsafe_allow_html=True)



# =================================================================
# 1. AYARLAR VE VERİTABANI
# =================================================================
uygula_global_css()
BACKTEST_FILE = "backtest_history.csv"

# =================================================================
# BIST TÜM HİSSELERİ 
# =================================================================
BIST_TUM_LIST = sorted([
    "A1CAP", "ACSEL", "ADEL", "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AGYO", 
    "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSGY", 
    "AKSUE", "AKYHO", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", 
    "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARCLK", "ARDYZ", 
    "ARENA", "ARSAN", "ARTMS", "ARZUM", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATAKP", 
    "ATPCO", "AVGYO", "AVHOL", "AVOD", "AVPGY", "AYCES", "AYDEM", "AYEN", "AYES", "AYGAZ", 
    "AZTEK", "BAGFS", "BAKAB", "BALAT", "BANVT", "BARMA", "BASCM", "BASGZ", "BAYRK", "BEGYO", 
    "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIOEN", "BIZIM", "BJKAS", "BLCYT", 
    "BMSCH", "BMSTL", "BNTAS", "BOBET", "BORLS", "BOSSA", "BRISA", "BRKO", "BRKSN", "BRKVY", 
    "BRLSM", "BRMEN", "BRSAN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", 
    "BYDNR", "CANTE", "CATES", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEOEM", "CIMSA", "CLEBI", 
    "CMBTN", "CMENT", "CONSE", "COSMO", "CRDFA", "CRFSA", "CUSAN", "CVKMD", "CWENE", "DAGHL", 
    "DAGI", "DAPGM", "DARDL", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA", "DGATE", 
    "DGGYO", "DGNMO", "DIRIT", "DITAS", "DMSAS", "DNISI", "DOAS", "DOBUR", "DOCO", "DOGUB", 
    "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", 
    "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKIZ", "EKSUN", "ELITE", "EMKEL", 
    "EMNIS", "ENJSA", "ENKAI", "ENSRI", "ENTRA", "EPLAS", "ERBOS", "ERCB", "EREGL", "ERSU", 
    "ESCAR", "ESCOM", "ESEN", "ETILR", "ETYAT", "EUHOL", "EUKYO", "EUPWR", "EUREN", "EUYO", 
    "EYGYO", "FADE", "FENER", "FLAP", "FMIZP", "FONET", "FORMT", "FORTE", "FRIGO", "FROTO", 
    "FZLGY", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GLBMD", 
    "GLCVY", "GLRYH", "GLYHO", "GMTAS", "GOKNR", "GOLTS", "GOODY", "GOZDE", "GRNYO", "GRSEL", 
    "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATEK", "HATSN", "HDFGS", 
    "HEDEF", "HEKTS", "HKTM", "HLGYO", "HITIT", "HRKET", "HTTBT", "HUBVC", "HUNER", "HURGZ", 
    "ICBCT", "IDEAS", "IDGYO", "IEYHO", "IHAAS", "IHEVA", "IHGZT", "IMASM", "INDES", "INFO", 
    "INGRM", "INTEM", "INVEO", "INVES", "IPEKE", "ISATR", "ISBIR", "ISBTR", "ISCTR", "ISDMR", 
    "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISKUR", "ISMEN", "ISSEN", "ISYAT", "ITTFH", "IZENR", 
    "IZFAS", "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARYE", "KATMR", "KAYSE", 
    "KCAER", "KCMKW", "KENT", "KERVN", "KERVT", "KFEIN", "KGYO", "KIMMR", "KLGYO", "KLKIM", 
    "KLMSN", "KLNMA", "KLRHO", "KLSER", "KMPUR", "KNFRT", "KBORU", "KONKA", "KONTR", "KONYA", 
    "KOPOL", "KORDS", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", 
    "KRSTL", "KRTEK", "KRVGD", "KSTUR", "KTLEV", "KTSKR", "KUTPO", "KUVVA", "KUYAS", "KZBGY", 
    "KZGYO", "LIDER", "LIDFA", "LINK", "LKMNH", "LOGO", "LRSHO", "LUKSK", "MAALT", "MACKO", 
    "MAGEN", "MAKIM", "MAKTK", "MANAS", "MARBL", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", 
    "MEGMT", "MEKAG", "MENDO", "MERCN", "MERIT", "MERKO", "METRO", "METUR", "MGROS", "MIATK", 
    "MIPAZ", "MMCAS", "MNDRS", "MNDTR", "MOBTL", "MOGAN", "MPARK", "MRGYO", "MRSHL", "MSGYO", 
    "MTRKS", "MTRYO", "MUNDA", "NATA", "NETAS", "NIBAS", "NTGAZ", "NTHOL", "NUGYO", "NUHCM", 
    "OBAMS", "ODAS", "OFFSYM", "ONCSM", "ORCAY", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", 
    "OTTO", "OYAKC", "OYAYO", "OYLUM", "OYYAT", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO", 
    "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT", "PEGYO", "PEKGY", "PENGD", "PENTA", "PETKM", 
    "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PLAT", "PLTUR", "PNLSN", "PNSUT", "POLHO", 
    "POLTK", "PRDGS", "PRKAB", "PRKME", "PRZMA", "PSDTC", "PSGYO", "QNBFB", "QNBFL", "QUAGR", 
    "RALYH", "RAYSG", "RNPOL", "RODRG", "ROYAL", "RTALB", "RUBNS", "RYGYO", "RYSAS", "SAFKR", 
    "SAHOL", "SAMAT", "SANEL", "SANFM", "SANKO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEKFK", 
    "SEKUR", "SELEC", "SELGD", "SELVA", "SEYKM", "SILVR", "SISE", "SKBNK", "SKTAS", "SMART", 
    "SMRTG", "SNGYO", "SNKRN", "SNPAM", "SODSN", "SOKE", "SOKM", "SONME", "SRVGY", "SUMAS", 
    "SUNTK", "SURGY", "SUWEN", "TABGD", "TARKM", "TATEN", "TATGD", "TAVHL", "TBORG", "TCELL", 
    "TDGYO", "TEKTU", "TERA", "TETMT", "TEZOL", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", 
    "TMPOL", "TMSN", "TNZTP", "TOASO", "TRCAS", "TRGYO", "TRILC", "TSGYO", "TSKB", "TSPOR", 
    "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TURGG", "TURSG", "UFUK", "ULAS", "ULKER", 
    "ULUFA", "ULUSE", "ULUUN", "UMPAS", "UNLU", "USAK", "UZERB", "VAKBN", "VAKFN", "VAKKO", 
    "VANGD", "VBTYZ", "VERUS", "VESBE", "VESTL", "VKFYO", "VKGYO", "VKING", "VRGYO", "YAPRK", 
    "YATAS", "YAYLA", "YEOTK", "YESIL", "YGGYO", "YGYO", "YKBNK", "YKSLN", "YONGA", "YUNSA", 
    "YYAPI", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"
])

# =================================================================
# 2. MOTOR ENTEGRASYONU
# =================================================================

class AkYatirimEngine:
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_daily_technical_levels():
        try:
            url = "https://www.akyatirim.com.tr/arastirma-raporlari"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                sup = re.search(r"BIST100 için ([\d\–\/]+) destek", text)
                res = re.search(r"([\d\–\-]+) direnç", text)
                s = sup.group(1).replace('–', '-').split('-') if sup else ["13681", "13400"]
                r = res.group(1).replace('–', '-').split('-') if res else ["13913", "14200"]
                return s, r
        except: pass
        return ["13600", "13400"], ["13900", "14150"]

try:
    from data_engine import DataEngine, son_gecerli_satirlar
    from ml_engine import MLEngine
    data_engine = DataEngine()
    ml_engine = MLEngine()
except ImportError:
    st.error("KRİTİK HATA: 'data_engine.py' veya 'ml_engine.py' bulunamadı!")
    st.stop()

# =================================================================
# 3. YARDIMCI FONKSİYONLAR
# =================================================================
# load_master_db/save_master_db de aynı sebeple db.py'ye yönlendirildi (bkz. db_yukle/db_kaydet).
def load_master_db():
    return get_all_users_as_dict()

def save_master_db(db):
    upsert_users_from_dict(db)

def get_initial_portfolio():
    return {
        "FROTO": {"lot": 101, "maliyet": 93.45, "hedef": "Temettü"},
        "TUPRS": {"lot": 30, "maliyet": 145.0, "hedef": "Stratejik"},
        "MGROS": {"lot": 15, "maliyet": 460.0, "hedef": "Büyüme"},
        "THYAO": {"lot": 20, "maliyet": 290.0, "hedef": "Küresel"},
        "AKSEN": {"lot": 50, "maliyet": 38.0, "hedef": "Enerji"}
    }
# --- HIZLI VERİ ÇEKME MOTORU ---
@st.cache_data(ttl=900, show_spinner=False)
def hizli_veri_cek(sembol):
    try:
        t = yf.Ticker(f"{sembol}.IS")
        hist = t.history(period="1y") 
        if hist.empty: 
            return pd.DataFrame(), 0.0, 0.0

        # Borsa kapalıyken veya seans öncesinde yfinance'in eklediği son satırın
        # Close değeri NaN, ya da Volume=0 olan "taslak" bir satır olabiliyor.
        # Bu satırı atıp SON GEÇERLİ (gerçekten kapanmış) fiyatı baz alıyoruz.
        hist = son_gecerli_satirlar(hist)
        if hist.empty:
            return pd.DataFrame(), 0.0, 0.0

        cp = float(hist['Close'].iloc[-1])
        yillik_temettu = 0.0
        
        try:
            if 'Dividends' in hist.columns:
                yillik_temettu = float(hist['Dividends'].sum())
        except Exception as div_err:
            print(f"[{sembol}] Temettü hesaplama hatası: {div_err}")
            yillik_temettu = 0.0
                
        div_yield = (yillik_temettu / cp) if cp > 0 else 0.0
        
        return hist, div_yield, yillik_temettu
        
    except Exception as e:
        print(f"[{sembol}] Genel veri çekme hatası: {e}")
        return pd.DataFrame(), 0.0, 0.0
# --- RADAR MOTORU (YARDIMCI FONKSİYONLAR BÖLÜMÜ) ---
@st.cache_data(ttl=1800, show_spinner=False)
def asenkron_bist_tara(hisse_listesi):
    def tek_hisse_analiz(sembol):
        try:
            hist = yf.Ticker(f"{sembol}.IS").history(period="3mo")
            hist = son_gecerli_satirlar(hist)  # borsa kapalıyken/taslak satırı at
            if len(hist) < 35: 
                return None
                
            close = hist['Close']
            fiyat = float(close.iloc[-1])
            
            rsi = float(ta.rsi(close, length=14).iloc[-1])
            sma20 = float(ta.sma(close, length=20).iloc[-1])
            sma50 = float(ta.sma(close, length=50).iloc[-1])
            macd = ta.macd(close)
            macd_line = float(macd.iloc[-1, 0])
            macd_signal = float(macd.iloc[-1, 2])
            
            durum = "Nötr 🟡"
            puan = 0
            
            if rsi < 35: puan += 2
            elif rsi > 70: puan -= 2
            
            if fiyat > sma50: puan += 1
            else: puan -= 1
                
            if macd_line > macd_signal: puan += 1
            else: puan -= 1
            
            if puan >= 3: durum = "Güçlü Al 🟢"
            elif puan == 2: durum = "Topla 🟢"
            elif puan <= -3: durum = "Güçlü Sat 🔴"
            elif puan == -2: durum = "Dikkat 🔴"

            trend = "Pozitif 📈" if fiyat > sma50 else "Negatif 📉"

            return {
                "Hisse": sembol,
                "Fiyat": f"{fiyat:.2f} ₺",
                "RSI (14)": round(rsi, 2),
                "Trend (SMA50)": trend,
                "MACD": "Alış 🟢" if macd_line > macd_signal else "Satış 🔴",
                "Yapay Zeka Sinyali": durum,
                "_puan": puan 
            }
        except Exception:
            return None

    sonuclar = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        gelecek_sonuclar = {executor.submit(tek_hisse_analiz, s): s for s in hisse_listesi}
        for future in as_completed(gelecek_sonuclar):
            veri = future.result()
            if veri:
                sonuclar.append(veri)
                
    return pd.DataFrame(sonuclar)


def sirala_radar_sonuclari(df):
    if df.empty:
        return df

    trend_rank = {"Pozitif 📈": 1, "Negatif 📉": 0}
    macd_rank = {"Alış 🟢": 1, "Satış 🔴": 0}
    sinyal_rank = {
        "Güçlü Al 🟢": 4,
        "Topla 🟢": 3,
        "Nötr 🟡": 2,
        "Dikkat 🔴": 1,
        "Güçlü Sat 🔴": 0
    }

    df2 = df.copy()
    df2["_trend_sort"] = df2["Trend (SMA50)"].map(trend_rank).fillna(0)
    df2["_macd_sort"] = df2["MACD"].map(macd_rank).fillna(0)
    df2["_sinyal_sort"] = df2["Yapay Zeka Sinyali"].map(sinyal_rank).fillna(0)

    sorted_df = df2.sort_values(
        by=["_puan", "RSI (14)", "_trend_sort", "_macd_sort", "_sinyal_sort"],
        ascending=[False, False, False, False, False],
        kind="mergesort"
    )

    return sorted_df.drop(columns=["_trend_sort", "_macd_sort", "_sinyal_sort"])

# --- BACKTEST TOPLU KAYIT MOTORU ---
BACKTEST_FILE = "backtest_history.csv"

def backteste_toplu_ekle(df_kayit):
    import os
    import pandas as pd
    from datetime import datetime
    
    # Gelen tablodaki tüm satırları alıp Backtest formatına çeviriyoruz
    yeni_veri = pd.DataFrame({
        "Tarih": datetime.now().strftime("%Y-%m-%d"),
        "Hisse": df_kayit["Hisse"],
        "Fiyat": df_kayit["Fiyat"],
        "Sinyal": df_kayit["Yapay Zeka Sinyali"]
    })
    
    if os.path.exists(BACKTEST_FILE):
        df_eski = pd.read_csv(BACKTEST_FILE)
        df_son = pd.concat([df_eski, yeni_veri], ignore_index=True)
    else:
        df_son = yeni_veri
        
    df_son.to_csv(BACKTEST_FILE, index=False)
    
def calculate_support_resistance_levels(df, window=20):
    if len(df) < window: return [], []
    v = df['Close'].values
    sup_idx = argrelextrema(v, np.less_equal, order=window)[0]
    res_idx = argrelextrema(v, np.greater_equal, order=window)[0]
    return sorted(list(set(v[sup_idx]))), sorted(list(set(v[res_idx])))

def calculate_risk_metrics(df):
    if df.empty: return 0, 0, 0
    returns = df['Close'].pct_change().dropna()
    vol = returns.std() * np.sqrt(252)
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
    cum = (1 + returns).cumprod()
    dd = (cum / cum.cummax()) - 1
    max_dd = dd.min()
    return vol, sharpe, max_dd

def check_security_thresholds(stock, current_p, supports):
    if 'notifications' not in st.session_state: st.session_state.notifications = []
    if supports:
        nearest = max([s for s in supports if s < current_p], default=0)
        if nearest > 0 and (current_p - nearest)/nearest < 0.01:
            msg = f"{stock} Destek Bölgesinde: {nearest:.2f}"
            if not any(n['msg'] == msg for n in st.session_state.notifications):
                st.session_state.notifications.insert(0, {"time": datetime.datetime.now().strftime("%H:%M"), "msg": msg})

# Ana Sayfa'daki "en çok yükselen/düşen" taraması için: 600+ hisseli tam listeyi
# her sayfa yenilemesinde tek tek taramak hem çok yavaş hem de Yahoo Finance'i
# tetikleyip veri gelmemesine yol açabiliyor. Bunun yerine likit/en çok işlem
# gören ~40 hisseden oluşan bir alt küme kullanıyoruz (BIST30 + birkaç popüler isim).
# Sektör Karşılaştırma modülü için kabaca sektör -> hisse eşlemesi (BIST'te resmi/eksiksiz
# bir sektör API'si olmadığından, bilinen büyük/likit isimlerle elle küratörlü liste).
BIST_SEKTORLER = {
    "Bankacılık": ["AKBNK", "GARAN", "ISCTR", "YKBNK", "VAKBN", "HALKB", "TSKB", "ALBRK"],
    "Havacılık & Ulaştırma": ["THYAO", "PGSUS", "TAVHL", "CLEBI", "GSDHO"],
    "Otomotiv & Sanayi": ["FROTO", "TOASO", "ASUZU", "OTKAR", "TTRAK", "KARSN", "BRSAN"],
    "Perakende & Gıda": ["BIMAS", "MGROS", "SOKM", "CCOLA", "AEFES", "ULKER", "CRFSA"],
    "Enerji & Petrokimya": ["TUPRS", "PETKM", "AKSEN", "AYDEM", "ENJSA", "ODAS", "ZOREN"],
    "Demir-Çelik & Madencilik": ["EREGL", "KRDMD", "KOZAL", "KOZAA", "ISDMR"],
    "Teknoloji & Savunma": ["ASELS", "ALFAS", "LOGO", "KAREL", "ARDYZ"],
    "Holding": ["KCHOL", "SAHOL", "SASA", "AGHOL", "ALARK", "DOAS"],
}

ANA_SAYFA_TARAMA_LISTESI = [
    "THYAO", "AKBNK", "GARAN", "ISCTR", "KCHOL", "SASA", "EREGL", "BIMAS", "ASELS", "TUPRS",
    "SISE", "PETKM", "FROTO", "TOASO", "TCELL", "YKBNK", "VAKBN", "HALKB", "PGSUS", "MGROS",
    "ENKAI", "KOZAL", "KOZAA", "TAVHL", "AEFES", "CCOLA", "ULKER", "DOAS", "OTKAR", "ARCLK",
    "VESTL", "KRDMD", "EKGYO", "GUBRF", "ALARK", "SAHOL", "TTKOM", "TKFEN", "ODAS", "ZOREN",
]


@st.cache_data(ttl=900, show_spinner=False)
def piyasa_ozeti_getir():
    """
    Ana Sayfa için: XU100 endeksi + likit hisse alt kümesinde günlük en çok
    yükselen/düşenler. hizli_veri_cek ile AYNI, kanıtlanmış çalışan yöntemi kullanır
    (tek tek yf.Ticker(...).history + son_gecerli_satirlar) — toplu yf.download YAPMAZ,
    çünkü büyük listede toplu indirme sessizce boş/parçalı veri döndürebiliyor.
    """
    endeks = {"deger": None, "degisim": None}
    hata_detaylari = []

    try:
        idx_hist, _, _ = hizli_veri_cek("XU100")
        if len(idx_hist) >= 2:
            endeks["deger"] = float(idx_hist["Close"].iloc[-1])
            onceki = float(idx_hist["Close"].iloc[-2])
            endeks["degisim"] = (endeks["deger"] / onceki - 1) * 100
        elif idx_hist.empty:
            hata_detaylari.append("XU100: hizli_veri_cek boş DataFrame döndürdü (veri gelmedi).")
        else:
            hata_detaylari.append("XU100: en az 2 günlük veri yok (tek satır geldi).")
    except Exception as e:
        hata_detaylari.append(f"XU100: {type(e).__name__}: {e}")

    sonuclar = []
    for s in ANA_SAYFA_TARAMA_LISTESI:
        try:
            hist, _, _ = hizli_veri_cek(s)
            if len(hist) < 2:
                continue
            close = hist["Close"]
            son = float(close.iloc[-1])
            onceki = float(close.iloc[-2])
            if onceki <= 0:
                continue
            sonuclar.append({
                "Hisse": s, "Fiyat": son, "Değişim %": (son / onceki - 1) * 100,
                "Trend": close.tail(15).tolist(),
            })
        except Exception as e:
            hata_detaylari.append(f"{s}: {type(e).__name__}: {e}")
            continue

    df_ozet = pd.DataFrame(sonuclar)
    return endeks, df_ozet, hata_detaylari


def check_price_alarms():
    """Kullanıcının tanımladığı fiyat alarmlarını kontrol eder, tetiklenenleri bildirimlere ekler."""
    if 'price_alarms' not in st.session_state: st.session_state.price_alarms = []
    if 'notifications' not in st.session_state: st.session_state.notifications = []

    yeni_tetiklenen = False
    for alarm in st.session_state.price_alarms:
        if alarm.get('tetiklendi'):
            continue
        try:
            h, _, _ = hizli_veri_cek(alarm['hisse'])
            if h.empty:
                continue
            fiyat = float(h['Close'].iloc[-1])
        except Exception:
            continue

        kosul = (
            (alarm['yon'] == "Üzerine Çıkınca" and fiyat >= alarm['esik']) or
            (alarm['yon'] == "Altına İnince" and fiyat <= alarm['esik'])
        )
        if kosul:
            yon_metin = "üzerine çıktı" if alarm['yon'] == "Üzerine Çıkınca" else "altına indi"
            msg = f"🔔 {alarm['hisse']} {alarm['esik']:.2f} ₺ {yon_metin}: güncel {fiyat:.2f} ₺"
            if not any(n['msg'] == msg for n in st.session_state.notifications):
                st.session_state.notifications.insert(0, {"time": datetime.datetime.now().strftime("%H:%M"), "msg": msg})
            alarm['tetiklendi'] = True
            yeni_tetiklenen = True

    if yeni_tetiklenen:
        d = load_master_db()
        if st.session_state.get('user_email') in d:
            d[st.session_state.user_email]['price_alarms'] = st.session_state.price_alarms
            save_master_db(d)

# =================================================================
# 4. GİRİŞ VE MENÜ
# =================================================================
prec = st.sidebar.selectbox("Hassasiyet", ["Günlük", "Saatlik", "Canlı"])

if prec == "Günlük":
    p_int = "1d"
    opts = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    def_opt = "1y"
elif prec == "Saatlik":
    p_int = "1h"
    opts = ["1mo", "3mo", "6mo", "1y", "2y"]
    def_opt = "6mo"
else: # Canlı
    p_int = "1m"
    opts = ["1s","5s","30s","1d", "5d", "7d"]
    def_opt = "1d"

p_per = st.sidebar.selectbox("Geçmiş Peryodu", options=opts, index=opts.index(def_opt) if def_opt in opts else 0)

with st.sidebar.expander("Portföy İşlemleri"):
    crud = st.radio("İşlem Tipi:", ["Güncelle", "Ekle", "Sil"])
    
    # 1. GÜNCELLEME MODU
    if crud == "Güncelle" and st.session_state.portfolio:
        s = st.selectbox("Hisse Seç:", list(st.session_state.portfolio.keys()))
        l = st.number_input("Güncel Lot:", value=int(st.session_state.portfolio[s]['lot']))
        c = st.number_input("Güncel Maliyet:", value=float(st.session_state.portfolio[s]['maliyet']))
        if st.button("KAYDET"):
            st.session_state.portfolio[s].update({'lot': l, 'maliyet': c})
            d = load_master_db()
            d[st.session_state.user_email]['portfolio'] = st.session_state.portfolio
            save_master_db(d)
            st.success("Güncellendi!")
            time.sleep(0.5); st.rerun()
            
    # 2. EKLEME MODU
    elif crud == "Ekle":
        n = st.selectbox("Hisse Ekle:", BIST_TUM_LIST)
        nl = st.number_input("Lot Adedi:", min_value=1, value=10)
        nc = st.number_input("Maliyet:", min_value=0.0, value=10.0)
        if st.button("PORTFÖYE EKLE"):
            st.session_state.portfolio[n] = {"lot": nl, "maliyet": nc, "hedef": "Yeni"}
            d = load_master_db()
            d[st.session_state.user_email]['portfolio'] = st.session_state.portfolio
            save_master_db(d)
            st.success("Eklendi!")
            time.sleep(0.5); st.rerun()

    # 3. SİLME MODU (YENİ EKLENEN KISIM)
    elif crud == "Sil" and st.session_state.portfolio:
        s_del = st.selectbox("Silinecek Hisse:", list(st.session_state.portfolio.keys()))
        st.warning(f"{s_del} portföyden kalıcı olarak silinecek.")
        if st.button("🗑️ HİSSEYİ SİL", type="primary"):
            del st.session_state.portfolio[s_del]
            d = load_master_db()
            d[st.session_state.user_email]['portfolio'] = st.session_state.portfolio
            save_master_db(d)
            st.rerun()

check_price_alarms()
notif_bc = len(st.session_state.get('notifications', []))

# ==========================================================
# PLUTOS ÜST NAVBAR — kategorilere ayrılmış, web sitesi tarzı sekmeler
# ==========================================================
PLUTOS_KATEGORILER = {
    "Analiz": ["Stratejik Analiz", "Piyasa Tarayıcı", "AI Gelecek", "Backtest", "Sektör Karşılaştırma", "Temettü"],
    "Portföy": ["Portföy İzleme", "İzleme Listesi", "Portföy Optimizasyonu", "Emir Ver (Demo)", "Performans & Risk"],
    "Araçlar": ["AI Asistan 🤖", "Finansal Özgürlük (FIRE)", "WhatsApp Botu", "Fiyat Alarmları"],
}
PLUTOS_UST_SEKMELER = ["Ana Sayfa"] + list(PLUTOS_KATEGORILER.keys())

if "plutos_show_notifs" not in st.session_state:
    st.session_state["plutos_show_notifs"] = False

col_brand, col_bell = st.columns([6, 1])
with col_brand:
    st.markdown(
        f'<div class="plutos-brand">{plutos_logo_svg(26)}<span>PLUTOS</span></div>',
        unsafe_allow_html=True,
    )
with col_bell:
    if st.button(f"🔔 {notif_bc}", key="plutos_bell_btn", help="Bildirimler"):
        st.session_state["plutos_show_notifs"] = not st.session_state["plutos_show_notifs"]

if st.session_state["plutos_show_notifs"]:
    mod_nav = f"Bildirimler ({notif_bc})"
    if st.button("← Panele dön", key="plutos_notif_back"):
        st.session_state["plutos_show_notifs"] = False
        st.rerun()
else:
    aktif_kategori = st.radio(
        "plutos_cat_nav", PLUTOS_UST_SEKMELER,
        horizontal=True, label_visibility="collapsed", key="plutos_cat",
    )
    if aktif_kategori == "Ana Sayfa":
        mod_nav = "Ana Sayfa"
    else:
        aktif_modul = st.radio(
            "plutos_mod_nav", PLUTOS_KATEGORILER[aktif_kategori],
            horizontal=True, label_visibility="collapsed", key=f"plutos_mod__{aktif_kategori}",
        )
        mod_nav = aktif_modul

st.markdown('<div style="margin-bottom:6px;"></div>', unsafe_allow_html=True)

# =================================================================
# 6. ANALİZ FRAGMANI (FRAKTAL ANALİZ VERSİYONU)
# =================================================================
def hisse_inceleme_ekrani(hisse_kodu):
    hisse_kodu = str(hisse_kodu).upper().strip().replace(".IS.IS", ".IS")
    sembol = hisse_kodu.replace(".IS", "")

    # Şık Ana Başlık
    st.markdown(
        f"<h2 style='text-align: center; color: {LQ_TEXT}; font-family: Fraunces, serif;'>"
        f"{sembol} <span style='color: {LQ_GOLD}; font-family: Inter, sans-serif; font-weight: 400;'>│</span> "
        f"<span style='font-family: Inter, sans-serif; font-size: 16px; color: {LQ_TEXT_MUTED}; font-weight: 400;'>Analiz</span></h2>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    # ==========================================================
    # 1. ÇİFT MOTORLU VERİ ÇEKME
    # ==========================================================
    df = pd.DataFrame()
    yf_hata, tv_hata = "Hata yok", "Hata yok"

    try:
        hisse = yf.Ticker(f"{sembol}.IS")
        df_yf = hisse.history(period="1y")
        if df_yf is not None and not df_yf.empty:
            df = df_yf
        else:
            yf_hata = "Yahoo Finance boş tablo döndürdü."
    except Exception as e:
        yf_hata = str(e)

    if df.empty:
        try:
            from tvDatafeed import TvDatafeed, Interval
            tv = TvDatafeed() 
            df_tv = tv.get_hist(symbol=sembol, exchange='BIST', interval=Interval.in_daily, n_bars=260)
            if df_tv is not None and not df_tv.empty:
                df = df_tv
                df.index.name = 'Date'
            else:
                tv_hata = "TradingView veriyi bulamadı."
        except Exception as e:
            tv_hata = str(e)

    if df.empty:
        st.error(f" '{sembol}' için veri çekme motorlarının ikisi de başarısız oldu!")
        st.warning(f"**Yahoo Finance:** {yf_hata} | **TradingView:** {tv_hata}")
        return
    
    # ==========================================================
    # ZORUNLU KÜÇÜK HARF VE VERİ TEMİZLİĞİ 
    # ==========================================================
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    # Her sütunu zorla küçük harfe çevir 
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()].copy()

    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df.dropna(subset=['close'], inplace=True)

    def get_col(prefix):
        p = prefix.lower()
        cols = [c for c in df.columns if str(c).lower().startswith(p)]
        return cols[0] if cols else None

    secilen_ana_grafik = []
    secilen_alt_grafik = []

    # 2. PANEL
    with st.expander(" Gelişmiş İndikatör & Algoritma Kütüphanesi", expanded=True):
        tab1, tab2, tab3, tab4 = st.tabs([" Trend (Ana)", " Osilatör (Alt)", " Volatilite & Hacim", " Özel Algoritma Yaz"])
        
        with tab1:
            secilen_ana_grafik = st.multiselect("Fiyat grafiğinin üzerine eklenecekler:", ["SMA 20", "SMA 50", "EMA 20", "EMA 50", "Bollinger Bantları", "Donchian Kanalları"])
        with tab2:
            osilatörler = st.multiselect("Alt panele eklenecek osilatörler:", ["RSI", "MACD", "Stochastic (STOCH)", "CCI"])
            secilen_alt_grafik.extend(osilatörler)
        with tab3:
            vol_hacim = st.multiselect("Volatilite ve Hacim:", ["ATR (Ortalama Gerçek Aralık)", "OBV (On Balance Volume)"])
            secilen_alt_grafik.extend(vol_hacim)
        with tab4:
            st.info("💡 İPUCU: Artık tüm veriler küçük harftir. (Örn: df['close'] - df['sma_20'])")
            ozel_formul = st.text_input("Matematiksel Formül:", placeholder="df['close'] - df['sma_20']")
            if ozel_formul:
                try:
                    if not get_col("sma_20"): df.ta.sma(length=20, append=True)
                    df['Ozel_Algoritma'] = eval(ozel_formul)
                    st.success("Algoritma başarıyla derlendi!")
                    secilen_alt_grafik.append("Özel Algoritma")
                except Exception as e:
                    st.error(f"Formül Hatası: Küçük harf kullandığınızdan emin olun (Örn: df['close']). Detay: {e}")

    # 3. KESİN HESAPLAMALAR
    if "SMA 20" in secilen_ana_grafik: df.ta.sma(length=20, append=True)
    if "SMA 50" in secilen_ana_grafik: df.ta.sma(length=50, append=True)
    if "EMA 20" in secilen_ana_grafik: df.ta.ema(length=20, append=True)
    if "EMA 50" in secilen_ana_grafik: df.ta.ema(length=50, append=True)
    if "Bollinger Bantları" in secilen_ana_grafik: df.ta.bbands(length=20, append=True)
    if "Donchian Kanalları" in secilen_ana_grafik: df.ta.donchian(append=True)

    if "RSI" in secilen_alt_grafik: df.ta.rsi(length=14, append=True)
    if "MACD" in secilen_alt_grafik: df.ta.macd(append=True)
    if "Stochastic (STOCH)" in secilen_alt_grafik: df.ta.stoch(append=True)
    if "CCI" in secilen_alt_grafik: df.ta.cci(append=True)
    if "ATR (Ortalama Gerçek Aralık)" in secilen_alt_grafik: df.ta.atr(append=True)
    if "OBV (On Balance Volume)" in secilen_alt_grafik: df.ta.obv(append=True)

    # 4. GRAFİK ALTYAPISI
    row_count = 1 + len(secilen_alt_grafik)
    row_heights = [0.6] + [(0.4 / len(secilen_alt_grafik))] * len(secilen_alt_grafik) if secilen_alt_grafik else [1]

    fig = make_subplots(
        rows=row_count, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=row_heights, subplot_titles=["Fiyat Grafiği"] + secilen_alt_grafik
    )

    # Fiyat Mumları
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Fiyat', increasing_line_color='#089981', decreasing_line_color='#f23645',
        increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'
    ), row=1, col=1)

    # 5. ANA GRAFİK ÇİZİMLERİ
    if "Bollinger Bantları" in secilen_ana_grafik:
        u_col, l_col = get_col("bbu"), get_col("bbl")
        if u_col and l_col:
            # Üst Bant: İnce ve hafif mavi çizgi
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=df[u_col], 
                line=dict(color='rgba(41, 98, 255, 0.4)', width=1), 
                name='BB Üst'
            ), row=1, col=1)
            
            # Alt Bant ve Dolgu: Sihrin gerçekleştiği "fillcolor" kısmı
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=df[l_col], 
                line=dict(color='rgba(41, 98, 255, 0.4)', width=1), 
                fill='tonexty', 
                fillcolor='rgba(41, 98, 255, 0.08)', # %8 şeffaflıkta ferah bir dolgu
                name='BB Alt'
            ), row=1, col=1)
            
    if "Donchian Kanalları" in secilen_ana_grafik:
        u_col, l_col = get_col("dcu"), get_col("dcl")
        if u_col and l_col:
            fig.add_trace(go.Scatter(x=df.index, y=df[u_col], line=dict(color='rgba(255, 152, 0, 0.4)', width=1, dash='dash'), name='DC Üst'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df[l_col], line=dict(color='rgba(255, 152, 0, 0.4)', width=1, dash='dash'), fill='tonexty', name='DC Alt'), row=1, col=1)

    if "SMA 20" in secilen_ana_grafik: 
        col = get_col("sma_20")
        if col: fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color='#2962FF', width=1.5), name='SMA 20'), row=1, col=1)
    if "SMA 50" in secilen_ana_grafik: 
        col = get_col("sma_50")
        if col: fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color='#FF9800', width=1.5), name='SMA 50'), row=1, col=1)
    if "EMA 20" in secilen_ana_grafik: 
        col = get_col("ema_20")
        if col: fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color='#E91E63', width=1.5), name='EMA 20'), row=1, col=1)
    if "EMA 50" in secilen_ana_grafik: 
        col = get_col("ema_50")
        if col: fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color='#9C27B0', width=1.5), name='EMA 50'), row=1, col=1)

    # 6. ALT GRAFİK ÇİZİMLERİ
    current_row = 2
    for alt_gosterge in secilen_alt_grafik:
        if alt_gosterge == "RSI":
            rsi_col = get_col("rsi")
            if rsi_col:
                fig.add_trace(go.Scatter(x=df.index, y=df[rsi_col], line=dict(color='#7E57C2', width=2), name='RSI'), row=current_row, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="rgba(242, 54, 69, 0.5)", row=current_row, col=1, line_width=1)
                fig.add_hline(y=30, line_dash="dash", line_color="rgba(8, 153, 129, 0.5)", row=current_row, col=1, line_width=1)
        
        elif alt_gosterge == "MACD":
            macd_col, signal_col, hist_col = get_col("macd_"), get_col("macds_"), get_col("macdh_")
            if macd_col and signal_col and hist_col:
                fig.add_trace(go.Scatter(x=df.index, y=df[macd_col], line=dict(color='#2962FF', width=1.5), name='MACD'), row=current_row, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df[signal_col], line=dict(color='#FF9800', width=1.5), name='Sinyal'), row=current_row, col=1)
                colors = ['#089981' if val >= 0 else '#f23645' for val in df[hist_col]]
                fig.add_trace(go.Bar(x=df.index, y=df[hist_col], marker_color=colors, name='MACD Hist'), row=current_row, col=1)
            
        elif alt_gosterge == "Stochastic (STOCH)":
            stoch_k, stoch_d = get_col("stochk"), get_col("stochd")
            if stoch_k and stoch_d:
                fig.add_trace(go.Scatter(x=df.index, y=df[stoch_k], line=dict(color='#03A9F4', width=1.5), name='%K'), row=current_row, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df[stoch_d], line=dict(color='#FF9800', width=1.5, dash='dot'), name='%D'), row=current_row, col=1)
                fig.add_hline(y=80, line_dash="dash", line_color="rgba(242, 54, 69, 0.5)", row=current_row, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="rgba(8, 153, 129, 0.5)", row=current_row, col=1)

        elif alt_gosterge == "CCI":
            cci_col = get_col("cci")
            if cci_col:
                fig.add_trace(go.Scatter(x=df.index, y=df[cci_col], line=dict(color='#8D6E63', width=1.5), name='CCI'), row=current_row, col=1)
                fig.add_hline(y=100, line_dash="dash", line_color="rgba(242, 54, 69, 0.5)", row=current_row, col=1)
                fig.add_hline(y=-100, line_dash="dash", line_color="rgba(8, 153, 129, 0.5)", row=current_row, col=1)

        elif alt_gosterge == "ATR (Ortalama Gerçek Aralık)":
            atr_col = get_col("atr")
            if atr_col:
                fig.add_trace(go.Scatter(x=df.index, y=df[atr_col], line=dict(color='#FF5252', width=1.5), name='ATR'), row=current_row, col=1)

        elif alt_gosterge == "OBV (On Balance Volume)":
            obv_col = get_col("obv")
            if obv_col:
                fig.add_trace(go.Scatter(x=df.index, y=df[obv_col], line=dict(color='#4CAF50', width=1.5), name='OBV', fill='tozeroy'), row=current_row, col=1)
        
        elif alt_gosterge == "Özel Algoritma":
            if 'Ozel_Algoritma' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['Ozel_Algoritma'], line=dict(color='#E040FB', width=2), name='Sinyalim'), row=current_row, col=1)

        current_row += 1

    # 7. GÖRSEL AYARLAR
    dinamik_yukseklik = 600 + (150 * len(secilen_alt_grafik))
    fig.update_layout(
        template="plotly_dark", xaxis_rangeslider_visible=False, height=dinamik_yukseklik,
        dragmode='pan', hovermode='closest', uirevision='true',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=15, r=15, t=40, b=15)
    )
    lq_grafik_temasi(fig)

    gosterilecek_mum_sayisi = 60 if len(df) > 60 else len(df)
    baslangic_tarihi = df.index[-gosterilecek_mum_sayisi] if len(df) > 0 else "2023-01-01"
    bitis_tarihi = df.index[-1] if len(df) > 0 else "2024-01-01"

    fig.update_xaxes(
        range=[baslangic_tarihi, bitis_tarihi], fixedrange=False, showgrid=True,
        gridwidth=1, gridcolor="rgba(42, 46, 57, 0.4)", griddash="dot",
        rangebreaks=[dict(bounds=["sat", "mon"])]
    )
    fig.update_yaxes(
        fixedrange=False, side="right", showgrid=True,
        gridwidth=1, gridcolor="rgba(42, 46, 57, 0.4)", griddash="dot"
    )

    config = {'scrollZoom': True, 'displayModeBar': True, 'modeBarButtonsToAdd': ['drawline', 'drawcircle', 'eraseshape'], 'displaylogo': False, 'responsive': True}
    st.plotly_chart(fig, use_container_width=True, config=config, theme=None)

def render_analysis(stock, period_val, interval_val, prefix="def"):
    # 1. VERİLERİ ÇEK
    df_ana = data_engine.get_historical_data(stock, period_val, interval_val)
    if df_ana.empty: return

    # 2. FRAKTAL HAVUZU 
    search_period = "10y" if interval_val == "1d" else "2y"
    df_search = data_engine.get_historical_data(stock, search_period, interval_val)
    if df_search.empty or len(df_search) < len(df_ana): df_search = df_ana

    v_close = df_ana['Close']
    v_search = df_search['Close']
    lp = v_close.iloc[-1]
    
    # Teknik Göstergeler
    rsi_ana = ml_engine.calculate_rsi(v_close).iloc[-1]
    pn_ana, sl_ana, ppts_ana = ml_engine.detect_pattern_advanced(v_close.values[-30:]) if len(v_close) >= 30 else ("Yatay", 0, None)
    sup_ana, res_ana = calculate_support_resistance_levels(df_ana)
    e20, e50 = ml_engine.calculate_ema(v_close, 20), ml_engine.calculate_ema(v_close, 50)
    macd, sig, hist = ml_engine.calculate_macd(v_close)
    vol, sharpe, mdd = calculate_risk_metrics(df_ana)
    
    check_security_thresholds(stock, lp, sup_ana)
    
    st.subheader(f"🧬 {stock} Fraktal Geometri Terminali")
    
    # Metrikler
    clist = st.columns(6)
    if stock in st.session_state.portfolio:
        ctx = st.session_state.portfolio[stock]; kz = (lp - ctx['maliyet']) * ctx['lot']; pkz = (kz/(ctx['maliyet']*ctx['lot']))*100
        clist[0].metric("Fiyat", f"{lp:.2f} ₺"); clist[1].metric("K/Z", f"{kz:,.0f} ₺", delta=f"{kz:,.0f}"); clist[2].metric("Verim %", f"%{pkz:.2f}")
    else:
        clist[0].metric("Fiyat", f"{lp:.2f} ₺"); clist[1].metric("RSI", f"{rsi_ana:.1f}"); clist[2].metric("Trend", pn_ana)
    clist[3].metric("EMA20", f"{e20.iloc[-1]:.2f}"); clist[4].metric("EMA50", f"{e50.iloc[-1]:.2f}"); clist[5].metric("MACD", f"{macd.iloc[-1]:.2f}")

    # --- ANA GRAFİK ---
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.025, row_heights=[0.45, 0.1, 0.15, 0.15, 0.15])
    fig.add_trace(go.Scatter(x=v_close.index, y=v_close, name="Fiyat", fill='tozeroy', fillcolor='rgba(8,153,129,0.10)', line=dict(color=LQ_GREEN, width=2.5)), row=1, col=1)
    if isinstance(ppts_ana, (np.ndarray, list)) and len(ppts_ana) == 30:
         fig.add_trace(go.Scatter(x=v_close.index[-30:], y=ppts_ana, name="Formasyon", line=dict(color=LQ_RED, dash='dot', width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=v_close.index, y=e20, name="EMA20", line=dict(color='orange', width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=v_close.index, y=e50, name="EMA50", line=dict(color='cyan', width=1.5)), row=3, col=1)
    h_cols = [LQ_GREEN if h > 0 else LQ_RED for h in hist]
    fig.add_trace(go.Scatter(x=v_close.index, y=macd, name="MACD", line=dict(color='#2962FF')), row=4, col=1)
    fig.add_trace(go.Scatter(x=v_close.index, y=sig, name="Signal", line=dict(color='#FF6D00')), row=4, col=1)
    fig.add_trace(go.Bar(x=v_close.index, y=hist, name="Hist", marker_color=h_cols), row=4, col=1)
    fig.add_trace(go.Bar(x=v_close.index, y=df_ana['Volume'], name="Hacim", marker_color='rgba(0,191,255,0.2)'), row=5, col=1)
    fig.update_layout(template="plotly_dark", height=950, hovermode='x unified', xaxis5=dict(tickformat='%d %b %y', nticks=40))
    lq_grafik_temasi(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"main_{stock}_{prefix}")

    # --- FRAKTAL ANALİZ BÖLÜMÜ ---
    st.markdown("### Fraktal Eşleşme Analizi (DNA Benzerliği)")
    
    # Sadece 3 sütun oluşturuyoruz
    cc = st.columns(3)
    current_len = len(v_close)
    
    # 1. SOL SÜTUN: GÜNCEL GRAFİK
    with cc[0]:
        st.caption("🔴 GÜNCEL (Aktif Trend)")
        f_c = go.Figure()
        f_c.add_trace(go.Scatter(x=list(range(current_len)), y=v_close.values, fill='tozeroy', fillcolor='rgba(8,153,129,0.10)', line=dict(color=LQ_GREEN, width=2)))
        f_c.update_layout(template="plotly_dark", height=200, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False, showlegend=False)
        lq_grafik_temasi(f_c)
        st.plotly_chart(f_c, use_container_width=True, key=f"current_fractal_{prefix}")
        st.caption(f"{v_close.index[0].strftime('%d.%m.%y')} - {v_close.index[-1].strftime('%d.%m.%y')}")

    # FRAKTAL MOTORUNU ÇALIŞTIR
    matches = ml_engine.find_multiple_matches(v_close.values, v_search.values, window_size=current_len, top_n=2)
    
    f_len = 30 # Gelecek Projeksiyonu
    roi_expectations = []
    
    if matches:
        for i, (score, s_idx, match_len) in enumerate(matches):
            # Gelecek verisi kontrolü
            if s_idx + match_len + f_len >= len(v_search): continue

            # Sütun seçimi (cc[1] ve cc[2])
            with cc[i+1]:
                p_seg = v_search.values[s_idx : s_idx + match_len]
                f_seg = v_search.values[s_idx + match_len : s_idx + match_len + f_len]
                
                roi = ((f_seg[-1] - p_seg[-1]) / p_seg[-1]) * 100
                roi_expectations.append(roi)
                
                start_date = v_search.index[s_idx].strftime('%d.%m.%y')
                end_date = v_search.index[s_idx + match_len + f_len - 1].strftime('%d.%m.%y')
                
                st.caption(f"{'🧬' if i==0 else '🔗'} FRAKTAL {i+1} (Benzerlik: %{min(score * 10, 99.9):.1f} | %{roi:.2f})")
                
                f_s = go.Figure()
                f_s.add_trace(go.Scatter(x=list(range(match_len)), y=p_seg, name="Geçmiş", line=dict(color='#FFD700', width=2)))
                
                future_x = list(range(match_len - 1, match_len + f_len))
                future_y = np.concatenate(([p_seg[-1]], f_seg))
                f_s.add_trace(go.Scatter(x=future_x, y=future_y, name="Projeksiyon", line=dict(color='#E040FB', width=2, dash='dot')))
                
                f_s.update_layout(template="plotly_dark", height=200, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False, showlegend=False)
                lq_grafik_temasi(f_s)
                st.plotly_chart(f_s, use_container_width=True, key=f"match_{i}_{prefix}")
                st.caption(f"Dönem: {start_date} - {end_date}")
    
    if not matches:
        with cc[1]: st.warning("Yeterli veri yok.")
        with cc[2]: st.info("Periyodu değiştirmeyi dene.")

    # PROJEKSİYON KARTI
    if roi_expectations:
        avg_roi = sum(roi_expectations) / len(roi_expectations)
        txt_col = LQ_GREEN if avg_roi > 0 else LQ_RED
        bg_col = "rgba(8, 153, 129, 0.08)" if avg_roi > 0 else "rgba(242, 54, 69, 0.08)"

        st.markdown(f"""
        <div style="background-color: {bg_col}; padding: 22px 24px; border-radius: 12px; border: 1px solid {LQ_GRID}; border-left: 3px solid {txt_col}; text-align: center; margin-top: 15px;">
            <h4 style="margin:0; color: {LQ_TEXT_MUTED}; letter-spacing: 0.08em; font-size: 12px; text-transform: uppercase; font-weight: 600;">🔮 Fraktal Projeksiyon</h4>
            <h1 style="margin:10px 0; color: {txt_col}; font-size: 36px; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{'%+' if avg_roi > 0 else '%'}{avg_roi:.2f}</h1>
            <p style="margin:0; font-size: 13px; color: {LQ_TEXT_FAINT};">Geçmişteki benzer geometrik yapıların ortalama 30 günlük getirisidir.</p>
        </div>
        """, unsafe_allow_html=True)

    # EXPANDERLAR
    with st.expander("Temel Analiz ve Risk Karnesi", expanded=True):
        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("Volatilite", f"%{vol*100:.1f}")
        rc2.metric("Sharpe", f"{sharpe:.2f}")
        rc3.metric("Max Drawdown", f"%{mdd*100:.1f}")
        try: inf = yf.Ticker(f"{stock}.IS").info; rc4.metric("F/K", f"{inf.get('trailingPE', 0):.2f}")
        except: rc4.metric("F/K", "N/A")

    with st.expander("Haberler & AI Yorum"):
        news = data_engine.get_stock_news(stock)
        for n in news[:3]: st.write(f"**[{ml_engine.analyze_sentiment(n['title'])[0]}]** {n['title']}")
        comm, stat = ml_engine.generate_investment_comment(lp, rsi_ana, e20.iloc[-1], e50.iloc[-1], macd.iloc[-1], sig.iloc[-1], pn_ana)
        if stat == "positive": st.success(f"🤖 AI: {comm}")
        elif stat == "negative": st.error(f"🤖 AI: {comm}")
        else: st.info(f"AI: {comm}")

# =================================================================
# MODÜL: AI ASİSTAN (SOHBET)
# =================================================================
if mod_nav == "Ana Sayfa":
    bolum_basligi(f"{dinamik_karsilama()}, {ad}", ikon="🪙", alt_baslik="Plutos — günün piyasa özeti")

    endeks, df_ozet, ana_sayfa_hatalari = piyasa_ozeti_getir()

    hc1, hc2, hc3 = st.columns(3)
    if endeks["deger"] is not None:
        hc1.metric("BIST 100 (XU100)", f"{endeks['deger']:,.0f}", f"{endeks['degisim']:+.2f}%")
    else:
        hc1.metric("BIST 100 (XU100)", "—")

    toplam_pozisyon_deger_h = 0.0
    for s, poz in st.session_state.portfolio.items():
        try:
            h, _, _ = hizli_veri_cek(s)
            fp = float(h['Close'].iloc[-1]) if not h.empty else poz['maliyet']
        except Exception:
            fp = poz['maliyet']
        toplam_pozisyon_deger_h += fp * poz['lot']
    hc2.metric("Toplam Varlığınız (Demo)", f"{(st.session_state.virtual_cash + toplam_pozisyon_deger_h):,.0f} ₺")

    aktif_alarm_sayisi = len([a for a in st.session_state.get('price_alarms', []) if not a.get('tetiklendi')])
    hc3.metric("Aktif Fiyat Alarmı", aktif_alarm_sayisi)

    st.markdown("<hr>", unsafe_allow_html=True)

    gc1, gc2 = st.columns(2, gap="large")
    if not df_ozet.empty:
        _trend_config = {
            "Trend": st.column_config.LineChartColumn("Son 15 Gün", width="small", y_min=None, y_max=None),
        }
        with gc1:
            st.markdown("#### 📈 En Çok Yükselenler")
            yukselen = df_ozet.sort_values("Değişim %", ascending=False).head(5).reset_index(drop=True)
            st.dataframe(
                plutos_tablo_stilli(
                    yukselen, yuzde_kolonlari=["Değişim %"], notr_para_kolonlari=["Fiyat"], bar_kolonu="Değişim %"
                ),
                use_container_width=True, hide_index=True, column_config=_trend_config,
            )
        with gc2:
            st.markdown("#### 📉 En Çok Düşenler")
            dusen = df_ozet.sort_values("Değişim %", ascending=True).head(5).reset_index(drop=True)
            st.dataframe(
                plutos_tablo_stilli(
                    dusen, yuzde_kolonlari=["Değişim %"], notr_para_kolonlari=["Fiyat"], bar_kolonu="Değişim %"
                ),
                use_container_width=True, hide_index=True, column_config=_trend_config,
            )
    else:
        st.info("Piyasa özeti verisi şu anda alınamadı, birazdan tekrar deneyin.")

    if ana_sayfa_hatalari:
        with st.expander("Hata Detayı (destek için)"):
            for h in ana_sayfa_hatalari:
                st.caption(h)

    if st.session_state.get('notifications'):
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### 🔔 Son Bildirimler")
        for n in st.session_state.notifications[:5]:
            st.markdown(f"`{n['time']}` — {n['msg']}")

elif mod_nav == "AI Asistan 🤖":
    from ai_asistan import sohbet_yaniti_uret, asistan_hazir_mi

    st.markdown(f"""
    <div style="background: linear-gradient(155deg, #16203F, #0D1220); border: 1px solid {LQ_GRID};
                border-radius: 16px; padding: 26px 28px; margin-bottom: 18px; position: relative; overflow: hidden;">
        <div style="position:absolute; top:-40%; right:-15%; width:220px; height:220px; border-radius:50%;
                    background: radial-gradient(circle, rgba(201,162,39,0.16), transparent 70%);"></div>
        <div style="color:{LQ_GOLD}; text-transform:uppercase; letter-spacing:0.12em; font-size:11px; font-weight:700;">Lumina Quant AI</div>
        <div style="font-family:'Fraunces', serif; font-size:26px; font-weight:600; color:{LQ_TEXT}; margin-top:6px;">
            Hisse ve halka arzları benimle konuşarak analiz et
        </div>
        <div style="color:{LQ_TEXT_MUTED}; font-size:14px; margin-top:6px; max-width:640px;">
            Gerçek fiyat, teknik indikatör, haber ve portföy verine bakarak yanıt veririm. Yatırım tavsiyesi vermem —
            veriyi yorumlarım, kararı sen verirsin.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not asistan_hazir_mi():
        st.info(
            "AI Asistan'ı kullanmak için proje kökündeki `.env` dosyanıza "
            "`ANTHROPIC_API_KEY=sk-ant-...` satırını ekleyip uygulamayı yeniden başlatın "
            "(bkz. `.env.example`). Anahtarınızı [Anthropic Console](https://console.anthropic.com)'dan alabilirsiniz.",
            icon="🔐",
        )

    if "ai_sohbet_gecmisi" not in st.session_state:
        st.session_state["ai_sohbet_gecmisi"] = []

    gecmis = st.session_state["ai_sohbet_gecmisi"]

    # Hızlı başlangıç önerileri (sohbet henüz boşsa)
    if not gecmis:
        st.markdown(f"<div style='color:{LQ_TEXT_FAINT}; font-size:12px; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px;'>Denemek için</div>", unsafe_allow_html=True)
        oneri_kolonlari = st.columns(3)
        onerilen_sorular = [
            "THYAO'yu teknik olarak analiz eder misin?",
            "Bu hafta gündemde olan halka arzlar neler?",
            "Portföyümü genel olarak değerlendirir misin?",
        ]
        for kol, soru in zip(oneri_kolonlari, onerilen_sorular):
            with kol:
                if st.button(soru, use_container_width=True, key=f"ai_oneri_{soru}"):
                    gecmis.append({"role": "user", "content": soru})
                    st.rerun()

    # Geçmiş mesajları göster (en son kullanıcı mesajı da dahil)
    for msg in gecmis:
        avatar = "🤖" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Yeni kullanıcı mesajı için giriş kutusu
    kullanici_mesaji = st.chat_input("Bir hisse, halka arz veya portföyünüz hakkında sorun...")
    if kullanici_mesaji:
        gecmis.append({"role": "user", "content": kullanici_mesaji})
        st.rerun()

    # Son mesaj kullanıcıdansa (henüz yanıtlanmadıysa) asistanı çalıştır
    if gecmis and gecmis[-1]["role"] == "user":
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Veriler taranıyor ve analiz ediliyor..."):
                yanit = sohbet_yaniti_uret(gecmis, data_engine, ml_engine, st.session_state)
            st.markdown(yanit)
        gecmis.append({"role": "assistant", "content": yanit})

    if gecmis:
        if st.button("Sohbeti Temizle", key="ai_sohbet_temizle"):
            st.session_state["ai_sohbet_gecmisi"] = []
            st.rerun()

# =================================================================
# MODÜL: İZLEME LİSTESİ
# =================================================================
elif mod_nav == "İzleme Listesi":
    bolum_basligi("Piyasa Takip Ekranı", ikon="📡")

    # --- TIKLAMA FONKSİYONLARI ---
    def secim_yap(sembol):
        st.session_state.secili_hisse = sembol

    def secim_sil():
        if 'secili_hisse' in st.session_state:
            del st.session_state.secili_hisse

    # --- EKRAN KONTROLÜ ---
    if 'secili_hisse' in st.session_state and st.session_state.secili_hisse:
        # DETAY SAYFASI
        secilen = st.session_state.secili_hisse
        c1, c2 = st.columns([0.8, 0.2])
        c1.subheader(f"{secilen} Detaylı Analizi")
        c2.button("LİSTEYE DÖN", on_click=secim_sil, type="primary", use_container_width=True)
        st.divider()
        render_analysis(secilen, p_per, p_int, "watch_detail")

    else:
        # LİSTE SAYFASI
        db = load_master_db()
        if 'watchlist' not in st.session_state:
            user_info = db.get(st.session_state.user_email, {})
            st.session_state.watchlist = user_info.get('watchlist', ["THYAO", "AKBNK", "EREGL", "TUPRS"])

        with st.expander("➕ Listeyi Düzenle"):
            mevcut = set(BIST_TUM_LIST)
            guvenli = [h for h in st.session_state.watchlist if h in mevcut]
            yeni = st.multiselect("Hisseler:", options=BIST_TUM_LIST, default=guvenli)
            if st.button("KAYDET"):
                st.session_state.watchlist = yeni
                db[st.session_state.user_email]['watchlist'] = yeni
                save_master_db(db); st.rerun()

        st.divider()

        # GRID BUTONLAR
        watchlist = st.session_state.watchlist
        clean_watch = [x for x in watchlist if x in BIST_TUM_LIST]
        cols_per_row = 6
        
        for i in range(0, len(clean_watch), cols_per_row):
            row_stocks = clean_watch[i : i + cols_per_row]
            cols = st.columns(cols_per_row)
            
            for idx, stock in enumerate(row_stocks):
                with cols[idx]:
                    try:
                        t = yf.Ticker(f"{stock}.IS")
                        h = t.history(period="5d")
                        h = son_gecerli_satirlar(h)  # borsa kapalıyken/taslak satırı at
                        label = f"{stock}"
                        if not h.empty and len(h) >= 2:
                            cp = h['Close'].iloc[-1]
                            ch = ((cp - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
                            icon = "🟢" if ch > 0 else "🔴" if ch < 0 else "⚪"
                            label = f"{icon} {stock}\n{cp:.2f}\n%{ch:.2f}"
                        elif not h.empty:
                            cp = h['Close'].iloc[-1]
                            label = f"{stock}\n{cp:.2f}"
                        
                        st.button(label, key=f"btn_{stock}_{i}", on_click=secim_yap, args=(stock,), use_container_width=True)
                    except:
                        st.caption("...")
# =================================================================
# MODÜL: PORTFÖY İZLEME  
# =================================================================
elif mod_nav == "Portföy İzleme":
    bolum_basligi("Portföy Performans & Temettü Analizi", ikon="💼")
    
    if st.button("Verileri Yenile", type="secondary"):
        st.cache_data.clear()
        st.rerun()

    if not st.session_state.get('portfolio'):
        st.warning("Portföyünüz boş. Lütfen yan menüden hisse ekleyin.")
    else:
        rows = []
        genel_maliyet = 0.0
        genel_deger = 0.0
        
        with st.spinner("Veriler hafızadan çekiliyor..."):
            for s, info in st.session_state.portfolio.items():
                try:
                    hist, div_yield_val, yillik_temettu_tl = hizli_veri_cek(s)
                    if hist.empty: continue
                    
                    cp = float(hist['Close'].iloc[-1]) 
                    div_yield_pct = div_yield_val * 100 
                    
                    lt = int(info['lot'])
                    maliyet = float(info['maliyet'])
                    
                    toplam_deger = cp * lt
                    beklenen_yillik_gelir = yillik_temettu_tl * lt
                    toplam_maliyet = maliyet * lt
                    
                    kz_tutar = toplam_deger - toplam_maliyet
                    kz_yuzde = (kz_tutar / toplam_maliyet) * 100 if toplam_maliyet > 0 else 0.0

                    genel_maliyet += toplam_maliyet
                    genel_deger += toplam_deger

                    rows.append({
                        "Hisse": s,
                        "Fiyat": f"{cp:.2f} ₺",
                        "Lot": lt,
                        "Maliyet": f"{maliyet:.2f} ₺",
                        "K/Z (%)": f"{kz_yuzde:.2f}%",         
                        "K/Z (₺)": f"{kz_tutar:,.2f} ₺",       
                        "Temettü Verimi": f"%{div_yield_pct:.2f}", 
                        "Hisse Başı (₺)": f"{yillik_temettu_tl:.2f} ₺",
                        "Yıllık Temettü Geliri": f"{beklenen_yillik_gelir:,.2f} ₺",
                        "Portföy Değeri": f"{toplam_deger:,.2f} ₺"
                    })
                except Exception as e:
                    continue

        if rows:
            genel_kz_tutar = genel_deger - genel_maliyet
            genel_kz_yuzde = (genel_kz_tutar / genel_maliyet) * 100 if genel_maliyet > 0 else 0.0
            
            # 3'lü şık sütun tasarımı
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Portföy Değeri", f"{genel_deger:,.2f} ₺")
            c2.metric("Toplam Kâr / Zarar", f"{genel_kz_tutar:,.2f} ₺", delta=f"{genel_kz_tutar:,.2f} ₺")
            c3.metric("Genel K/Z Yüzdesi", f"%{genel_kz_yuzde:.2f}", delta=f"%{genel_kz_yuzde:.2f}")
            
            st.divider()

            # 3. ADIM: TABLO İÇİ RENKLENDİRME 
            df_final = pd.DataFrame(rows)
            
            secili_index = None
            if "portfoy_tablo_secim" in st.session_state:
                secili_satirlar = st.session_state["portfoy_tablo_secim"].get("selection", {}).get("rows", [])
                if secili_satirlar:
                    secili_index = secili_satirlar[0]

            def satir_boya(row):
                satir_no = row.name 
                stiller = ['' for _ in row] 
                
                if satir_no == secili_index:
                    return [f'background-color: rgba(201, 162, 39, 0.14); border-top: 1px solid {LQ_GOLD}; border-bottom: 1px solid {LQ_GOLD};' for _ in row]
                
                kz_yuzde_idx = df_final.columns.get_loc('K/Z (%)')
                kz_tutar_idx = df_final.columns.get_loc('K/Z (₺)')
                
                for idx in [kz_yuzde_idx, kz_tutar_idx]:
                    val_str = str(row.iloc[idx])
                    if val_str.startswith('-'):
                        stiller[idx] = f'color: {LQ_RED}; font-weight: 600;'
                    elif val_str.startswith('0.00'):
                        stiller[idx] = f'color: {LQ_TEXT_MUTED};'
                    else:
                        stiller[idx] = f'color: {LQ_GREEN}; font-weight: 600;'
                        
                return stiller

            styled_df = df_final.style.apply(satir_boya, axis=1)

            tablo_secimi = st.dataframe(
                styled_df, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="portfoy_tablo_secim"  
            )
            
            toplam_gelir = sum([float(str(r['Yıllık Temettü Geliri']).replace(' ₺', '').replace(',', '')) for r in rows])
            st.success(f"💰 Bu portföyün sana yıllık tahmini temettü nakit akışı: **{toplam_gelir:,.2f} ₺**")

            if secili_index is not None:
                secilen_hisse = df_final.iloc[secili_index]['Hisse']
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.divider()
                st.markdown(f"<h3 style='text-align: center; color: {LQ_GOLD_STRONG};'>🔍 {secilen_hisse} Hızlı Analiz</h3>", unsafe_allow_html=True)
                
                render_analysis(secilen_hisse, p_per, p_int, prefix="port_secim")

# =================================================================
# MODÜL: STRATEJİK ANALİZ (SERBEST ARAMA)
# =================================================================
elif mod_nav == "Stratejik Analiz":
    bolum_basligi("Stratejik Teknik Analiz", ikon="🧭")
    
    search_s = st.selectbox("Analiz Edilecek Hisse Sembolü:", BIST_TUM_LIST, index=BIST_TUM_LIST.index("THYAO"))
    st.divider()
    
    tab1, tab2 = st.tabs(["Fraktal Analiz", "İnteraktif Teknik Grafik"])
    
    with tab1:
        render_analysis(search_s, p_per, p_int, "stratejik")
        
    with tab2:
        hisse_inceleme_ekrani(f"{search_s}.IS")
elif mod_nav == "Piyasa Tarayıcı":
    bolum_basligi("Piyasa Radarı", ikon="📊")
    yatirim_uyarisi_goster()
    
    tum_hisseler = [
        "AEFES", "AGHOL", "AHGAZ", "AKBNK", "AKCNS", "AKFGY", "AKFYE", "AKSA", "AKSEN", "ALARK", "ALBRK", "ALFAS", "ARCLK", "ASELS", "ASTOR", "BERA", "BIMAS", "BRSAN", "BRYAT", "BUCIM", "CANTE", "CCOLA", "CIMSA", "CWENE", "DOAS", "DOHOL", "ECILC", "EGEEN", "EKGYO", "ENERY", "ENJSA", "ENKAI", "EREGL", "EUPWR", "EUREN", "FROTO", "GARAN", "GESAN", "GUBRF", "GWIND", "HALKB", "HEKTS", "IMASM", "IPEKE", "ISCTR", "ISDMR", "ISGYO", "ISMEN", "IZENR", "KALES", "KRDMD", "KAYSE", "KCAER", "KCHOL", "KMPUR", "KONTR", "KONYA", "KOZAA", "KOZAL", "KZBGY", "MAVI", "MGROS", "MIATK", "ODAS", "OTKAR", "OYAKC", "PENTA", "PETKM", "PGSUS", "QUAGR", "REEDR", "SAHOL", "SASA", "SDTTR", "SISE", "SKBNK", "SMRTG", "SOKM", "TABGD", "TAVHL", "TCELL", "THYAO", "TKFEN", "TOASO", "TSKB", "TTKOM", "TTRAK", "TUKAS", "TUPRS", "ULKER", "VAKBN", "VESBE", "VESTL", "YEOTK", "YKBNK", "YYLGD", "ZOREN"
    ]
    
    def radar_renk(val):
        val_str = str(val)
        if '🟢' in val_str or '📈' in val_str:
            return f'color: {LQ_GREEN}; font-weight: 600;'
        elif '🔴' in val_str or '📉' in val_str:
            return f'color: {LQ_RED}; font-weight: 600;'
        elif '🟡' in val_str:
            return f'color: {LQ_GOLD_STRONG};'
        return ''

    tab_oto, tab_portfoy = st.tabs(["Otonom Tarama (Top 5)", "Portföy Röntgeni"])

    # --- 1. SEKME: OTOMATİK BIST 100 TARAYICI ---
    with tab_oto:
        st.info("BIST 100 endeksini asenkron motorla tarayarak teknik potansiyeli en yüksek 5 varlığı filtreler.")
        
        # Tarama Butonu
        if st.button("BIST 100'ü Tara ve Top 5'i Bul", type="primary", use_container_width=True, key="btn_oto_tara"):
            with st.spinner("Tüm BIST 100 asenkron olarak taranıyor..."):
                df_radar = asenkron_bist_tara(tum_hisseler)
                if not df_radar.empty:
                    df_islenmis = sirala_radar_sonuclari(df_radar).head(5)
                    st.session_state['son_top5'] = df_islenmis.drop(columns=["_puan"])
                    st.session_state['top5_lider'] = df_islenmis.iloc[0]['Hisse'] if not df_islenmis.empty else "-"
                    st.session_state['top5_guc_al'] = len(df_islenmis[df_islenmis['Yapay Zeka Sinyali'] == 'Güçlü Al'])
        
        # Hafızada tarama sonucu varsa KPI'ları ve Tabloyu göster
        if 'son_top5' in st.session_state:
            df_top5 = st.session_state['son_top5']
            
            # --- KPI METRİKLERİ ---
            k1, k2, k3 = st.columns(3)
            k1.metric("Günün Lider Varlığı", st.session_state.get('top5_lider', '-'), help="Hacim, momentum ve trend kırılımı bazında en yüksek teknik skora sahip varlık.")
            k2.metric("Güçlü Al Sinyalleri (Top 5'te)", str(st.session_state.get('top5_guc_al', 0)), help="Temel indikatörlerin eşzamanlı pozitif kesişim (Golden Cross vb.) verdiği varlık sayısı.", delta_color="normal")
            k3.metric("Filtrelenen Hacim", "5 Varlık", help="Tüm pazar taranarak en iyi 5 fırsat süzülmüştür.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- RENKLİ TABLO GÖSTERİMİ ---
            try:
                styled_top5 = df_top5.style.map(radar_renk, subset=["Trend (SMA50)", "MACD", "Yapay Zeka Sinyali"])
            except AttributeError:
                styled_top5 = df_top5.style.applymap(radar_renk, subset=["Trend (SMA50)", "MACD", "Yapay Zeka Sinyali"])
            
            st.dataframe(styled_top5, use_container_width=True, hide_index=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Backtest Kayıt Butonu
            if st.button("Çıkan 5 Varlığı Backtest'e Gönder", use_container_width=True, key="bt_btn_oto_toplu"):
                backteste_toplu_ekle(df_top5)
                st.success("✅ 5 varlığın tamamı strateji laboratuvarına (Backtest) eklendi!")
                del st.session_state['son_top5'] 

    # --- 2. SEKME: PORTFÖY VE MANUEL SEÇİM ---
    with tab_portfoy:
        
        with st.expander("⚙️ Manuel Check-up Havuzu", expanded=True):
            varsayilan_hisseler = list(st.session_state.get('portfolio', {}).keys())
            if not varsayilan_hisseler:
                varsayilan_hisseler = ["THYAO", "TUPRS", "FROTO", "EREGL", "ENJSA"]
                
            for s in varsayilan_hisseler:
                if s not in tum_hisseler:
                    tum_hisseler.append(s)
            tum_hisseler.sort()
            
            secilen_liste = st.multiselect(
                "İncelenecek Varlıkları Seçin:", 
                tum_hisseler, 
                default=varsayilan_hisseler, 
                key="ozel_tarama_multi",
                help="Sadece seçtiğiniz hisselerin güncel teknik röntgeni çekilir."
            )
            
            ozel_tara_btn = st.button("📡 Seçili Varlıkları Analiz Et", use_container_width=True, key="btn_ozel_tara")
        
        if ozel_tara_btn:
            if not secilen_liste:
                st.warning("Lütfen taranacak en az bir varlık seçin.")
            else:
                with st.spinner("Teknik göstergeler hesaplanıyor..."):
                    df_ozel = asenkron_bist_tara(secilen_liste)
                    if not df_ozel.empty:
                        df_ozel_sirali = sirala_radar_sonuclari(df_ozel)
                        st.session_state['son_ozel'] = df_ozel_sirali.drop(columns=["_puan"])
                        st.session_state['ozel_lider'] = df_ozel_sirali.iloc[0]['Hisse'] if not df_ozel_sirali.empty else "-"
        
        if 'son_ozel' in st.session_state:
            df_ozel_tablo = st.session_state['son_ozel']
            
            # --- ÖZEL TARAMA KPI METRİĞİ ---
            st.metric("Seçilenler Arasında En Güçlüsü", st.session_state.get('ozel_lider', '-'), help="Seçtiğiniz havuz içinde algoritmadan en yüksek puanı alan hisse.")
            st.markdown("<br>", unsafe_allow_html=True)
            
            try:
                styled_ozel = df_ozel_tablo.style.map(radar_renk, subset=["Trend (SMA50)", "MACD", "Yapay Zeka Sinyali"])
            except AttributeError:
                styled_ozel = df_ozel_tablo.style.applymap(radar_renk, subset=["Trend (SMA50)", "MACD", "Yapay Zeka Sinyali"])
                
            st.dataframe(styled_ozel, use_container_width=True, hide_index=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"📥 Çıkan {len(df_ozel_tablo)} Varlığı Backtest'e Gönder", use_container_width=True, key="bt_btn_ozel_toplu"):
                backteste_toplu_ekle(df_ozel_tablo)
                st.success(f"✅ {len(df_ozel_tablo)} varlık başarıyla laboratuvara eklendi!")
                del st.session_state['son_ozel']

elif mod_nav == "AI Gelecek":
    bolum_basligi("Makro-Entegre AI Fiyat Projeksiyonu", ikon="🔮", alt_baslik="GBM Motoru")
    yatirim_uyarisi_goster()
    
    if not st.session_state.get('portfolio'):
        st.warning("Portföyünüz boş. Lütfen hisse ekleyin.")
    else:
        s = st.selectbox("Analiz Edilecek Hisse:", list(st.session_state.portfolio.keys()))
        
        if st.button("SİMÜLASYONU BAŞLAT", type="primary"):
            with st.status(f"{s} için global veriler ve piyasa duyarlılığı işleniyor...", expanded=True) as status:
                
                # 1. HİSSE GEÇMİŞ VERİSİ
                st.write("Veri setleri indiriliyor...")
                h_df = data_engine.get_historical_data(s, "1y", "1d")
                h_df = son_gecerli_satirlar(h_df)  # ekstra güvenlik: taslak/NaN satırı at
                if h_df.empty:
                    st.error("Hisse verisi çekilemedi!")
                    st.stop()
                    
                close = h_df['Close']
                last_price = float(close.iloc[-1])
                
                # -------------------------------------------------------------
                # 2. MAKROEKONOMİK ETKİ
                # -------------------------------------------------------------
                st.write("Makroekonomik korelasyon hesaplanıyor...")
                macro_sym = "XU100.IS" 
                macro_isim = "BIST 100 Endeksi"
                
                if s in ["TUPRS", "THYAO", "PGSUS", "AKSEN"]:
                    macro_sym = "BZ=F"
                    macro_isim = "Brent Petrol"
                elif s in ["FROTO", "TOASO", "EREGL", "KRDMD", "ENJSA", "MGROS"]:
                    macro_sym = "TRY=X" 
                    macro_isim = "Dolar/TL Kuru"
                    
                try:
                    m_ticker = yf.Ticker(macro_sym)
                    m_df = m_ticker.history(period="1y")
                    m_df = son_gecerli_satirlar(m_df)['Close']  # ASIL BUG buradaydı: bu seri hiç filtrelenmiyordu
                    if len(m_df) < 16:
                        raise ValueError("Makro seri için yeterli geçerli veri yok.")
                    macro_trend = float((m_df.iloc[-1] - m_df.iloc[-15]) / m_df.iloc[-15])
                    
                    c_temp = close.copy()
                    m_temp = m_df.copy()
                    if c_temp.index.tz is not None: c_temp.index = c_temp.index.tz_localize(None)
                    if m_temp.index.tz is not None: m_temp.index = m_temp.index.tz_localize(None)
                    c_temp.index = c_temp.index.normalize()
                    m_temp.index = m_temp.index.normalize()
                    
                    aligned = pd.concat([c_temp, m_temp], axis=1, join='inner').dropna()
                    korelasyon = float(aligned.iloc[:,0].corr(aligned.iloc[:,1])) if len(aligned) > 30 else 0.5
                except Exception:
                    macro_trend = 0.0
                    korelasyon = 0.5

                makro_aciklama = ""
                if s in ["THYAO", "PGSUS"] and macro_sym == "BZ=F":
                    makro_etki = macro_trend * -abs(korelasyon) * 0.15 
                    makro_aciklama = f"Makro Çevre: {macro_isim} tarafındaki hareketlilik, jet yakıtı maliyetlerini etkilediği için projeksiyona TERS orantılı yansıtıldı."
                else:
                    makro_etki = macro_trend * korelasyon * 0.1
                    makro_aciklama = f"Makro Çevre: {macro_isim} tarafındaki momentuma, %{korelasyon*100:.1f} pozitif korelasyon ile uyum sağlandı."

                # -------------------------------------------------------------
                # 3. HABER, DUYARLILIK VE TEMETTÜ PRİMİ 
                # -------------------------------------------------------------
                st.write("Medya duyarlılığı ve Temettü potansiyeli taranıyor...")
                sentiment_skor = 0
                haber_kaynagi = "Algoritmik Momentum"
                
                try:
                    t_div = yf.Ticker(f"{s}.IS")
                    hist_1y = t_div.history(period="1y")
                    hist_1y = son_gecerli_satirlar(hist_1y)
                    yillik_temettu = 0.0
                    
                    if not hist_1y.empty and 'Dividends' in hist_1y.columns:
                        yillik_temettu = float(hist_1y['Dividends'].sum())
                        
                    div_yield = (yillik_temettu / last_price) if last_price > 0 else 0.0
                    div_yield = min(div_yield, 0.15) 
                    
                    temettu_primi_aylik = div_yield * 0.05 
                    temettu_aciklama = f"%{div_yield*100:.2f} temettü verimi, hisseye ekstra 'toparlanma' ivmesi sağlıyor." if div_yield > 0.001 else "Kuvvetli bir temettü verimi tespit edilemedi."
                except Exception as e:
                    temettu_primi_aylik = 0.0
                    temettu_aciklama = f"Temettü hesaplanırken hata oluştu: {str(e)}"

                # Google News RSS
                try:
                    import urllib.request
                    import xml.etree.ElementTree as ET
                    url = f"https://news.google.com/rss/search?q={s}+hisse+borsa&hl=tr&gl=TR&ceid=TR:tr"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        xml_data = response.read()
                        
                    root = ET.fromstring(xml_data)
                    items = root.findall('.//item')
                    
                    pozitif_kelimeler = ['arttı', 'artıyor', 'artış', 'yükseldi', 'rekor', 'kâr', 'büyüme', 'temettü', 'onay', 'pozitif', 'uçuş', 'hedef', 'tavsiye']
                    negatif_kelimeler = ['düştü', 'zarar', 'risk', 'kriz', 'düşüş','düştü','düşük','düşüyor', 'satış', 'negatif', 'ceza', 'düşüş', 'iptal', 'kayıp']
                    
                    if len(items) > 0:
                        haber_kaynagi = "Google Haberler (TR)"
                        incelenen_haber = 0
                        for item in items[:7]:
                            baslik = item.find('title').text.lower()
                            if any(k in baslik for k in pozitif_kelimeler): sentiment_skor += 1; incelenen_haber += 1
                            elif any(k in baslik for k in negatif_kelimeler): sentiment_skor -= 1; incelenen_haber += 1
                                
                        if incelenen_haber == 0: 
                            import pandas_ta as ta
                            rsi_val = float(ta.rsi(close, length=14).iloc[-1])
                            sentiment_skor = 1 if rsi_val > 55 else (-1 if rsi_val < 45 else 0)
                            
                except Exception:
                    import pandas_ta as ta
                    rsi_val = float(ta.rsi(close, length=14).iloc[-1])
                    sentiment_skor = 2 if rsi_val > 65 else (1 if rsi_val > 55 else (-2 if rsi_val < 35 else (-1 if rsi_val < 45 else 0)))

                haber_etkisi_aylik = (sentiment_skor / 7.0) * 0.03 # Maksimum %3 AYLIK etki

                # -------------------------------------------------------------
                #  4. PROFESYONEL GBM (GEOMETRİK BROWN HAREKETİ) MANTARI
                # -------------------------------------------------------------
                st.write("Simülasyon (GBM) çalıştırılıyor...")
                gunluk_getiriler = np.log(close / close.shift(1)).dropna()
                mu = float(gunluk_getiriler.mean())
                sigma = float(gunluk_getiriler.std())
                
                gelecek_gun_sayisi = 21
                
                makro_etki_gunluk = makro_etki / gelecek_gun_sayisi
                haber_etkisi_gunluk = haber_etkisi_aylik / gelecek_gun_sayisi
                temettu_primi_gunluk = temettu_primi_aylik / gelecek_gun_sayisi
                
                # Toplam GÜNLÜK Sürüklenme (Drift)
                total_drift = mu + makro_etki_gunluk + haber_etkisi_gunluk + temettu_primi_gunluk
                
                import hashlib
                from datetime import datetime
                bugun_tarih = datetime.now().strftime("%Y-%m-%d")
                seed_metni = f"{s}_{bugun_tarih}" 
                sabit_tohum = int(hashlib.md5(seed_metni.encode()).hexdigest(), 16) % (2**32 - 1)
                np.random.seed(sabit_tohum) 
                
                Z = np.random.normal(0, 1, gelecek_gun_sayisi)
                gunluk_adimlar = np.exp((total_drift - 0.5 * sigma**2) + sigma * Z)
                
                projeksiyon = last_price * np.cumprod(gunluk_adimlar)
                hedef_fiyat = projeksiyon[-1]
                
                status.update(label="Tüm Analizler Tamamlandı!", state="complete")

            # --- EKRANA ÇİZİM VE RAPORLAMA ---
            st.divider()
            
            bg_color = "rgba(8, 153, 129, 0.08)" if hedef_fiyat > last_price else "rgba(242, 54, 69, 0.08)"
            txt_color = LQ_GREEN if hedef_fiyat > last_price else LQ_RED
            yon_ikon = "↗️" if hedef_fiyat > last_price else "↘️"
            
            c1, c2 = st.columns([0.7, 0.3])
            with c1:
                st.markdown(f"### 🤖 AI Karar Mekanizması & Raporu")
                st.write(f"- {makro_aciklama}")
                st.write(f"- **Piyasa Duyarlılığı:** {haber_kaynagi} NLP Skoru: **{sentiment_skor}** (Trend Etkisi: %{haber_etkisi_aylik*100:.2f})")
                st.write(f"- **Temettü Karakteristiği:** {temettu_aciklama}")
                st.write(f"- **Volatilite (Risk):** Günlük bazda %{sigma*100:.2f} standart sapma (oynaklık) ile fiyatlanıyor.")
            
            with c2:
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 20px; border-radius: 12px; border: 1px solid {LQ_GRID}; border-left: 3px solid {txt_color}; text-align: center;">
                    <p style="margin:0; color: {LQ_TEXT_FAINT}; font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em;">1 Aylık Hedef Fiyat (GBM)</p>
                    <h2 style="margin:10px 0; color: {txt_color}; font-family: 'JetBrains Mono', monospace;">{hedef_fiyat:.2f} ₺ {yon_ikon}</h2>
                    <p style="margin:0; color: {txt_color}; font-weight: 700; font-family: 'JetBrains Mono', monospace;">% {((hedef_fiyat-last_price)/last_price)*100:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

            f = go.Figure()
            f.add_trace(go.Scatter(x=close.index[-60:], y=close.values[-60:], name="Geçmiş Fiyat", line=dict(color='#2962FF', width=2.5)))
            
            gelecek_x = pd.date_range(start=close.index[-1], periods=gelecek_gun_sayisi+1, freq='B')
            gelecek_y = np.insert(projeksiyon, 0, last_price)
            f.add_trace(go.Scatter(x=gelecek_x, y=gelecek_y, name="AI Projeksiyon", line=dict(color=txt_color, width=2.5, dash='dash')))
            
            f.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified')
            lq_grafik_temasi(f)
            st.plotly_chart(f, use_container_width=True)
elif mod_nav == "Finansal Özgürlük (FIRE)":
    bolum_basligi("FIRE & Temettü Kartopu Simülatörü", ikon="🔥")
    st.write("Finansal bağımsızlık hedefinize giden yolda, yatırımlarınızın ve temettülerinizin bileşik getiriyle (re-invest) nasıl bir kartopuna dönüşeceğini hesaplayın.")
    
    st.divider()
    
    # --- 1. KULLANICI GİRİŞLERİ ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("Zaman Çizelgesi")
        mevcut_yas = st.number_input("Şu Anki Yaşınız:", min_value=18, max_value=80, value=22, step=1)
        hedef_yas = st.number_input("Hedef FIRE Yaşınız:", min_value=mevcut_yas+1, max_value=90, value=30, step=1)
        sure_yil = hedef_yas - mevcut_yas
        
    with c2:
        st.markdown("Sermaye")
        varsayilan_sermaye = 100000 
        baslangic_sermaye = st.number_input("Mevcut Portföy Büyüklüğü (₺):", min_value=0, value=varsayilan_sermaye, step=10000)
        aylik_ekleme = st.number_input("Aylık Düzenli Tasarruf (₺):", min_value=0, value=6000, step=500)
        
    with c3:
        st.markdown("Getiri Beklentileri")
        yillik_getiri = st.slider("Yıllık Hisse Büyümesi (%)", min_value=0, max_value=150, value=45, help="Hissenin kendi fiyatındaki yıllık ortalama artış beklentisi.")
        temettu_verimi = st.slider("Ortalama Temettü Verimi (%)", min_value=0, max_value=20, value=6, help="Portföyün yıllık dağıttığı ortalama net temettü oranı.")

    # --- 2. BİLEŞİK GETİRİ VE KARTOPU MATEMATİĞİ ---
    if st.button("Kartopunu Yuvarla", type="primary", use_container_width=True):
        with st.spinner("Bileşik getiri motoru 8. harikayı hesaplıyor..."):
            
            yillar = []
            toplam_portfoy = []
            sadece_ana_para = []
            kümülatif_temettu = []
            kümülatif_deger_artisi = []
            
            anlik_deger = baslangic_sermaye
            yatirilan_toplam_nakit = baslangic_sermaye
            toplam_alinan_temettu = 0
            
            for yil in range(1, sure_yil + 1):
                yillar.append(mevcut_yas + yil)
                
                # Yıllık düzenli alımlar
                yillik_ekleme = aylik_ekleme * 12
                yatirilan_toplam_nakit += yillik_ekleme
                anlik_deger += yillik_ekleme
                
                # Sermaye Büyümesi 
                buyume_miktari = anlik_deger * (yillik_getiri / 100)
                anlik_deger += buyume_miktari
                
                # Temettü Dağıtımı ve Geri Alım 
                yillik_temettu_miktari = anlik_deger * (temettu_verimi / 100)
                toplam_alinan_temettu += yillik_temettu_miktari
                anlik_deger += yillik_temettu_miktari 
                
                # Listelere kayıt
                sadece_ana_para.append(yatirilan_toplam_nakit)
                kümülatif_temettu.append(toplam_alinan_temettu)
                toplam_portfoy.append(anlik_deger)
                kümülatif_deger_artisi.append(anlik_deger - yatirilan_toplam_nakit - toplam_alinan_temettu)
                
            son_portfoy_degeri = toplam_portfoy[-1]
            hedef_yastaki_aylik_temettu = (son_portfoy_degeri * (temettu_verimi / 100)) / 12

            st.divider()
            
            st.markdown(f"<h3 style='text-align: center; color: {LQ_GOLD_STRONG};'>🎉 {hedef_yas} Yaşındaki Finansal Tablonuz</h3>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(label="Toplam Portföy Değeri", value=f"{son_portfoy_degeri:,.0f} ₺")
            k2.metric(label="Cebinden Çıkan Net Nakit", value=f"{yatirilan_toplam_nakit:,.0f} ₺")
            k3.metric(label="Sadece Temettüden Gelen", value=f"{toplam_alinan_temettu:,.0f} ₺")
            k4.metric(label="Aylık Pasif Temettü Maaşı", value=f"{hedef_yastaki_aylik_temettu:,.0f} ₺/Ay", delta="Finansal Özgürlük!", delta_color="normal")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("Portföyün Kartopu Etkisi")
            
            import plotly.graph_objects as go
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=yillar, y=sadece_ana_para, mode='lines', 
                name='Yatırılan Ana Para', line=dict(width=0), 
                fillcolor='rgba(91, 141, 239, 0.45)', fill='tozeroy', stackgroup='one'
            ))
            
            fig.add_trace(go.Scatter(
                x=yillar, y=kümülatif_deger_artisi, mode='lines', 
                name='Hisse Fiyat Artışı', line=dict(width=0), 
                fillcolor='rgba(0, 230, 118, 0.5)', fill='tonexty', stackgroup='one'
            ))
            
            fig.add_trace(go.Scatter(
                x=yillar, y=kümülatif_temettu, mode='lines', 
                name='Yeniden Yatırılan Temettüler', line=dict(width=0), 
                fillcolor='rgba(255, 214, 0, 0.6)', fill='tonexty', stackgroup='one'
            ))
            
            fig.update_layout(
                template="plotly_dark", height=500,
                xaxis_title="Yaş", yaxis_title="Portföy Büyüklüğü (₺)",
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            lq_grafik_temasi(fig)
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("**Kartopunun Gücü:** Grafikteki sarı alan (Temettüler) ve yeşil alan (Büyüme) başlangıçta ince bir çizgi gibiyken, hedefe yaklaştıkça cebinizden çıkan mavi alandan (Ana Para) tamamen kopup üstel olarak büyür.")
# =========================================================================
# MODÜL: WHATSAPP BOTU & OTONOM ZAMANLAYICI
# =========================================================================
elif mod_nav == "WhatsApp Botu":
    bolum_basligi("WhatsApp Otomasyon Merkezi", ikon="💬")
    st.write("Raporlarınızı manuel olarak fırlatın veya programın arka planda her gün sizin belirlediğiniz saatte otomatik mesaj atmasını sağlayın.")
    
    import json
    import os
    import schedule
    import time
    import threading
    from datetime import datetime
    import yfinance as yf
    import numpy as np
    import pandas as pd
    
    # --- AYARLARI OKUMA ---
    # GÜVENLİK NOTU: Twilio SID/Token gibi sırlar artık whatsapp_ayarlar.json'a
    # açık metin yazılmıyor; .env dosyasından (auth_utils.get_secret) okunuyor.
    # Sadece hassas OLMAYAN bilgiler (gönderim saati, telefon numaraları) JSON'da kalıyor.
    from auth_utils import get_secret, twilio_configured
    AYAR_DOSYASI = "whatsapp_ayarlar.json"

    def ayarlari_getir():
        veri = {"tw_from": "", "tw_to": "", "saat": "09:30"}
        if os.path.exists(AYAR_DOSYASI):
            try:
                with open(AYAR_DOSYASI, "r") as f:
                    veri.update(json.load(f))
            except: pass
        # Sırlar .env'den geliyor; JSON'daki eski tw_sid/tw_token varsa yok say.
        veri["tw_sid"] = get_secret("TWILIO_SID", "")
        veri["tw_token"] = get_secret("TWILIO_TOKEN", "")
        return veri

    kayitli_ayarlar = ayarlari_getir()
    if not twilio_configured():
        st.info(
            "Twilio SID/Token .env dosyasında tanımlı değil. Proje kökünde bir `.env` "
            "dosyası oluşturup TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM değerlerini girin "
            "(bkz. `.env.example`). Bu bilgiler artık JSON dosyasına yazılmıyor.",
            icon="🔐",
        )
    
    # --- 1. AYARLAR VE ZAMANLAMA ---
    st.markdown("#### ⚙️ Otomasyon ve API Ayarları")
    c1, c2 = st.columns(2)
    with c1:
        # SID/Token artık salt-okunur gösterilir; değeri .env'den gelir, buradan değiştirilmez.
        tw_sid = st.text_input("Account SID (.env → TWILIO_SID):", value=kayitli_ayarlar.get("tw_sid", ""), disabled=True)
        tw_from = st.text_input("Twilio Numarası (Örn: +14155238886):", value=kayitli_ayarlar.get("tw_from", ""))
        gonderim_saati = st.time_input("Günlük Rapor Saati:", value=datetime.strptime(kayitli_ayarlar.get("saat", "09:30"), "%H:%M").time())
        
    with c2:
        tw_token = st.text_input("Auth Token (.env → TWILIO_TOKEN):", value="●●●●●●●●" if kayitli_ayarlar.get("tw_token") else "", disabled=True)
        tw_to = st.text_input("Kendi Numaranız (Örn: +90532...):", value=kayitli_ayarlar.get("tw_to", ""))
        
    # --- ARKA PLAN GÖREVİ (THREADING) ---
    def otomatik_mesaj_gorevi(sid, token, num_from, num_to):
        try:
            from twilio.rest import Client
            client = Client(sid, token)
            
            msg = "*Günlük Raporunuz Hazır!*\nPiyasalar taranıyor..."
            client.messages.create(from_=f"whatsapp:{num_from}", body=msg, to=f"whatsapp:{num_to}")
            print("Otomatik mesaj fırlatıldı!")
        except Exception as e:
            print(f"Otomatik mesaj hatası: {e}")

    # MİMARİ NOT: Streamlit her kullanıcı etkileşiminde script'i baştan çalıştırır.
    # threading.Thread + schedule burada "çalışıyor gibi görünür" ama süreç yeniden
    # başladığında (deploy, uyku modu, restart) zamanlayıcı sessizce kaybolur ve
    # çoklu kullanıcıda her oturum kendi thread'ini açmaya çalışır. Ticari/çok
    # kullanıcılı sürümde bu mantığı Streamlit sürecinden tamamen çıkarıp ayrı bir
    # servise (APScheduler + systemd, veya Celery beat + Redis, ya da basit bir
    # cron job) taşımak gerekir.
    def zamanlayici_baslat():
        while True:
            schedule.run_pending()
            time.sleep(30)

    if st.button("Bilgileri Kaydet ve Otomatiğe Bağla", use_container_width=True):
        saat_str = gonderim_saati.strftime("%H:%M")
        
        # JSON Dosyasına Yazma — GÜVENLİK: sır (SID/Token) buraya yazılmaz, sadece
        # hassas olmayan ayarlar (numaralar, saat) diske kaydedilir.
        yeni_ayarlar = {
            "tw_from": tw_from, "tw_to": tw_to, "saat": saat_str
        }
        with open(AYAR_DOSYASI, "w") as f:
            json.dump(yeni_ayarlar, f)
            
        # Otonom Sistemi Kurma
        schedule.clear()
        schedule.every().day.at(saat_str).do(otomatik_mesaj_gorevi, tw_sid, tw_token, tw_from, tw_to)
        
        if 'thread_aktif' not in st.session_state:
            threading.Thread(target=zamanlayici_baslat, daemon=True).start()
            st.session_state['thread_aktif'] = True
            
        st.success(f"✅ Ayarlar kalıcı olarak kaydedildi! Bilgisayar açık olduğu sürece {saat_str}'da rapor atılacak.")

    st.divider()

    # --- 2. MANUEL GÖNDERİM BUTONLARI ---
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("Piyasa Radarı")
        if st.button("Top 5 Bültenini Şimdi Gönder", type="primary", use_container_width=True):
            if not tw_sid or not tw_token:
                st.error("API bilgileri eksik!")
            else:
                try:
                    from twilio.rest import Client
                    client = Client(tw_sid, tw_token)
                    with st.status("BIST 100 taranıyor...", expanded=True) as status:
                        tum_hisseler = ["AEFES", "AGHOL", "AHGAZ", "AKBNK", "AKCNS", "AKFGY", "AKFYE", "AKSA", "AKSEN", "ALARK", "ALBRK", "ALFAS", "ARCLK", "ASELS", "ASTOR", "BERA", "BIMAS", "BRSAN", "BRYAT", "BUCIM", "CANTE", "CCOLA", "CIMSA", "CWENE", "DOAS", "DOHOL", "ECILC", "EGEEN", "EKGYO", "ENERY", "ENJSA", "ENKAI", "EREGL", "EUPWR", "EUREN", "FROTO", "GARAN", "GESAN", "GUBRF", "GWIND", "HALKB", "HEKTS", "IMASM", "IPEKE", "ISCTR", "ISDMR", "ISGYO", "ISMEN", "IZENR", "KALES", "KRDMD", "KAYSE", "KCAER", "KCHOL", "KMPUR", "KONTR", "KONYA", "KOZAA", "KOZAL", "KZBGY", "MAVI", "MGROS", "MIATK", "ODAS", "OTKAR", "OYAKC", "PENTA", "PETKM", "PGSUS", "QUAGR", "REEDR", "SAHOL", "SASA", "SDTTR", "SISE", "SKBNK", "SMRTG", "SOKM", "TABGD", "TAVHL", "TCELL", "THYAO", "TKFEN", "TOASO", "TSKB", "TTKOM", "TTRAK", "TUKAS", "TUPRS", "ULKER", "VAKBN", "VESBE", "VESTL", "YEOTK", "YKBNK", "YYLGD", "ZOREN"]
                        df_radar = asenkron_bist_tara(tum_hisseler)
                        if not df_radar.empty:
                            df_top5 = df_radar.sort_values(by="_puan", ascending=False).head(5)
                            msg = "*Terminal Günlük Bülten*\n\n🎯 *Haftanın Top 5 Fırsatı:*\n\n"
                            for _, row in df_top5.iterrows():
                                msg += f"🔹 *{row['Hisse']}* - Fiyat: {row['Fiyat']}\n   Sinyal: {row['Yapay Zeka Sinyali']}\n   Trend: {row['Trend (SMA50)']}\n\n"
                            client.messages.create(from_=f"whatsapp:{tw_from}", body=msg, to=f"whatsapp:{tw_to}")
                            status.update(label="Top 5 gönderildi!", state="complete")
                            st.success("✅ Bülten WhatsApp'ta!")
                except Exception as e: st.error(f"Hata: {e}")

    with col_b:
        st.markdown("Kriz Korumalı Altın Oran")
        if st.button("Hedged Raporu Şimdi Gönder", type="primary", use_container_width=True):
            if not tw_sid or not tw_token:
                st.error("API bilgileri eksik!")
            else:
                try:
                    from twilio.rest import Client
                    client = Client(tw_sid, tw_token)
                    with st.status("Savaş ve Kriz algoritmaları devrede...", expanded=True) as status:
                        
                        hisseler = list(st.session_state.get('portfolio', {}).keys())
                        if len(hisseler) < 3: hisseler = ["FROTO", "TUPRS", "ENJSA", "MGROS", "THYAO"]
                        
                        if "GLDTR" not in hisseler:
                            hisseler.append("GLDTR")
                            
                        # Verileri çek 
                        semboller = [f"{s}.IS" for s in hisseler]
                        raw = yf.download(semboller, period="5y")['Close'].ffill().bfill().dropna()
                        
                        # Günlük getiriler ve CAGR (Bileşik Getiri)
                        rets = raw.pct_change().dropna()
                        toplam_gun = len(raw)
                        cagr = (raw.iloc[-1] / raw.iloc[0]) ** (252 / toplam_gun) - 1
                        roll_max = raw.cummax()
                        drawdown = raw / roll_max - 1.0
                        max_dd = drawdown.min() 
                        
                        cov_matrix = rets.cov() * 252
                        

                        n_ports = 50000 
                        results = np.zeros((4, n_ports))
                        weights_list = []
                        
                        gecerli_portfoy_sayisi = 0
                        
                        for i in range(n_ports):
                            w = np.random.random(len(hisseler))
                            w /= np.sum(w)
                            
                            if np.any(w > 0.30):
                                continue

                            gldtr_index = hisseler.index("GLDTR")
                            if w[gldtr_index] < 0.10:
                                continue
                                
                            weights_list.append(w)
                            
                            p_cagr = np.sum(w * cagr)
                            p_risk = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
                            p_max_dd = np.sum(w * max_dd) 
                            p_score = p_cagr / abs(p_max_dd) 
                            
                            results[0, gecerli_portfoy_sayisi] = p_cagr
                            results[1, gecerli_portfoy_sayisi] = p_risk
                            results[2, gecerli_portfoy_sayisi] = p_max_dd
                            results[3, gecerli_portfoy_sayisi] = p_score
                            
                            gecerli_portfoy_sayisi += 1
                            
                        valid_results = results[:, :gecerli_portfoy_sayisi]
                        best_idx = np.argmax(valid_results[3])
                        
                        o_w = weights_list[best_idx]
                        o_g = valid_results[0, best_idx]
                        o_r = valid_results[1, best_idx] 
                        o_dd = valid_results[2, best_idx] 
                        
                        # WhatsApp Mesajı Derleme
                        msg = "*Hedged Portföy & Kriz Savunma Raporu*\n\n"
                        msg += "Savaş ve piyasa çöküşlerine karşı Calmar Oranı algoritmasıyla dengelenmiş ideal dağılım:\n\n"
                        
                        for i, h in enumerate(hisseler):
                            # Altını (Hedge) vurgulayarak göster
                            if h == "GLDTR":
                                msg += f"*ALTIN FONU (Hedge):* % {o_w[i]*100:.1f}\n"
                            else:
                                msg += f"🔸 *{h}:* % {o_w[i]*100:.1f}\n"
                                
                        msg += f"\n Beklenen Yıllık Büyüme (CAGR): *% {o_g*100:.1f}*\n"
                        msg += f"Yıllık Oynaklık (Risk): *% {o_r*100:.1f}*\n"
                        msg += f"Tarihi Maksimum Kriz Erimesi: *% {o_dd*100:.1f}*\n\n"
                        msg += "Analiz: Tek hisse riski sınırlandı ve güvenli liman eklendi._"
                        
                        client.messages.create(from_=f"whatsapp:{tw_from}", body=msg, to=f"whatsapp:{tw_to}")
                        status.update(label="Hedged Oran fırlatıldı!", state="complete")
                        st.success("✅ Kriz Korumalı Rapor WhatsApp'ta!")
                        
                except Exception as e: st.error(f"Hata: {e}")

elif mod_nav == "Fiyat Alarmları":
    bolum_basligi("Fiyat Alarmları", ikon="🔔", alt_baslik="Belirlediğiniz eşiğe gelince bildirim üretir")

    def _alarm_durumu_kaydet():
        d = load_master_db()
        if st.session_state.user_email not in d:
            d[st.session_state.user_email] = kullanici_verisi
        d[st.session_state.user_email]['price_alarms'] = st.session_state.price_alarms
        save_master_db(d)

    ac1, ac2 = st.columns([1, 1.3], gap="large")

    with ac1:
        st.markdown("#### Yeni Alarm Ekle")
        alarm_hisse = st.selectbox("Hisse", BIST_TUM_LIST, key="alarm_hisse_sec")

        guncel_fp = None
        try:
            h, _, _ = hizli_veri_cek(alarm_hisse)
            if not h.empty:
                guncel_fp = float(h['Close'].iloc[-1])
        except Exception:
            guncel_fp = None
        if guncel_fp:
            st.caption(f"Güncel fiyat: {guncel_fp:.2f} ₺")

        alarm_yon = st.radio("Koşul", ["Üzerine Çıkınca", "Altına İnince"], horizontal=True, key="alarm_yon_sec")
        alarm_esik = st.number_input(
            "Eşik Fiyat (₺)", min_value=0.01,
            value=float(guncel_fp) if guncel_fp else 1.0, step=0.01, key="alarm_esik_gir"
        )

        if st.button("🔔 Alarm Kur", type="primary", use_container_width=True, key="alarm_ekle_btn"):
            st.session_state.price_alarms.append({
                "hisse": alarm_hisse, "yon": alarm_yon, "esik": float(alarm_esik), "tetiklendi": False,
            })
            _alarm_durumu_kaydet()
            st.success(f"{alarm_hisse} için alarm kuruldu: {alarm_yon.lower()} {alarm_esik:.2f} ₺")
            st.rerun()

    with ac2:
        st.markdown("#### Kurulu Alarmlarım")
        if not st.session_state.price_alarms:
            st.info("Henüz alarm kurulmadı.")
        else:
            for i, alarm in enumerate(st.session_state.price_alarms):
                durum_metin = "🔴 Tetiklendi" if alarm.get('tetiklendi') else "🟢 Aktif"
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(
                        f"**{alarm['hisse']}** — {alarm['yon']} **{alarm['esik']:.2f} ₺** &nbsp; `{durum_metin}`",
                        unsafe_allow_html=True,
                    )
                with col_b:
                    if st.button("🗑️", key=f"alarm_sil_{i}", help="Alarmı sil"):
                        st.session_state.price_alarms.pop(i)
                        _alarm_durumu_kaydet()
                        st.rerun()

elif mod_nav == "Portföy Optimizasyonu":
    bolum_basligi("Modern Portföy Optimizasyonu", ikon="⚖️", alt_baslik="Markowitz")
    yatirim_uyarisi_goster()
    st.write("Nobel ödüllü Markowitz algoritmasını profesyonel kısıtlamalarla (Min %3 - Max %35 kuralı) kullanarak sağlıklı, defansif ve mantıklı altın ağırlık dağılımını bulun.")
    
    st.divider()
    
    # --- 1. HİSSE SEÇİMİ ---
    mevcut_hisseler = list(st.session_state.get('portfolio', {}).keys())
    if not mevcut_hisseler:
        mevcut_hisseler = ["FROTO", "TUPRS", "ENJSA", "MGROS", "THYAO", "AKBNK"]
        
    tum_hisseler_opt = list(set(mevcut_hisseler + ["EREGL", "SISE", "KCHOL", "SAHOL", "YKBNK", "ISCTR", "BIMAS", "TOASO", "ASELS"]))
    tum_hisseler_opt.sort()
    
    secilen_opt_hisseler = st.multiselect(
        "Optimizasyon Havuzundaki Hisseler (En az 3 hisse seçin):", 
        tum_hisseler_opt, 
        default=mevcut_hisseler,
        key="opt_hisse_secim"
    )
    
    # --- 2. AKILLI MARKOWITZ MOTORU ---
    if st.button("Altın Oranı Bul (Optimizasyonu Başlat)", type="primary", use_container_width=True):
        if len(secilen_opt_hisseler) < 3:
            st.warning("Sağlam bir çeşitlendirme (çeşitlilik) analizi için lütfen en az 3 hisse seçin.")
        else:
            with st.status("Akıllı Markowitz Motoru çalıştırılıyor...", expanded=True) as status:
                st.write("Son 5 yıllık piyasa verileri indiriliyor ve krizler analiz ediliyor...")
                
                semboller = [f"{s}.IS" for s in secilen_opt_hisseler]
                try:
                    raw_data = yf.download(semboller, period="5y")
                    if 'Close' in raw_data.columns:
                        veri = raw_data['Close']
                    else:
                        veri = raw_data.iloc[:, :len(semboller)] 
                        
                    if isinstance(veri, pd.Series):
                        veri = veri.to_frame()
                        
                    gecerli_semboller = [s for s in semboller if s in veri.columns]
                    veri = veri[gecerli_semboller]
                    secilen_opt_hisseler = [s.replace(".IS", "") for s in gecerli_semboller] 
                    veri = veri.ffill().bfill().dropna()
                    
                    if len(veri) < 20:
                        st.error("Yeterli tarihsel veri bulunamadı.")
                        st.stop()
                        
                except Exception as e:
                    st.error("Veri çekilirken hata oluştu.")
                    st.stop()
                
                st.write("CAGR (Bileşik Getiri) ve Risk matrisleri hesaplanıyor...")
                # Getiri (CAGR) ve Volatilite hesabı
                toplam_gun = len(veri)
                yillik_getiri = (veri.iloc[-1] / veri.iloc[0]) ** (252 / toplam_gun) - 1
                getiriler = veri.pct_change().dropna()
                kovaryans_matrisi = getiriler.cov() * 252
                
                st.write("Monte Carlo: 20.000 sınırlandırılmış portföy test ediliyor...")
                portfoy_sayisi = 20000 
                hisse_sayisi = len(secilen_opt_hisseler)
                
                gecerli_sonuclar = []
                agirliklar_kaydi = []
                
                
                for i in range(portfoy_sayisi):
                    # Rastgele ağırlık üretimi
                    w = np.random.dirichlet(np.ones(hisse_sayisi), size=1)[0]
                    
                    if np.any(w > 0.35) or np.any(w < 0.03):
                        continue 
                        
                    agirliklar_kaydi.append(w)
                    
                    p_getiri = np.sum(w * yillik_getiri)
                    p_volatilite = np.sqrt(np.dot(w.T, np.dot(kovaryans_matrisi, w)))
                    p_sharpe = p_getiri / p_volatilite if p_volatilite > 0 else 0
                    
                    gecerli_sonuclar.append([p_getiri, p_volatilite, p_sharpe])
                
                if len(agirliklar_kaydi) == 0:
                    esit_w = np.ones(hisse_sayisi) / hisse_sayisi
                    agirliklar_kaydi.append(esit_w)
                    p_getiri = np.sum(esit_w * yillik_getiri)
                    p_vol = np.sqrt(np.dot(esit_w.T, np.dot(kovaryans_matrisi, esit_w)))
                    gecerli_sonuclar.append([p_getiri, p_vol, p_getiri/p_vol])
                    
                sonuclar_np = np.array(gecerli_sonuclar).T
                
                # En yüksek Sharpe Oranını bul
                max_sharpe_idx = np.argmax(sonuclar_np[2])
                opt_agirliklar = agirliklar_kaydi[max_sharpe_idx]
                opt_getiri = sonuclar_np[0, max_sharpe_idx]
                opt_risk = sonuclar_np[1, max_sharpe_idx]
                opt_sharpe = sonuclar_np[2, max_sharpe_idx]
                
                # En düşük Volatiliteyi (Riski) bul
                min_risk_idx = np.argmin(sonuclar_np[1])
                guvenli_agirliklar = agirliklar_kaydi[min_risk_idx]
                
                status.update(label="Algoritma sağlıklı ve dengeli altın oranı başarıyla buldu!", state="complete")
                
            # --- 3. EKRANA ÇİZİM ---
            st.divider()
            c1, c2 = st.columns([0.4, 0.6])
            
            with c1:
                st.markdown("İdeal Dağılım (Maksimum Sharpe)")
                st.write("Hiçbir varlığın %35'i geçmediği, adil ve çeşitlendirilmiş sağlıklı portföy modeli.")
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=secilen_opt_hisseler, 
                    values=opt_agirliklar, 
                    hole=.62,
                    textinfo='label+percent',
                    textfont=dict(family="JetBrains Mono, monospace", size=12),
                    marker=dict(colors=LQ_COLORWAY, line=dict(color=LQ_SURFACE, width=2))
                )])
                fig_pie.update_layout(template="plotly_dark", margin=dict(t=20, b=20, l=20, r=20), showlegend=False, height=300)
                lq_grafik_temasi(fig_pie)
                st.plotly_chart(fig_pie, use_container_width=True)
                
                st.metric("Beklenen Yıllık Büyüme (CAGR)", f"% {opt_getiri*100:.1f}")
                st.metric("Yıllık Dalgalanma Riski", f"% {opt_risk*100:.1f}")
                st.metric("Sharpe Skoru", f"{opt_sharpe:.2f}")

            with c2:
                st.markdown("Etkin Sınır (Bounded Frontier)")
                st.write(f"Kurallara uyan {len(agirliklar_kaydi)} farklı sağlıklı portföy içinden yıldız ile işaretlenen altın oranınız.")
                
                fig_scatter = go.Figure()
                fig_scatter.add_trace(go.Scatter(
                    x=sonuclar_np[1,:], y=sonuclar_np[0,:], 
                    mode='markers', 
                    marker=dict(size=4, color=sonuclar_np[2,:],
                                colorscale=[[0, "#2A3A66"], [0.5, "#4AB8C4"], [1, LQ_GOLD_STRONG]],
                                showscale=True, colorbar=dict(title="Sharpe", tickfont=dict(color=LQ_TEXT_MUTED))),
                    name='Sağlıklı İhtimaller'
                ))
                fig_scatter.add_trace(go.Scatter(
                    x=[opt_risk], y=[opt_getiri], 
                    mode='markers', 
                    marker=dict(symbol='star', size=18, color=LQ_GOLD_STRONG, line=dict(width=1.5, color=LQ_BG)),
                    name='İdeal Portföy'
                ))
                fig_scatter.update_layout(template="plotly_dark", xaxis_title="Risk (Volatilite)", yaxis_title="Beklenen Yıllık Getiri (CAGR)", height=450, margin=dict(t=30, b=0, l=0, r=0))
                lq_grafik_temasi(fig_scatter)
                st.plotly_chart(fig_scatter, use_container_width=True)
                
            st.markdown("Kısıtlandırılmış Ağırlık Tavsiyesi")
            df_tavsiye = pd.DataFrame({
                "Hisse": secilen_opt_hisseler,
                "İdeal Ağırlık": [f"% {w*100:.1f}" for w in opt_agirliklar],
                "Defansif Ağırlık (Min. Risk)": [f"% {w*100:.1f}" for w in guvenli_agirliklar]
            })
            st.dataframe(df_tavsiye, use_container_width=True, hide_index=True)

elif mod_nav == "Temettü":
    bolum_basligi("Temettü Verimi & Takvimi", ikon="💰", alt_baslik="Son 1 yıllık temettü ödemeleri (yfinance)")

    varsayilan_temettu = [h for h in ANA_SAYFA_TARAMA_LISTESI[:10] if h in BIST_TUM_LIST]
    temettu_hisseler = st.multiselect(
        "Karşılaştırılacak Hisseler", options=BIST_TUM_LIST, default=varsayilan_temettu, key="temettu_hisseler"
    )

    if not temettu_hisseler:
        st.info("En az bir hisse seçin.")
    else:
        verim_satirlari = []
        takvim_satirlari = []

        for h in temettu_hisseler:
            try:
                hist, div_yield, yillik_temettu = hizli_veri_cek(h)
                if hist.empty:
                    continue
                fiyat = float(hist["Close"].iloc[-1])
                verim_satirlari.append({
                    "Hisse": h, "Güncel Fiyat": fiyat, "Son 1 Yıl Temettü (₺)": yillik_temettu,
                    "Temettü Verimi %": div_yield * 100,
                })

                if "Dividends" in hist.columns:
                    odemeler = hist[hist["Dividends"] > 0]["Dividends"]
                    for tarih, tutar in odemeler.items():
                        takvim_satirlari.append({
                            "Hisse": h, "Tarih": tarih.strftime("%Y-%m-%d"), "Hisse Başı Temettü (₺)": float(tutar),
                        })
            except Exception as e:
                st.caption(f"{h}: veri alınamadı ({e})")
                continue

        st.markdown("#### Temettü Verimi Karşılaştırması")
        if verim_satirlari:
            df_verim = pd.DataFrame(verim_satirlari).sort_values("Temettü Verimi %", ascending=False)
            st.dataframe(
                plutos_tablo_stilli(
                    df_verim,
                    notr_para_kolonlari=["Güncel Fiyat", "Son 1 Yıl Temettü (₺)"],
                    bar_kolonu="Temettü Verimi %",
                ).format({"Temettü Verimi %": "{:.2f}%"}),
                use_container_width=True, hide_index=True,
            )
            st.caption(
                "Not: 'Son 1 Yıl Temettü' yfinance'in geçmiş fiyat verisindeki Dividends kolonundan "
                "toplanır; gelecek temettü tutarı/tarihi tahmini DEĞİLDİR, geçmiş ödemeleri yansıtır."
            )
        else:
            st.warning("Seçilen hisseler için temettü verisi bulunamadı.")

        st.markdown("#### Temettü Takvimi (Son 1 Yıl — Geçmiş Ödemeler)")
        if takvim_satirlari:
            df_takvim = pd.DataFrame(takvim_satirlari).sort_values("Tarih", ascending=False).reset_index(drop=True)
            st.dataframe(
                plutos_tablo_stilli(df_takvim, notr_para_kolonlari=["Hisse Başı Temettü (₺)"]),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("Seçilen hisselerde son 1 yıl içinde kayıtlı temettü ödemesi bulunamadı.")

elif mod_nav == "Sektör Karşılaştırma":
    bolum_basligi("Sektör Karşılaştırma", ikon="🏭", alt_baslik="Aynı sektördeki hisseleri yan yana koyun")

    sc1, sc2 = st.columns([1, 2])
    with sc1:
        secilen_sektor = st.selectbox("Sektör", list(BIST_SEKTORLER.keys()), key="sektor_sec")
        periyot = st.selectbox("Periyot", ["1mo", "3mo", "6mo", "1y"], index=1, key="sektor_periyot")

    varsayilan_hisseler = BIST_SEKTORLER[secilen_sektor]
    with sc2:
        secilen_hisseler = st.multiselect(
            "Karşılaştırılacak Hisseler", options=BIST_TUM_LIST,
            default=[h for h in varsayilan_hisseler if h in BIST_TUM_LIST],
            key=f"sektor_hisseler__{secilen_sektor}",
        )

    if len(secilen_hisseler) < 2:
        st.info("Karşılaştırma için en az 2 hisse seçin.")
    else:
        satirlar = []
        fig_norm = go.Figure()
        gun_sayisi = {"1mo": 22, "3mo": 66, "6mo": 132, "1y": 252}[periyot]

        for h in secilen_hisseler:
            try:
                hist, _, _ = hizli_veri_cek(h)
                if hist.empty:
                    continue
                hist = hist.tail(gun_sayisi)
                if len(hist) < 2:
                    continue

                close = hist["Close"]
                son = float(close.iloc[-1])
                onceki_gun = float(close.iloc[-2])
                donem_basi = float(close.iloc[0])
                gunluk_degisim = (son / onceki_gun - 1) * 100
                donem_getiri = (son / donem_basi - 1) * 100

                satirlar.append({
                    "Hisse": h, "Fiyat": son, "Günlük %": gunluk_degisim,
                    f"{periyot} Getiri %": donem_getiri,
                })

                normalize_seri = (close / donem_basi) * 100
                fig_norm.add_trace(go.Scatter(
                    x=hist.index, y=normalize_seri, mode="lines", name=h,
                ))
            except Exception as e:
                st.caption(f"{h}: veri alınamadı ({e})")
                continue

        if satirlar:
            st.markdown("#### Performans Karşılaştırma Tablosu")
            df_sektor = pd.DataFrame(satirlar).sort_values(f"{periyot} Getiri %", ascending=False)
            st.dataframe(
                plutos_tablo_stilli(
                    df_sektor,
                    yuzde_kolonlari=["Günlük %", f"{periyot} Getiri %"],
                    notr_para_kolonlari=["Fiyat"],
                    bar_kolonu=f"{periyot} Getiri %",
                ),
                use_container_width=True, hide_index=True,
            )

            st.markdown(f"#### Normalize Fiyat Performansı (dönem başı = 100)")
            fig_norm.update_layout(
                template="plotly_dark", height=450,
                margin=dict(t=20, b=0, l=0, r=0), legend=dict(orientation="h", y=1.08),
            )
            lq_grafik_temasi(fig_norm)
            st.plotly_chart(fig_norm, use_container_width=True)
        else:
            st.warning("Seçilen hisseler için veri alınamadı.")

elif mod_nav == "Performans & Risk":
    bolum_basligi("Performans & Risk Analizi", ikon="📐", alt_baslik="Portföyünüz BIST 100'e karşı — kurumsal platformlardaki tarzda")

    st.caption(
        "Metodoloji notu: Bu analiz, **mevcut portföy kompozisyonunuzun** (bugünkü lotlarınızın) "
        "seçtiğiniz dönem boyunca sabit tutulduğu varsayımıyla geriye dönük hesaplanır — yani "
        "\"bu hisseleri bu dönem boyunca elimde tutsaydım nasıl bir seyir izlerdi\" sorusuna cevap verir. "
        "Alım/satım tarihlerinizin tam geçmişini yansıtan bir gerçek zamanlı getiri değildir."
    )

    if not st.session_state.portfolio:
        st.info("Analiz için önce Portföyünüze en az bir hisse eklemeniz (veya Emir Ver ile almanız) gerekiyor.")
    else:
        pr_c1, pr_c2 = st.columns([1, 1])
        with pr_c1:
            pr_periyot = st.selectbox("Periyot", ["3mo", "6mo", "1y"], index=1, key="perf_periyot")
        with pr_c2:
            risksiz_oran = st.number_input(
                "Risksiz Faiz Varsayımı (yıllık, %)", min_value=0.0, max_value=100.0, value=45.0, step=1.0,
                key="perf_risksiz", help="Sharpe oranı hesaplamasında kullanılır. TR'de risksiz oranın yüksekliği nedeniyle varsayılan 45% — kendi görüşünüze göre değiştirebilirsiniz."
            )

        gun_sayisi = {"3mo": 66, "6mo": 132, "1y": 252}[pr_periyot]

        fiyat_serileri = {}
        for h, poz in st.session_state.portfolio.items():
            try:
                hist, _, _ = hizli_veri_cek(h)
                if hist.empty:
                    continue
                fiyat_serileri[h] = hist["Close"].tail(gun_sayisi)
            except Exception:
                continue

        try:
            xu100_hist, _, _ = hizli_veri_cek("XU100")
            xu100_seri = xu100_hist["Close"].tail(gun_sayisi) if not xu100_hist.empty else None
        except Exception:
            xu100_seri = None

        if not fiyat_serileri:
            st.warning("Portföyünüzdeki hisseler için veri alınamadı.")
        else:
            df_fiyat = pd.DataFrame(fiyat_serileri).dropna()
            df_fiyat.index = df_fiyat.index.tz_localize(None) if df_fiyat.index.tz is not None else df_fiyat.index

            lotlar = pd.Series({h: st.session_state.portfolio[h]["lot"] for h in df_fiyat.columns})
            portfoy_degeri = (df_fiyat * lotlar).sum(axis=1)

            if len(portfoy_degeri) < 5:
                st.warning("Anlamlı bir analiz için yeterli ortak işlem günü verisi yok.")
            else:
                gunluk_getiri = portfoy_degeri.pct_change().dropna()
                toplam_getiri = (portfoy_degeri.iloc[-1] / portfoy_degeri.iloc[0] - 1) * 100
                yillik_volatilite = gunluk_getiri.std() * (252 ** 0.5) * 100
                yillik_getiri_ort = gunluk_getiri.mean() * 252 * 100
                sharpe = ((yillik_getiri_ort - risksiz_oran) / yillik_volatilite) if yillik_volatilite > 0 else 0.0

                kumulatif_max = portfoy_degeri.cummax()
                dusus_serisi = (portfoy_degeri - kumulatif_max) / kumulatif_max * 100
                maks_dusus = dusus_serisi.min()

                en_iyi_gun = gunluk_getiri.max() * 100
                en_kotu_gun = gunluk_getiri.min() * 100

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Dönem Getirisi", f"{toplam_getiri:+.2f}%")
                m2.metric("Yıllık Volatilite", f"{yillik_volatilite:.2f}%")
                m3.metric("Sharpe Oranı", f"{sharpe:.2f}")
                m4.metric("Maksimum Düşüş", f"{maks_dusus:.2f}%")

                st.caption(f"En iyi gün: {en_iyi_gun:+.2f}% · En kötü gün: {en_kotu_gun:+.2f}%")

                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown(f"#### Portföyünüz vs BIST 100 (dönem başı = 100)")

                fig_perf = go.Figure()
                portfoy_norm = (portfoy_degeri / portfoy_degeri.iloc[0]) * 100
                fig_perf.add_trace(go.Scatter(x=portfoy_norm.index, y=portfoy_norm, mode="lines", name="Portföyünüz"))

                if xu100_seri is not None and not xu100_seri.empty:
                    xu100_idx = xu100_seri.index.tz_localize(None) if xu100_seri.index.tz is not None else xu100_seri.index
                    xu100_seri = pd.Series(xu100_seri.values, index=xu100_idx)
                    ortak_tarih = portfoy_norm.index.intersection(xu100_seri.index)
                    if len(ortak_tarih) > 2:
                        xu100_hizali = xu100_seri.loc[ortak_tarih]
                        xu100_norm = (xu100_hizali / xu100_hizali.iloc[0]) * 100
                        fig_perf.add_trace(go.Scatter(x=xu100_norm.index, y=xu100_norm, mode="lines", name="BIST 100"))
                        fark = portfoy_norm.iloc[-1] - xu100_norm.iloc[-1]
                        renk_metin = "yeşil" if fark >= 0 else "kırmızı"
                        st.caption(
                            f"Portföyünüz, aynı dönemde BIST 100'ü **{fark:+.2f} puan** "
                            f"{'geride bıraktı' if fark >= 0 else 'gerisinde kaldı'} ({renk_metin} işaret grafikte)."
                        )
                    else:
                        st.caption("BIST 100 ile ortak işlem günü bulunamadı, sadece portföy eğrisi gösteriliyor.")
                else:
                    st.caption("BIST 100 verisi alınamadı, sadece portföy eğrisi gösteriliyor.")

                fig_perf.update_layout(
                    template="plotly_dark", height=420, margin=dict(t=20, b=0, l=0, r=0),
                    legend=dict(orientation="h", y=1.08),
                )
                lq_grafik_temasi(fig_perf)
                st.plotly_chart(fig_perf, use_container_width=True)

                with st.expander("Günlük Düşüş (Drawdown) Grafiği"):
                    fig_dd = go.Figure(data=[go.Scatter(
                        x=dusus_serisi.index, y=dusus_serisi, mode="lines", fill="tozeroy", name="Düşüş %",
                        line=dict(color="#F0455C"),
                    )])
                    fig_dd.update_layout(template="plotly_dark", height=280, margin=dict(t=10, b=0, l=0, r=0))
                    lq_grafik_temasi(fig_dd)
                    st.plotly_chart(fig_dd, use_container_width=True)

elif mod_nav == "Emir Ver (Demo)":
    bolum_basligi("Emir Ver", ikon="🧾", alt_baslik="Kâğıt (paper) işlem — gerçek para/gerçek emir DEĞİLDİR")

    st.warning(
        "⚠️ Bu ekran **simülasyondur**. Şu an Midas veya başka bir aracı kurumun gerçek "
        "hesabına bağlı değildir — bilindiği kadarıyla Midas, bireysel geliştiricilere açık "
        "resmi bir emir-gönderme API'si sunmuyor. Burada verdiğiniz emirler sadece bu "
        "uygulama içindeki sanal bakiyenizi ve portföyünüzü etkiler; gerçek borsaya iletilmez."
    )

    def _demo_durumu_kaydet():
        d = load_master_db()
        if st.session_state.user_email not in d:
            d[st.session_state.user_email] = kullanici_verisi
        d[st.session_state.user_email]['portfolio'] = st.session_state.portfolio
        d[st.session_state.user_email]['virtual_cash'] = st.session_state.virtual_cash
        d[st.session_state.user_email]['trade_log'] = st.session_state.trade_log
        save_master_db(d)

    m1, m2, m3 = st.columns(3)
    toplam_pozisyon_deger = 0.0
    toplam_maliyet = 0.0
    varlik_satirlari = []
    for s, poz in st.session_state.portfolio.items():
        try:
            h, _, _ = hizli_veri_cek(s)
            fp = float(h['Close'].iloc[-1]) if not h.empty else poz['maliyet']
        except Exception:
            fp = poz['maliyet']
        deger = fp * poz['lot']
        maliyet_tutari = poz['maliyet'] * poz['lot']
        kar_zarar = deger - maliyet_tutari
        kar_zarar_pct = (kar_zarar / maliyet_tutari * 100) if maliyet_tutari else 0.0
        toplam_pozisyon_deger += deger
        toplam_maliyet += maliyet_tutari
        varlik_satirlari.append({
            "Hisse": s, "Lot": poz['lot'], "Ort. Maliyet": poz['maliyet'], "Güncel Fiyat": fp,
            "Piyasa Değeri": deger, "Kâr/Zarar": kar_zarar, "Kâr/Zarar %": kar_zarar_pct,
            "Hedef": poz.get('hedef', '-'),
        })

    m1.metric("Sanal Nakit", f"{st.session_state.virtual_cash:,.2f} ₺")
    m2.metric("Pozisyon Değeri", f"{toplam_pozisyon_deger:,.2f} ₺")
    m3.metric("Toplam Varlık", f"{(st.session_state.virtual_cash + toplam_pozisyon_deger):,.2f} ₺")

    st.markdown("#### Varlıklarım")
    if varlik_satirlari:
        df_varlik = pd.DataFrame(varlik_satirlari).sort_values("Piyasa Değeri", ascending=False)
        toplam_kz = toplam_pozisyon_deger - toplam_maliyet
        toplam_kz_pct = (toplam_kz / toplam_maliyet * 100) if toplam_maliyet else 0.0
        renk = "var(--green)" if toplam_kz >= 0 else "var(--red)"
        st.markdown(
            f'<p style="color:{renk}; font-family:\'JetBrains Mono\',monospace; font-weight:600; margin-top:-6px;">'
            f'Toplam Kâr/Zarar: {toplam_kz:,.2f} ₺ ({toplam_kz_pct:+.2f}%)</p>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            plutos_tablo_stilli(
                df_varlik,
                yuzde_kolonlari=["Kâr/Zarar %"],
                para_kolonlari=["Kâr/Zarar"],
                notr_para_kolonlari=["Ort. Maliyet", "Güncel Fiyat", "Piyasa Değeri"],
                bar_kolonu="Kâr/Zarar %",
            ),
            use_container_width=True, hide_index=True,
        )

        with st.expander("Dağılım Grafiği"):
            fig_pie = go.Figure(data=[go.Pie(
                labels=df_varlik["Hisse"], values=df_varlik["Piyasa Değeri"], hole=0.55,
            )])
            fig_pie.update_layout(height=360, margin=dict(t=20, b=0, l=0, r=0), showlegend=True)
            lq_grafik_temasi(fig_pie)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Portföyünüzde henüz hisse yok. Aşağıdan ilk demo alım emrinizi verebilirsiniz.")

    st.markdown("<hr>", unsafe_allow_html=True)

    ec1, ec2 = st.columns([1, 1], gap="large")

    with ec1:
        st.markdown("#### Yeni Emir")
        emir_hisse = st.selectbox("Hisse", BIST_TUM_LIST, key="demo_emir_hisse")

        guncel_fiyat = None
        try:
            h, _, _ = hizli_veri_cek(emir_hisse)
            if not h.empty:
                guncel_fiyat = float(h['Close'].iloc[-1])
        except Exception:
            guncel_fiyat = None

        if guncel_fiyat:
            st.metric(f"{emir_hisse} Güncel Fiyat", f"{guncel_fiyat:.2f} ₺")
        else:
            st.error("Güncel fiyat alınamadı, lütfen tekrar deneyin.")

        emir_yon = st.radio("Yön", ["AL", "SAT"], horizontal=True, key="demo_emir_yon")
        emir_tip = st.radio("Emir Tipi", ["Piyasa (Market)", "Limit"], horizontal=True, key="demo_emir_tip")
        emir_lot = st.number_input("Lot", min_value=1, value=10, step=1, key="demo_emir_lot")

        if emir_tip == "Limit":
            limit_fiyat = st.number_input(
                "Limit Fiyat (₺)", min_value=0.01,
                value=float(guncel_fiyat) if guncel_fiyat else 1.0, step=0.01, key="demo_limit_fiyat"
            )
        else:
            limit_fiyat = guncel_fiyat

        elde_lot = st.session_state.portfolio.get(emir_hisse, {}).get("lot", 0)
        if emir_yon == "SAT":
            st.caption(f"Portföyünüzde {elde_lot} lot {emir_hisse} bulunuyor.")

        buton_tip = "primary"
        if st.button(f"{emir_yon} — {emir_hisse}", type=buton_tip, use_container_width=True, key="demo_emir_gonder"):
            if not limit_fiyat or limit_fiyat <= 0:
                st.error("Geçerli bir fiyat bulunamadı, emir gönderilemedi.")
            else:
                tutar = limit_fiyat * emir_lot
                if emir_yon == "AL":
                    if tutar > st.session_state.virtual_cash:
                        st.error(f"Yetersiz sanal bakiye. Gereken: {tutar:,.2f} ₺, mevcut: {st.session_state.virtual_cash:,.2f} ₺")
                    else:
                        mevcut = st.session_state.portfolio.get(emir_hisse)
                        if mevcut:
                            toplam_lot = mevcut['lot'] + emir_lot
                            yeni_maliyet = ((mevcut['lot'] * mevcut['maliyet']) + (emir_lot * limit_fiyat)) / toplam_lot
                            st.session_state.portfolio[emir_hisse] = {
                                "lot": toplam_lot, "maliyet": yeni_maliyet, "hedef": mevcut.get("hedef", "Demo")
                            }
                        else:
                            st.session_state.portfolio[emir_hisse] = {"lot": emir_lot, "maliyet": limit_fiyat, "hedef": "Demo"}
                        st.session_state.virtual_cash -= tutar
                        st.session_state.trade_log.insert(0, {
                            "zaman": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "hisse": emir_hisse, "yon": "AL", "lot": emir_lot,
                            "fiyat": limit_fiyat, "tutar": tutar,
                        })
                        _demo_durumu_kaydet()
                        st.success(f"[DEMO] {emir_lot} lot {emir_hisse} {limit_fiyat:.2f} ₺'den alındı.")
                        st.rerun()
                else:  # SAT
                    if emir_lot > elde_lot:
                        st.error(f"Elinizde sadece {elde_lot} lot var, {emir_lot} lot satamazsınız.")
                    else:
                        kalan_lot = elde_lot - emir_lot
                        if kalan_lot == 0:
                            del st.session_state.portfolio[emir_hisse]
                        else:
                            st.session_state.portfolio[emir_hisse]['lot'] = kalan_lot
                        st.session_state.virtual_cash += tutar
                        st.session_state.trade_log.insert(0, {
                            "zaman": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "hisse": emir_hisse, "yon": "SAT", "lot": emir_lot,
                            "fiyat": limit_fiyat, "tutar": tutar,
                        })
                        _demo_durumu_kaydet()
                        st.success(f"[DEMO] {emir_lot} lot {emir_hisse} {limit_fiyat:.2f} ₺'den satıldı.")
                        st.rerun()

    with ec2:
        st.markdown("#### İşlem Geçmişi (Demo)")
        if st.session_state.trade_log:
            df_log = pd.DataFrame(st.session_state.trade_log)
            st.dataframe(df_log, use_container_width=True, hide_index=True)
            if st.button("Geçmişi Temizle", key="demo_log_temizle"):
                st.session_state.trade_log = []
                _demo_durumu_kaydet()
                st.rerun()
        else:
            st.info("Henüz demo işlem yapılmadı.")

    with st.expander("Gerçek Midas hesabıyla nasıl bağlanır? (bilgilendirme)"):
        st.markdown("""
Şu an bildiğim kadarıyla **Midas**, bireysel geliştiricilerin kullanabileceği genel/self-servis bir
emir-gönderme (trading) API'si yayınlamıyor — mobil/web uygulaması dışında resmi bir programatik erişim yok.
Gerçek hesaba bağlı otomatik emir ekranı kurmak isterseniz iki yol var:

1. **Midas'a doğrudan sorun:** Destek/kurumsal iletişim kanallarından API veya kurumsal entegrasyon erişimi olup
   olmadığını, varsa nasıl başvurulacağını isteyin. Bu tür erişimler genelde herkese açık değildir, kurumla
   ayrı görüşme/anlaşma gerektirebilir.
2. **API sunan bir aracı kuruma geçin:** Örn. İş Yatırım'ın **Algolab API**'si ya da yurt dışı işlemler için
   **Interactive Brokers (TWS/IBKR API)** gibi platformlar bireysel/algoritmik erişime resmi olarak izin veriyor.
   Böyle bir API anahtarınız olursa, bu ekranın "sipariş gönder" mantığını gerçek API çağrısıyla değiştirip
   canlıya alabiliriz.

Şimdilik bu ekran, stratejinizi gerçek para riske atmadan test edebileceğiniz bir kâğıt-işlem (paper trading)
ortamı olarak çalışıyor.
        """)

elif mod_nav == "Backtest":
    bolum_basligi("Backtest Laboratuvarı & Kâr/Zarar Motoru", ikon="🧪")
    st.write("Burada kaydettiğiniz hisselerin o günden bugüne ne kadar kâr/zarar getirdiğini anlık olarak görebilirsiniz.")
    
    if os.path.exists(BACKTEST_FILE):
        df_bt = pd.read_csv(BACKTEST_FILE)
        if not df_bt.empty:
            
            if st.button("Güncel Kâr/Zarar Durumunu Hesapla", type="primary", use_container_width=True):
                with st.spinner("Piyasadan güncel fiyatlar çekiliyor ve Kâr/Zarar hesaplanıyor..."):
                    
                    df_bt['Giriş Fiyatı'] = df_bt['Fiyat'].astype(str).str.replace(' ₺', '').str.replace(',', '.').astype(float)
                    
                    guncel_fiyatlar = []
                    fark_yuzdeler = []
                    
                    benzersiz_hisseler = df_bt['Hisse'].unique()
                    guncel_sozluk = {}
                    
                    for s in benzersiz_hisseler:
                        try:
                            h = yf.Ticker(f"{s}.IS").history(period="5d")
                            h = son_gecerli_satirlar(h)  # borsa kapalıyken/taslak satırı at
                            son_fiyat = float(h['Close'].iloc[-1])
                            guncel_sozluk[s] = son_fiyat
                        except Exception:
                            guncel_sozluk[s] = None
                            
                    # Her satır için Kâr/Zarar dökümü
                    for index, row in df_bt.iterrows():
                        h_isim = row['Hisse']
                        g_fiyat = row['Giriş Fiyatı']
                        yeni_fiyat = guncel_sozluk.get(h_isim, None)
                        
                        if yeni_fiyat and g_fiyat > 0:
                            guncel_fiyatlar.append(f"{yeni_fiyat:.2f} ₺")
                            degisim = ((yeni_fiyat - g_fiyat) / g_fiyat) * 100
                            fark_yuzdeler.append(degisim)
                        else:
                            guncel_fiyatlar.append("Veri Yok")
                            fark_yuzdeler.append(0.0)
                            
                    df_bt['Güncel Fiyat'] = guncel_fiyatlar
                    df_bt['Kâr/Zarar (%)'] = fark_yuzdeler
                    def pnl_renk(val):
                        if isinstance(val, float):
                            if val > 0: return f'color: {LQ_GREEN}; font-weight: 600;'
                            elif val < 0: return f'color: {LQ_RED}; font-weight: 600;'
                        return ''
                    def hit_rate_hesapla(islem_getirileri):
                        """
                        islem_getirileri: Her bir işlemin sonucunu (kar/zarar miktarı veya % getiri) içeren liste.
                        Örnek: [5.2, -1.3, 2.4, -0.5, 10.1]
                        """
                        toplam_islem = len(islem_getirileri)
                        
                        if toplam_islem == 0:
                            return 0.0 
                            

                        kazanan_islemler = sum(1 for getiri in islem_getirileri if getiri > 0)
                        kaybeden_islemler = toplam_islem - kazanan_islemler
                        
                        hit_rate = (kazanan_islemler / toplam_islem) * 100
                        
                        print(f"--- BACKTEST SONUÇLARI ---")
                        print(f"Toplam İşlem   : {toplam_islem}")
                        print(f"Kazanan İşlem  : {kazanan_islemler}")
                        print(f"Kaybeden İşlem : {kaybeden_islemler}")
                        print(f"Hit Rate       : %{hit_rate:.2f}")
                        
                        return hit_rate

                    # Test edelim
                    ornek_islemler = [120.5, -45.0, 30.2, 55.0, -10.5, -20.0, 8.4]
                    hesaplanan_hit_rate = hit_rate_hesapla(ornek_islemler)
                    gosterim_df = df_bt[['Tarih', 'Hisse', 'Sinyal', 'Fiyat', 'Güncel Fiyat', 'Kâr/Zarar (%)']]
                    
                    st.success("Hesaplama tamamlandı! İşte algoritmanın performansı:")
                    try:
                        st.dataframe(
                            gosterim_df.style.map(pnl_renk, subset=['Kâr/Zarar (%)']).format({'Kâr/Zarar (%)': "{:.2f}%"}),
                            use_container_width=True, hide_index=True
                        )
                    except AttributeError:
                        st.dataframe(
                            gosterim_df.style.applymap(pnl_renk, subset=['Kâr/Zarar (%)']).format({'Kâr/Zarar (%)': "{:.2f}%"}),
                            use_container_width=True, hide_index=True
                        )
            
            st.divider()
            st.info("💡 **Silme İşlemi:** Veritabanından çıkarmak istediğiniz satırın en solundaki gri sıra numarasına tıklayıp klavyenizden 'Delete' tuşuna veya sağ üstteki çöp kutusu ikonuna basın.")
            
            duzenlenmis_df = st.data_editor(
                df_bt[['Tarih', 'Hisse', 'Fiyat', 'Sinyal']], 
                num_rows="dynamic", 
                use_container_width=True,
                key="bt_editor",
                hide_index=False
            )
            
            if st.button("💾 Değişiklikleri / Silinenleri Kaydet"):
                duzenlenmis_df.to_csv(BACKTEST_FILE, index=False)
                st.success("✅ Veritabanı başarıyla güncellendi!")
                st.rerun() # Temizlik sonrası sayfayı yenile
                
        else:
            st.warning("Backtest listeniz şu an boş. Lütfen Piyasa Tarayıcı üzerinden hisse ekleyin.")
    else:
        st.warning("Backtest listeniz şu an boş. Lütfen Piyasa Tarayıcı üzerinden hisse ekleyin.")

elif mod_nav == "Portföy İzleme":
    bolum_basligi("Portföy Performans & Temettü Analizi", ikon="💼")
    
    if not st.session_state.get('portfolio'):
        st.warning("Portföyünüz boş. Lütfen hisse ekleyin.")
    else:
        rows = []
        with st.spinner("Canlı piyasa verileri ve temettü detayları çekiliyor..."):
            for s, info in st.session_state.portfolio.items():
                try:
                    t = yf.Ticker(f"{s}.IS")
                    hist = t.history(period="1d")
                    if hist.empty: continue
                    
                    # 1. Anlık Veriler
                    cp = hist['close'].iloc[-1] # Fiyat
                    div_yield = (t.info.get('dividendYield', 0) or 0) * 100 # Verim %
                    
                    # 2. Akıllı Temettü Hesaplama (TL bazında)
                    divs = t.dividends
                    yillik_temettu_tl = 0.0
                    
                    if not divs.empty:
                        # Son 1 yıldaki (365 gün) toplam ödeme
                        son_bir_yil = divs[divs.index > (datetime.now() - timedelta(days=365))].sum()
                        
                        if son_bir_yil > 0:
                            yillik_temettu_tl = son_bir_yil
                        else:
                            # Eğer son 1 yılda ödeme yoksa, en son ödediği tam yılın toplamına bak
                            son_odeme_tarihi = divs.index[-1]
                            yillik_temettu_tl = divs[divs.index.year == son_odeme_tarihi.year].sum()
                    
                    lt = info['lot']
                    maliyet = info['maliyet']
                    toplam_deger = cp * lt
                    beklenen_yillik_gelir = yillik_temettu_tl * lt

                    rows.append({
                        "Hisse": s,
                        "Fiyat": f"{cp:.2f} ₺",
                        "Lot": lt,
                        "Maliyet": f"{maliyet:.2f} ₺",
                        "Verim": f"%{div_yield:.2f}",
                        "Hisse Başı (₺)": f"{yillik_temettu_tl:.2f} ₺",
                        "Yıllık Toplam Gelir": f"{beklenen_yillik_gelir:,.2f} ₺",
                        "Portföy Değeri": f"{toplam_deger:,.2f} ₺"
                    })
                except Exception as e:
                    continue

        # 📊 PROFESYONEL PORTFÖY TABLOSU
        if rows:
            df_final = pd.DataFrame(rows)
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            
            # Alt Özet Metrikler
            toplam_gelir = sum([float(str(r['Yıllık Toplam Gelir']).replace(' ₺', '').replace(',', '')) for r in rows])
            st.success(f"Bu portföyün sana yıllık tahmini nakit akışı: **{toplam_gelir:,.2f} ₺**")
        else:
            st.error("Veriler işlenirken bir sorun oluştu.")

elif "Bildirimler" in mod_nav:
    bolum_basligi("Bildirimler", ikon="🔔")
    if st.button("Temizle"): st.session_state.notifications = []; st.rerun()
    for n in st.session_state.get('notifications', []):
        with st.container(border=True):
            c = st.columns([0.1, 0.9]); c[0].caption(n['time']); c[1].info(n['msg'])

st.sidebar.caption(f"Umut Emre Çelebi | 2026")