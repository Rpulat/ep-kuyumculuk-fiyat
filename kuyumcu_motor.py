import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import base64
import traceback
import gspread
from google.oauth2.service_account import Credentials

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

ADMIN_MODE = st.query_params.get("admin") == "1"

# =====================================================
# GOOGLE SHEETS AYARLARI
# =====================================================

SHEET_TAB_ADI = "carpanlar"

DEFAULT_MANUEL_HAS_ALTIN = 6588.67

DEFAULT_CARPANLAR = {
    "24 Ayar Gram": 1.000,
    "22 Ayar Gram": 0.916,
    "Çeyrek Altın": 1.760,
    "Yarım Altın": 3.520,
    "Tam Altın": 7.040,
    "Ata Lira": 7.216,
    "22 Ayar Bilezik": 0.916
}

SHEET_HATA_DETAYI = None


# =====================================================
# TÜRKİYE SAATİ
# =====================================================

def turkiye_saati():
    return datetime.now(ZoneInfo("Europe/Istanbul"))


def turkiye_saati_formatli():
    return turkiye_saati().strftime("%d.%m.%Y %H:%M")


# =====================================================
# SAYI TEMİZLEME
# =====================================================

def sayi_temizle(deger, varsayilan=None):
    """
    Türkçe / İngilizce sayı formatlarını güvenli float'a çevirir.

    Örnek:
    6.588,67 -> 6588.67
    6,588.67 -> 6588.67
    6588,67  -> 6588.67
    6588.67  -> 6588.67
    """

    if deger is None:
        return varsayilan

    try:
        if isinstance(deger, (int, float)):
            return float(deger)

        metin = str(deger).strip()
        metin = metin.replace("TL", "")
        metin = metin.replace("TRY", "")
        metin = metin.replace("₺", "")
        metin = metin.replace(" ", "")
        metin = metin.strip()

        if metin == "":
            return varsayilan

        if "." in metin and "," in metin:
            son_nokta = metin.rfind(".")
            son_virgul = metin.rfind(",")

            if son_virgul > son_nokta:
                metin = metin.replace(".", "").replace(",", ".")
            else:
                metin = metin.replace(",", "")

        elif "," in metin:
            metin = metin.replace(",", ".")

        return float(metin)

    except Exception:
        return varsayilan


# =====================================================
# GOOGLE SHEETS BAĞLANTISI
# =====================================================

def google_sheets_aktif_mi():
    try:
        return "GOOGLE_SHEET_ID" in st.secrets and "gcp_service_account" in st.secrets
    except Exception:
        return False


def google_sheet_baglan():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    service_account_info = dict(st.secrets["gcp_service_account"])

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=scopes
    )

    gc = gspread.authorize(credentials)

    sheet_id = st.secrets["GOOGLE_SHEET_ID"]

    spreadsheet = gc.open_by_key(sheet_id)

    try:
        worksheet = spreadsheet.worksheet(SHEET_TAB_ADI)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=SHEET_TAB_ADI,
            rows=30,
            cols=2
        )

        rows = [["urun_adi", "carpan"]]

        for urun_adi, carpan in DEFAULT_CARPANLAR.items():
            rows.append([urun_adi, carpan])

        rows.append(["MANUEL_HAS_ALTIN", DEFAULT_MANUEL_HAS_ALTIN])

        worksheet.update("A1:B" + str(len(rows)), rows)

    return worksheet


def ayarlari_yukle():
    global SHEET_HATA_DETAYI

    carpanlar = DEFAULT_CARPANLAR.copy()
    manuel_has_altin = DEFAULT_MANUEL_HAS_ALTIN
    ayar_kaynagi = "Varsayılan"

    SHEET_HATA_DETAYI = None

    if not google_sheets_aktif_mi():
        SHEET_HATA_DETAYI = "Streamlit Secrets içinde GOOGLE_SHEET_ID veya gcp_service_account bulunamadı."
        return carpanlar, manuel_has_altin, ayar_kaynagi

    try:
        worksheet = google_sheet_baglan()
        records = worksheet.get_all_records()

        if not records:
            ayarlari_kaydet(carpanlar, manuel_has_altin)
            return carpanlar, manuel_has_altin, "Google Sheets"

        for row in records:
            urun_adi = str(row.get("urun_adi", "")).strip()
            carpan_ham = row.get("carpan", "")

            if urun_adi == "MANUEL_HAS_ALTIN":
                okunan_manuel = sayi_temizle(carpan_ham, DEFAULT_MANUEL_HAS_ALTIN)

                if okunan_manuel and 0 < okunan_manuel < 1000000:
                    manuel_has_altin = okunan_manuel

            elif urun_adi in carpanlar:
                okunan_carpan = sayi_temizle(carpan_ham, carpanlar[urun_adi])

                if okunan_carpan and 0 < okunan_carpan <= 20:
                    carpanlar[urun_adi] = okunan_carpan

        return carpanlar, manuel_has_altin, "Google Sheets"

    except Exception:
        SHEET_HATA_DETAYI = traceback.format_exc()
        return carpanlar, manuel_has_altin, "Varsayılan"


def ayarlari_kaydet(carpanlar, manuel_has_altin):
    if not google_sheets_aktif_mi():
        return False, "Google Sheets Secrets tanımlı değil."

    try:
        worksheet = google_sheet_baglan()

        rows = [["urun_adi", "carpan"]]

        for urun_adi, carpan in carpanlar.items():
            rows.append([urun_adi, float(carpan)])

        rows.append(["MANUEL_HAS_ALTIN", float(manuel_has_altin)])

        worksheet.clear()
        worksheet.update("A1:B" + str(len(rows)), rows)

        return True, "Ayarlar Google Sheets'e kaydedildi."

    except Exception:
        return False, traceback.format_exc()


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

html, body, [class*="css"] {{
    font-family: "Segoe UI", sans-serif;
}}

.block-container {{
    padding-top: 1.2rem;
    padding-bottom: 1.2rem;
    overflow: visible !important;
}}

.logo-area {{
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 8px;
    margin-bottom: 8px;
    padding-top: 10px;
    overflow: visible !important;
}}

.logo-img {{
    width: 125px;
    max-width: 125px;
    height: auto;
    display: block;
    object-fit: contain;
    overflow: visible !important;
}}

.main-title {{
    font-size: 38px;
    font-weight: 900;
    color: var(--text);
    line-height: 1.12;
    text-align: center;
    margin-top: 0px;
    margin-bottom: 4px;
}}

.subtitle {{
    font-size: 15px;
    color: var(--muted);
    text-align: center;
    margin-bottom: 14px;
}}

.top-badges {{
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 8px;
    margin-bottom: 14px;
}}

.badge-box {{
    background: white;
    border: 1px solid var(--border);
    color: #444;
    padding: 9px 15px;
    border-radius: 999px;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}}

.refresh-area {{
    width: 100%;
    display: flex;
    justify-content: center;
    margin-top: 4px;
    margin-bottom: 20px;
}}

.stButton > button {{
    background: linear-gradient(135deg, #050505, #1c1c1c) !important;
    color: #D4AF37 !important;
    border: 1.8px solid #D4AF37 !important;
    border-radius: 999px !important;
    padding: 0.55rem 1.35rem !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    box-shadow: 0 10px 28px rgba(0,0,0,0.16) !important;
    transition: all 0.25s ease !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px) !important;
    color: #fff4c2 !important;
    box-shadow: 0 14px 34px rgba(0,0,0,0.22), 0 0 18px rgba(212,175,55,0.25) !important;
}}

.section-title {{
    font-size: 30px;
    font-weight: 900;
    color: var(--text);
    margin-top: 10px;
    margin-bottom: 18px;
}}

.gold-card {{
    background: linear-gradient(180deg, #0d0d0d 0%, #060606 100%);
    border: 2px solid var(--gold);
    border-radius: 22px;
    padding: 28px 16px;
    text-align: center;
    min-height: 175px;
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
    font-size: 21px;
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
    font-size: 33px;
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
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
        overflow: visible !important;
    }}

    .logo-area {{
        margin-top: 6px;
        margin-bottom: 8px;
        padding-top: 8px;
        overflow: visible !important;
    }}

    .logo-img {{
        width: 105px;
        max-width: 105px;
        overflow: visible !important;
    }}

    .main-title {{
        font-size: 28px;
    }}

    .subtitle {{
        font-size: 14px;
        margin-bottom: 12px;
    }}

    .top-badges {{
        margin-bottom: 12px;
    }}

    .badge-box {{
        font-size: 13px;
        padding: 8px 13px;
    }}

    .section-title {{
        font-size: 24px;
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
# YARDIMCI FONKSİYONLAR
# =====================================================

def temizle_ve_cevir(fiyat):
    return sayi_temizle(fiyat, None)


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
def has_altin_api_al():
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
                    "hata": son_hatalar,
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


def has_altin_al(manuel_has_altin):
    api_veri = has_altin_api_al()

    if api_veri["basarili"]:
        return api_veri

    return {
        "basarili": True,
        "kaynak": "Manuel / Yedek Has Altın",
        "has_altin": manuel_has_altin,
        "hata": api_veri["hata"],
        "cekilme_zamani": turkiye_saati_formatli()
    }


# =====================================================
# FİYAT HESAPLAMA
# =====================================================

def fiyat_hesapla(has_altin, carpan):
    if has_altin is None or carpan is None:
        return None
    return has_altin * carpan


def fiyatlari_olustur(has_altin, carpanlar):
    fiyatlar = {}

    for urun_adi, carpan in carpanlar.items():
        fiyatlar[urun_adi] = fiyat_hesapla(has_altin, carpan)

    return fiyatlar


# =====================================================
# YÖNETİCİ PANELİ
# =====================================================

def yonetici_paneli(carpanlar, manuel_has_altin, ayar_kaynagi):
    if not ADMIN_MODE:
        return carpanlar, manuel_has_altin

    with st.sidebar:
        st.markdown("<div class='sidebar-title'>🔐 Yönetici Paneli</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-note'>Çarpanları ve manuel has altın değerini buradan yönetebilirsiniz.</div>", unsafe_allow_html=True)

        admin_sifre = st.text_input("Yönetici Şifresi", type="password")

        DOGRU_SIFRE = "3471"

        if admin_sifre != DOGRU_SIFRE:
            st.info("Yönetici ayarlarını açmak için şifre giriniz.")
            return carpanlar, manuel_has_altin

        st.success("Yönetici girişi aktif")
        st.caption(f"Ayar Kaynağı: {ayar_kaynagi}")

        with st.form("admin_form"):
            st.markdown("### Manuel Has Altın")

            guvenli_manuel_has = sayi_temizle(manuel_has_altin, DEFAULT_MANUEL_HAS_ALTIN)

            if guvenli_manuel_has is None or guvenli_manuel_has <= 0:
                guvenli_manuel_has = DEFAULT_MANUEL_HAS_ALTIN

            yeni_manuel_has_altin = st.number_input(
                "Canlı kaynak çalışmazsa kullanılacak manuel has altın",
                min_value=0.0,
                max_value=1000000.0,
                value=float(guvenli_manuel_has),
                step=1.0,
                format="%.2f",
                key="manuel_has_altin_input"
            )

            st.markdown("### Has Çarpanları")

            yeni_carpanlar = {}

            for urun_adi, mevcut_carpan in carpanlar.items():
                guvenli_carpan = sayi_temizle(mevcut_carpan, DEFAULT_CARPANLAR.get(urun_adi, 1.0))

                if guvenli_carpan is None or guvenli_carpan <= 0 or guvenli_carpan > 20:
                    guvenli_carpan = DEFAULT_CARPANLAR.get(urun_adi, 1.0)

                yeni_carpanlar[urun_adi] = st.number_input(
                    f"{urun_adi}",
                    min_value=0.000,
                    max_value=20.000,
                    value=float(guvenli_carpan),
                    step=0.001,
                    format="%.3f",
                    key=f"carpan_{urun_adi}"
                )

            col_a, col_b = st.columns(2)

            with col_a:
                kaydet = st.form_submit_button("Ayarları Kaydet", use_container_width=True)

            with col_b:
                varsayilan = st.form_submit_button("Varsayılanlara Dön", use_container_width=True)

        if kaydet:
            basarili, mesaj = ayarlari_kaydet(yeni_carpanlar, yeni_manuel_has_altin)
            st.cache_data.clear()

            if basarili:
                st.success(mesaj)
            else:
                st.error("Google Sheets kaydı başarısız.")
                st.code(mesaj)

            st.rerun()

        if varsayilan:
            basarili, mesaj = ayarlari_kaydet(DEFAULT_CARPANLAR.copy(), DEFAULT_MANUEL_HAS_ALTIN)
            st.cache_data.clear()

            if basarili:
                st.success("Varsayılan değerlere dönüldü.")
            else:
                st.error("Google Sheets kaydı başarısız.")
                st.code(mesaj)

            st.rerun()

    return carpanlar, manuel_has_altin


# =====================================================
# HEADER
# =====================================================

def header_olustur(cekilme_zamani):
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
        "<div class='main-title'>ENES PULAT Kuyumculuk<br>Canlı Fiyat Ekranı</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>Güncel piyasa verilerine göre anlık altın fiyat panosu</div>",
        unsafe_allow_html=True
    )

    st.markdown(f"""
    <div class='top-badges'>
        <div class='badge-box'>🕒 Türkiye Saati: {cekilme_zamani}</div>
    </div>
    """, unsafe_allow_html=True)


def fiyat_guncelle_butonu():
    st.markdown("<div class='refresh-area'>", unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1.4, 1, 1.4])

    with col_center:
        if st.button("🔄 Fiyatları Güncelle", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


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

carpanlar, manuel_has_altin, ayar_kaynagi = ayarlari_yukle()

carpanlar, manuel_has_altin = yonetici_paneli(carpanlar, manuel_has_altin, ayar_kaynagi)

carpanlar, manuel_has_altin, ayar_kaynagi = ayarlari_yukle()

veri = has_altin_al(manuel_has_altin)

has_altin = veri["has_altin"]
fiyatlar = fiyatlari_olustur(has_altin, carpanlar)

if ADMIN_MODE and SHEET_HATA_DETAYI:
    st.warning("Google Sheets okunamadı. Varsayılan ayarlar kullanılıyor.")
    with st.expander("Google Sheets hata detayları"):
        st.code(SHEET_HATA_DETAYI)

header_olustur(veri["cekilme_zamani"])

fiyat_guncelle_butonu()

if ADMIN_MODE:
    st.markdown(f"""
    <div class='admin-source-box'>
        <b>Yönetici Teknik Bilgi:</b><br>
        Veri Kaynağı: {veri["kaynak"]}<br>
        Canlı / Manuel Has Altın: {para_formatla(has_altin)}<br>
        Çarpan Kaynağı: {ayar_kaynagi}
    </div>
    """, unsafe_allow_html=True)

    if veri["hata"]:
        with st.expander("Canlı API hata detayları"):
            st.write(veri["hata"])


# =====================================================
# CANLI FİYAT PANOSU
# =====================================================

st.markdown("<div class='section-title'>Canlı Altın Fiyat Panosu</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    fiyat_karti("24 Ayar Gram", fiyatlar["24 Ayar Gram"])

with col2:
    fiyat_karti("22 Ayar Gram", fiyatlar["22 Ayar Gram"])

with col3:
    fiyat_karti("Çeyrek Altın", fiyatlar["Çeyrek Altın"])

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    fiyat_karti("Yarım Altın", fiyatlar["Yarım Altın"])

with col5:
    fiyat_karti("Tam Altın", fiyatlar["Tam Altın"])

with col6:
    fiyat_karti("Ata Lira", fiyatlar["Ata Lira"])


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