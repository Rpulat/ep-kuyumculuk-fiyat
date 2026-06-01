import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import base64

# =====================================================
# SAYFA AYARLARI
# =====================================================

st.set_page_config(
    page_title="ENES PULAT Kuyumculuk Canlı Fiyat Ekranı",
    page_icon="💎",
    layout="wide"
)

# =====================================================
# ADMIN MODU
# =====================================================
# Müşteri normal linkten girer:
# https://epkuyumculuk.streamlit.app
#
# Yönetici özel linkten girer:
# https://epkuyumculuk.streamlit.app/?admin=1

ADMIN_MODE = st.query_params.get("admin") == "1"


# =====================================================
# TÜRKİYE SAATİ
# =====================================================

def turkiye_saati():
    return datetime.now(ZoneInfo("Europe/Istanbul"))


def turkiye_saati_formatli():
    return turkiye_saati().strftime("%d.%m.%Y %H:%M")


# =====================================================
# LOGO
# =====================================================

def logo_base64_yap(dosya_yolu):
    with open(dosya_yolu, "rb") as file:
        return base64.b64encode(file.read()).decode()


# =====================================================
# STREAMLIT GİZLEME CSS
# =====================================================

streamlit_gizleme_css = ""

if not ADMIN_MODE:
    streamlit_gizleme_css = """
    footer {
        visibility: hidden !important;
        height: 0 !important;
    }

    footer:after {
        content: "" !important;
        display: none !important;
    }

    .stDeployButton {
        display: none !important;
    }

    [data-testid="stToolbar"] {
        display: none !important;
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }

    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    [data-testid="collapsedControl"] {
        display: none !important;
    }

    [data-testid="stSidebar"] {
        display: none !important;
    }
    """


# =====================================================
# TASARIM
# =====================================================

st.markdown(f"""
<style>
:root {{
    --gold: #D4AF37;
    --gold-soft: #e6c96b;
    --dark: #0b0b0b;
    --soft-bg: #f7f5ef;
    --text: #2c2c35;
    --muted: #777777;
    --border: #e8d8a2;
}}

html, body, [class*="css"]  {{
    font-family: "Segoe UI", sans-serif;
}}

.block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
}}

.logo-area {{
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 10px;
    margin-bottom: 18px;
}}

.logo-img {{
    width: 190px;
    max-width: 190px;
    height: auto;
    display: block;
    object-fit: contain;
}}

.main-title {{
    font-size: 48px;
    font-weight: 900;
    color: var(--text);
    line-height: 1.15;
    text-align: center;
    margin-top: 5px;
    margin-bottom: 8px;
}}

.subtitle {{
    font-size: 18px;
    color: var(--muted);
    text-align: center;
    margin-bottom: 25px;
}}

.top-badges {{
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 12px;
    margin-bottom: 30px;
}}

.badge-box {{
    background: white;
    border: 1px solid var(--border);
    color: #444;
    padding: 10px 16px;
    border-radius: 999px;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}}

.section-title {{
    font-size: 30px;
    font-weight: 900;
    color: var(--text);
    margin-top: 15px;
    margin-bottom: 18px;
}}

.gold-card {{
    background: linear-gradient(180deg, #0d0d0d 0%, #060606 100%);
    border: 2px solid var(--gold);
    border-radius: 22px;
    padding: 24px 16px;
    text-align: center;
    min-height: 170px;
    box-shadow: 0 14px 40px rgba(0,0,0,0.14);
}}

.gold-card-featured {{
    background: linear-gradient(180deg, #0d0d0d 0%, #000000 100%);
    border: 2px solid var(--gold);
    border-radius: 26px;
    padding: 34px 18px;
    text-align: center;
    min-height: 210px;
    box-shadow: 0 18px 55px rgba(0,0,0,0.20), 0 0 28px rgba(212,175,55,0.20);
}}

.gold-name {{
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 12px;
}}

.gold-name-featured {{
    color: #ffffff;
    font-size: 28px;
    font-weight: 900;
    margin-bottom: 16px;
}}

.gold-price {{
    color: var(--gold);
    font-size: 31px;
    font-weight: 900;
    line-height: 1.15;
    user-select: none;
}}

.gold-price-featured {{
    color: var(--gold);
    font-size: 54px;
    font-weight: 900;
    line-height: 1.15;
    user-select: none;
}}

.gold-sub {{
    color: #b7b7b7;
    font-size: 13px;
    margin-top: 10px;
}}

.gold-sub-featured {{
    color: #c9c9c9;
    font-size: 15px;
    margin-top: 14px;
}}

.info-box {{
    background: #fcfaf4;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid var(--border);
    margin-top: 28px;
    font-size: 17px;
    line-height: 1.9;
    color: #2b2b2b;
}}

.small-note {{
    font-size: 14px;
    color: #666;
    text-align: center;
    margin-top: 18px;
    line-height: 1.6;
}}

.footer-brand {{
    text-align: center;
    margin-top: 34px;
    font-size: 14px;
    color: #999;
}}

.sidebar-title {{
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 8px;
}}

.sidebar-note {{
    font-size: 13px;
    color: #777;
    margin-bottom: 14px;
}}

.admin-source-box {{
    background: #fff7df;
    border: 1px solid #e8d8a2;
    padding: 12px;
    border-radius: 12px;
    font-size: 13px;
    margin-top: 10px;
}}

@media screen and (max-width: 768px) {{
    .logo-img {{
        width: 145px;
        max-width: 145px;
    }}

    .main-title {{
        font-size: 34px;
    }}

    .subtitle {{
        font-size: 15px;
    }}

    .gold-price {{
        font-size: 25px;
    }}

    .gold-name-featured {{
        font-size: 23px;
    }}

    .gold-price-featured {{
        font-size: 38px;
    }}
}}

{streamlit_gizleme_css}
</style>
""", unsafe_allow_html=True)


# =====================================================
# VARSAYILAN ÇARPANLAR
# =====================================================

DEFAULT_CARPANLAR = {
    "24 Ayar Gram": 1.000,
    "22 Ayar Gram": 0.916,
    "14 Ayar Gram": 0.585,
    "Çeyrek Altın": 1.760,
    "Yarım Altın": 3.520,
    "Tam Altın": 7.040,
    "Ata Lira": 7.216,
    "Cumhuriyet Altını": 7.216,
    "22 Ayar Bilezik": 0.916
}


# =====================================================
# SESSION STATE
# =====================================================

if "carpanlar" not in st.session_state:
    st.session_state.carpanlar = DEFAULT_CARPANLAR.copy()


# =====================================================
# YARDIMCI FONKSİYONLAR
# =====================================================

def temizle_ve_cevir(fiyat):
    if fiyat is None:
        return None

    fiyat = str(fiyat).strip()
    fiyat = fiyat.replace("TL", "").replace("TRY", "").replace("₺", "").strip()

    if "." in fiyat and "," in fiyat:
        fiyat = fiyat.replace(".", "").replace(",", ".")
    elif "," in fiyat:
        fiyat = fiyat.replace(",", ".")

    try:
        return float(fiyat)
    except:
        return None


def para_formatla(tutar):
    if tutar is None:
        return "-"
    return f"{tutar:,.2f} TL"


def normalize_text(text):
    text = str(text).lower()
    text = text.replace("ı", "i")
    text = text.replace("ğ", "g")
    text = text.replace("ü", "u")
    text = text.replace("ş", "s")
    text = text.replace("ö", "o")
    text = text.replace("ç", "c")
    text = text.replace("-", " ")
    text = text.replace("_", " ")
    return text


def veri_icinden_fiyat_bul(data, aranan_kelimeler):
    if isinstance(data, dict):
        for key, value in data.items():
            key_normal = normalize_text(key)
            eslesme_var = all(kelime in key_normal for kelime in aranan_kelimeler)

            if eslesme_var:
                if isinstance(value, dict):
                    for sell_key in [
                        "Selling", "selling", "SATIS", "satis", "Satış",
                        "Satis", "satis_fiyat", "sell", "price"
                    ]:
                        if sell_key in value:
                            fiyat = temizle_ve_cevir(value[sell_key])
                            if fiyat and fiyat > 0:
                                return fiyat

                    for possible_value in value.values():
                        fiyat = temizle_ve_cevir(possible_value)
                        if fiyat and fiyat > 0:
                            return fiyat
                else:
                    fiyat = temizle_ve_cevir(value)
                    if fiyat and fiyat > 0:
                        return fiyat

        for value in data.values():
            result = veri_icinden_fiyat_bul(value, aranan_kelimeler)
            if result:
                return result

    elif isinstance(data, list):
        for item in data:
            result = veri_icinden_fiyat_bul(item, aranan_kelimeler)
            if result:
                return result

    return None


# =====================================================
# CANLI HAS ALTIN VERİSİ
# =====================================================

@st.cache_data(ttl=60)
def has_altin_al():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*"
    }

    kaynaklar = [
        {"ad": "Truncgil v4", "url": "https://finans.truncgil.com/v4/today.json"},
        {"ad": "Truncgil v3", "url": "https://finans.truncgil.com/v3/today.json"},
        {"ad": "Truncgil eski", "url": "https://finans.truncgil.com/today.json"},
        {"ad": "GenelPara eski", "url": "https://api.genelpara.com/embed/altin.json"}
    ]

    son_hatalar = []

    for kaynak in kaynaklar:
        try:
            response = requests.get(kaynak["url"], headers=headers, timeout=8)

            if response.status_code != 200:
                son_hatalar.append(f"{kaynak['ad']}: HTTP {response.status_code}")
                continue

            data = response.json()

            gram_altin = (
                veri_icinden_fiyat_bul(data, ["gram", "altin"])
                or veri_icinden_fiyat_bul(data, ["gram"])
                or veri_icinden_fiyat_bul(data, ["ga"])
            )

            if gram_altin and gram_altin > 0:
                return {
                    "basarili": True,
                    "kaynak": kaynak["ad"],
                    "has_altin": gram_altin,
                    "hata": None,
                    "cekilme_zamani": turkiye_saati_formatli()
                }

            son_hatalar.append(f"{kaynak['ad']}: has altın bulunamadı")

        except Exception as e:
            son_hatalar.append(f"{kaynak['ad']}: {str(e)}")

    return {
        "basarili": False,
        "kaynak": None,
        "has_altin": None,
        "hata": son_hatalar,
        "cekilme_zamani": turkiye_saati_formatli()
    }


# =====================================================
# FİYAT HESAPLAMA
# =====================================================

def fiyat_hesapla(has_altin, carpan):
    if has_altin is None or carpan is None:
        return None
    return has_altin * carpan


def fiyatlari_olustur(has_altin):
    fiyatlar = {}
    for urun_adi, carpan in st.session_state.carpanlar.items():
        fiyatlar[urun_adi] = fiyat_hesapla(has_altin, carpan)
    return fiyatlar


# =====================================================
# YÖNETİCİ PANELİ
# =====================================================

def yonetici_paneli():
    if not ADMIN_MODE:
        return

    with st.sidebar:
        st.markdown("<div class='sidebar-title'>🔐 Yönetici Paneli</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-note'>Çarpanları sadece siz yönetin.</div>", unsafe_allow_html=True)

        admin_sifre = st.text_input("Yönetici Şifresi", type="password")

        DOGRU_SIFRE = "3471"

        if admin_sifre != DOGRU_SIFRE:
            st.info("Yönetici ayarlarını açmak için şifre giriniz.")
            return

        st.success("Yönetici girişi aktif")

        with st.form("admin_form"):
            st.markdown("### Has Çarpanları")

            yeni_carpanlar = {}
            for urun_adi, mevcut_carpan in st.session_state.carpanlar.items():
                yeni_carpanlar[urun_adi] = st.number_input(
                    f"{urun_adi}",
                    min_value=0.000,
                    max_value=20.000,
                    value=float(mevcut_carpan),
                    step=0.001,
                    format="%.3f"
                )

            col_a, col_b = st.columns(2)

            with col_a:
                kaydet = st.form_submit_button("Fiyatları Güncelle", use_container_width=True)

            with col_b:
                varsayilan = st.form_submit_button("Varsayılanlara Dön", use_container_width=True)

        if kaydet:
            st.session_state.carpanlar = yeni_carpanlar.copy()
            st.success("Çarpanlar güncellendi.")

        if varsayilan:
            st.session_state.carpanlar = DEFAULT_CARPANLAR.copy()
            st.success("Varsayılan değerlere dönüldü.")


# =====================================================
# HEADER
# =====================================================

def header_olustur(has_altin, cekilme_zamani):
    if os.path.exists("logo.png"):
        logo_base64 = logo_base64_yap("logo.png")
        st.markdown(f"""
        <div class="logo-area">
            <img class="logo-img" src="data:image/png;base64,{logo_base64}">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Logo dosyası bulunamadı. Repo içine 'logo.png' adıyla yükleyin.")

    st.markdown(
        "<div class='main-title'>EP Kuyumculuk<br>Canlı Fiyat Ekranı</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>Güncel has altın verisine göre anlık altın fiyat panosu</div>",
        unsafe_allow_html=True
    )

    st.markdown(f"""
    <div class='top-badges'>
        <div class='badge-box'>🟡 Canlı Has Altın: {para_formatla(has_altin)}</div>
        <div class='badge-box'>🕒 Türkiye Saati: {cekilme_zamani}</div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# KART OLUŞTURMA
# =====================================================

def fiyat_karti(urun_adi, fiyat):
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>{urun_adi}</div>
        <div class='gold-price'>{para_formatla(fiyat)}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)


def bilezik_karti(fiyat):
    st.markdown(f"""
    <div class='gold-card-featured'>
        <div class='gold-name-featured'>22 Ayar Bilezik</div>
        <div class='gold-price-featured'>{para_formatla(fiyat)}</div>
        <div class='gold-sub-featured'>Gram satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# ANA AKIŞ
# =====================================================

yonetici_paneli()

veri = has_altin_al()

if not veri["basarili"]:
    st.error("Piyasa verilerine ulaşılamıyor. Lütfen birkaç dakika sonra tekrar deneyiniz.")
    with st.expander("Teknik hata detayları"):
        st.write(veri["hata"])
    st.stop()

has_altin = veri["has_altin"]
fiyatlar = fiyatlari_olustur(has_altin)

header_olustur(has_altin, veri["cekilme_zamani"])

if ADMIN_MODE:
    st.markdown(f"""
    <div class='admin-source-box'>
        <b>Yönetici Teknik Bilgi:</b><br>
        Veri Kaynağı: {veri["kaynak"]}<br>
        Canlı Has Altın: {para_formatla(has_altin)}
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# CANLI FİYAT PANOSU
# =====================================================

st.markdown("<div class='section-title'>Canlı Altın Fiyat Panosu</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    fiyat_karti("24 Ayar Gram", fiyatlar["24 Ayar Gram"])

with col2:
    fiyat_karti("22 Ayar Gram", fiyatlar["22 Ayar Gram"])

with col3:
    fiyat_karti("14 Ayar Gram", fiyatlar["14 Ayar Gram"])

with col4:
    fiyat_karti("Çeyrek Altın", fiyatlar["Çeyrek Altın"])

st.markdown("<br>", unsafe_allow_html=True)

col5, col6, col7, col8 = st.columns(4)

with col5:
    fiyat_karti("Yarım Altın", fiyatlar["Yarım Altın"])

with col6:
    fiyat_karti("Tam Altın", fiyatlar["Tam Altın"])

with col7:
    fiyat_karti("Ata Lira", fiyatlar["Ata Lira"])

with col8:
    fiyat_karti("Cumhuriyet Altını", fiyatlar["Cumhuriyet Altını"])


# =====================================================
# 22 AYAR BİLEZİK
# =====================================================

st.markdown("---")
st.markdown("<div class='section-title'>22 Ayar Bilezik Fiyatı</div>", unsafe_allow_html=True)

bilezik_karti(fiyatlar["22 Ayar Bilezik"])


# =====================================================
# BİLGİ ALANI
# =====================================================

st.markdown(f"""
<div class='info-box'>
    <b>Canlı Has Altın:</b> {para_formatla(has_altin)}<br>
    <b>22 Ayar Bilezik:</b> {para_formatla(fiyatlar["22 Ayar Bilezik"])}<br>
    <b>Türkiye Saati:</b> {veri["cekilme_zamani"]}
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<div class='small-note'>Bu ekran bilgilendirme amaçlıdır. Nihai fiyat piyasa hareketi, ürün gramı ve mağaza onayına göre netleşir.</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='footer-brand'>ENES PULAT Kuyumculuk</div>",
    unsafe_allow_html=True
)