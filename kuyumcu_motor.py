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
# TÜRKİYE SAATİ
# =====================================================

def turkiye_saati():
    return datetime.now(ZoneInfo("Europe/Istanbul"))


def turkiye_saati_formatli():
    return turkiye_saati().strftime("%d.%m.%Y %H:%M")


# =====================================================
# LOGO YARDIMCI FONKSİYONU
# =====================================================

def logo_base64_yap(dosya_yolu):
    with open(dosya_yolu, "rb") as file:
        return base64.b64encode(file.read()).decode()


# =====================================================
# TASARIM
# =====================================================

st.markdown("""
<style>
:root {
    --gold: #D4AF37;
    --gold-soft: #e6c96b;
    --dark: #0b0b0b;
    --soft-bg: #f7f5ef;
    --text: #2c2c35;
    --muted: #777777;
    --border: #e8d8a2;
}

html, body, [class*="css"]  {
    font-family: "Segoe UI", sans-serif;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* LOGO VE HEADER */
.logo-area {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 10px;
    margin-bottom: 18px;
}

.logo-img {
    width: 190px;
    max-width: 190px;
    height: auto;
    display: block;
    object-fit: contain;
}

.main-title {
    font-size: 48px;
    font-weight: 900;
    color: var(--text);
    line-height: 1.15;
    text-align: center;
    margin-top: 5px;
    margin-bottom: 8px;
}

.subtitle {
    font-size: 18px;
    color: var(--muted);
    text-align: center;
    margin-bottom: 25px;
}

.top-badges {
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 12px;
    margin-bottom: 30px;
}

.badge-box {
    background: white;
    border: 1px solid var(--border);
    color: #444;
    padding: 10px 16px;
    border-radius: 999px;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}

.section-title {
    font-size: 30px;
    font-weight: 900;
    color: var(--text);
    margin-top: 15px;
    margin-bottom: 18px;
}

.gold-card {
    background: linear-gradient(180deg, #0d0d0d 0%, #060606 100%);
    border: 2px solid var(--gold);
    border-radius: 22px;
    padding: 24px 16px;
    text-align: center;
    min-height: 170px;
    box-shadow: 0 14px 40px rgba(0,0,0,0.14);
}

.gold-name {
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 12px;
}

.gold-price {
    color: var(--gold);
    font-size: 31px;
    font-weight: 900;
    line-height: 1.15;
    user-select: none;
}

.gold-sub {
    color: #b7b7b7;
    font-size: 13px;
    margin-top: 10px;
}

.price-box {
    font-size: 58px;
    color: var(--gold);
    font-weight: 900;
    text-align: center;
    background: linear-gradient(180deg, #0d0d0d 0%, #050505 100%);
    padding: 36px 20px;
    border-radius: 24px;
    border: 2px solid var(--gold);
    box-shadow: 0 16px 45px rgba(0,0,0,0.18);
    user-select: none;
    margin-top: 6px;
}

.info-box {
    background: #fcfaf4;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid var(--border);
    margin-top: 22px;
    font-size: 17px;
    line-height: 1.9;
    color: #2b2b2b;
}

.small-note {
    font-size: 14px;
    color: #666;
    text-align: center;
    margin-top: 18px;
    line-height: 1.6;
}

.footer-brand {
    text-align: center;
    margin-top: 34px;
    font-size: 14px;
    color: #999;
}

.sidebar-title {
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 8px;
}

.sidebar-note {
    font-size: 13px;
    color: #777;
    margin-bottom: 14px;
}

/* MOBİL UYUMLULUK */
@media screen and (max-width: 768px) {
    .logo-img {
        width: 145px;
        max-width: 145px;
    }

    .main-title {
        font-size: 34px;
    }

    .subtitle {
        font-size: 15px;
    }

    .gold-price {
        font-size: 25px;
    }

    .price-box {
        font-size: 38px;
    }
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# VARSAYILAN AYARLAR
# =====================================================

DEFAULT_CARPANLAR = {
    "24 Ayar Gram": 1.000,
    "22 Ayar Gram": 0.916,
    "14 Ayar Gram": 0.585,
    "Çeyrek Altın": 1.760,
    "Yarım Altın": 3.520,
    "Tam Altın": 7.040,
    "Ata Lira": 7.216,
    "Cumhuriyet Altını": 7.216
}

DEFAULT_MAGAZA_ORANLARI = {
    "14 Ayar Takı": 20.0,
    "22 Ayar Takı": 12.0,
    "24 Ayar Gram": 5.0
}


# =====================================================
# SESSION STATE
# =====================================================

if "carpanlar" not in st.session_state:
    st.session_state.carpanlar = DEFAULT_CARPANLAR.copy()

if "magaza_oranlari" not in st.session_state:
    st.session_state.magaza_oranlari = DEFAULT_MAGAZA_ORANLARI.copy()


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
    with st.sidebar:
        st.markdown("<div class='sidebar-title'>🔐 Yönetici Paneli</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-note'>Çarpanları ve mağaza oranlarını sadece siz yönetin.</div>", unsafe_allow_html=True)

        admin_sifre = st.text_input("Yönetici Şifresi", type="password")

        DOGRU_SIFRE = "1234"

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

            st.markdown("### Takı Mağaza Oranları (%)")

            yeni_oranlar = {}
            for oran_adi, mevcut_oran in st.session_state.magaza_oranlari.items():
                yeni_oranlar[oran_adi] = st.number_input(
                    f"{oran_adi}",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(mevcut_oran),
                    step=1.0,
                    format="%.1f"
                )

            col_a, col_b = st.columns(2)

            with col_a:
                kaydet = st.form_submit_button("Fiyatları Güncelle", use_container_width=True)

            with col_b:
                varsayilan = st.form_submit_button("Varsayılanlara Dön", use_container_width=True)

        if kaydet:
            st.session_state.carpanlar = yeni_carpanlar.copy()
            st.session_state.magaza_oranlari = yeni_oranlar.copy()
            st.success("Çarpanlar güncellendi.")

        if varsayilan:
            st.session_state.carpanlar = DEFAULT_CARPANLAR.copy()
            st.session_state.magaza_oranlari = DEFAULT_MAGAZA_ORANLARI.copy()
            st.success("Varsayılan değerlere dönüldü.")


# =====================================================
# HEADER
# =====================================================

def header_olustur(kaynak, has_altin, cekilme_zamani):
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
        "<div class='subtitle'>Güncel has altın verisine göre anlık fiyat panosu ve takı fiyat hesaplama ekranı</div>",
        unsafe_allow_html=True
    )

    st.markdown(f"""
    <div class='top-badges'>
        <div class='badge-box'>📡 Veri Kaynağı: {kaynak}</div>
        <div class='badge-box'>🟡 Canlı Has Altın: {para_formatla(has_altin)}</div>
        <div class='badge-box'>🕒 Türkiye Saati: {cekilme_zamani}</div>
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

header_olustur(veri["kaynak"], has_altin, veri["cekilme_zamani"])

# =====================================================
# CANLI FİYAT PANOSU
# =====================================================

st.markdown("<div class='section-title'>Canlı Altın Fiyat Panosu</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>24 Ayar Gram</div>
        <div class='gold-price'>{para_formatla(fiyatlar["24 Ayar Gram"])}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>22 Ayar Gram</div>
        <div class='gold-price'>{para_formatla(fiyatlar["22 Ayar Gram"])}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>14 Ayar Gram</div>
        <div class='gold-price'>{para_formatla(fiyatlar["14 Ayar Gram"])}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Çeyrek Altın</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Çeyrek Altın"])}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Yarım Altın</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Yarım Altın"])}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Tam Altın</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Tam Altın"])}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)

with col7:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Ata Lira</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Ata Lira"])}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)

with col8:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Cumhuriyet Altını</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Cumhuriyet Altını"])}</div>
        <div class='gold-sub'>Anlık satış fiyatı</div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# TAKI FİYAT HESAPLAMA
# =====================================================

st.markdown("---")
st.markdown("<div class='section-title'>Takı Fiyat Hesaplama</div>", unsafe_allow_html=True)

hesap_col1, hesap_col2 = st.columns(2)

with hesap_col1:
    ayar_secimi = st.selectbox(
        "Altın Türü",
        ["14 Ayar Takı", "22 Ayar Takı", "24 Ayar Gram"]
    )

with hesap_col2:
    urun_gram = st.number_input(
        "Ürün Gramı",
        min_value=0.10,
        value=1.00,
        step=0.10,
        format="%.2f"
    )

if ayar_secimi == "14 Ayar Takı":
    baz_fiyat = fiyatlar["14 Ayar Gram"]
    magaza_orani = st.session_state.magaza_oranlari["14 Ayar Takı"]
elif ayar_secimi == "22 Ayar Takı":
    baz_fiyat = fiyatlar["22 Ayar Gram"]
    magaza_orani = st.session_state.magaza_oranlari["22 Ayar Takı"]
else:
    baz_fiyat = fiyatlar["24 Ayar Gram"]
    magaza_orani = st.session_state.magaza_oranlari["24 Ayar Gram"]

hesaplanan_fiyat = (urun_gram * baz_fiyat) * (1 + (magaza_orani / 100))

st.markdown(
    f"<div class='price-box'>{para_formatla(hesaplanan_fiyat)}</div>",
    unsafe_allow_html=True
)

st.markdown(f"""
<div class='info-box'>
    <b>Seçilen Tür:</b> {ayar_secimi}<br>
    <b>Ürün Gramı:</b> {urun_gram:.2f} gr<br>
    <b>Baz Fiyat:</b> {para_formatla(baz_fiyat)}<br>
    <b>Canlı Has Altın:</b> {para_formatla(has_altin)}<br>
    <b>Türkiye Saati:</b> {veri["cekilme_zamani"]}
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<div class='small-note'>Bu ekran bilgilendirme amaçlıdır. Nihai fiyat ürün modeli, işçilik, ayar, gram ve mağaza onayına göre netleşir.</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='footer-brand'>ENES PULAT Kuyumculuk</div>",
    unsafe_allow_html=True
)