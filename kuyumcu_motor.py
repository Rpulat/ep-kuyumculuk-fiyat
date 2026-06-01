import streamlit as st
import requests
from datetime import datetime

# =====================================================
# SAYFA AYARLARI
# =====================================================

st.set_page_config(
    page_title="EP Kuyumculuk Canlı Altın Fiyatları",
    page_icon="💎",
    layout="wide"
)

# =====================================================
# TASARIM
# =====================================================

st.markdown("""
<style>
.main-title {
    font-size: 48px;
    font-weight: 900;
    color: #2c2c35;
    line-height: 1.2;
    margin-bottom: 10px;
    text-align: center;
}

.subtitle {
    font-size: 18px;
    color: #666;
    text-align: center;
    margin-bottom: 35px;
}

.section-title {
    font-size: 30px;
    font-weight: 900;
    color: #2c2c35;
    margin-top: 25px;
    margin-bottom: 20px;
}

.gold-card {
    background: #050505;
    border: 2px solid #D4AF37;
    border-radius: 20px;
    padding: 26px 16px;
    text-align: center;
    box-shadow: 0 14px 38px rgba(0,0,0,0.16);
    min-height: 160px;
}

.gold-name {
    color: #ffffff;
    font-size: 21px;
    font-weight: 800;
    margin-bottom: 14px;
}

.gold-price {
    color: #D4AF37;
    font-size: 31px;
    font-weight: 900;
    user-select: none;
}

.gold-sub {
    color: #aaa;
    font-size: 13px;
    margin-top: 8px;
}

.price-box { 
    font-size: 58px; 
    color: #D4AF37; 
    font-weight: 900; 
    text-align: center; 
    background: #050505; 
    padding: 35px 20px; 
    border-radius: 22px; 
    border: 2px solid #D4AF37;
    box-shadow: 0 16px 45px rgba(0,0,0,0.18);
    user-select: none;
}

.info-box {
    background: #faf7ef;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #ead9a7;
    margin-top: 22px;
    font-size: 17px;
    line-height: 1.8;
}

.small-note {
    font-size: 14px;
    color: #666;
    text-align: center;
    margin-top: 18px;
    line-height: 1.5;
}

.footer-brand {
    text-align: center;
    margin-top: 35px;
    font-size: 14px;
    color: #999;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# VARSAYILAN ÇARPANLAR
# =====================================================
# Buradaki değerler ilk açılışta kullanılır.
# Yönetici panelinden geçici olarak değiştirilebilir.

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

# Ürün hesaplama tarafındaki mağaza oranları
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

    return float(fiyat)


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
                            try:
                                return temizle_ve_cevir(value[sell_key])
                            except:
                                pass

                    for possible_value in value.values():
                        try:
                            fiyat = temizle_ve_cevir(possible_value)
                            if fiyat and fiyat > 0:
                                return fiyat
                        except:
                            pass
                else:
                    try:
                        return temizle_ve_cevir(value)
                    except:
                        pass

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
        {
            "ad": "Truncgil v4",
            "url": "https://finans.truncgil.com/v4/today.json"
        },
        {
            "ad": "Truncgil v3",
            "url": "https://finans.truncgil.com/v3/today.json"
        },
        {
            "ad": "Truncgil eski",
            "url": "https://finans.truncgil.com/today.json"
        },
        {
            "ad": "GenelPara eski",
            "url": "https://api.genelpara.com/embed/altin.json"
        }
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
                    "hata": None
                }

            son_hatalar.append(f"{kaynak['ad']}: has altın bulunamadı")

        except Exception as e:
            son_hatalar.append(f"{kaynak['ad']}: {str(e)}")

    return {
        "basarili": False,
        "kaynak": None,
        "has_altin": None,
        "hata": son_hatalar
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
    st.sidebar.markdown("## 🔐 Yönetici Paneli")

    admin_sifre = st.sidebar.text_input(
        "Yönetici Şifresi",
        type="password"
    )

    # İstersen bu şifreyi değiştirebilirsin.
    # Daha profesyonel sürümde Streamlit Secrets içine alacağız.
    DOGRU_SIFRE = "1234"

    if admin_sifre != DOGRU_SIFRE:
        st.sidebar.info("Çarpanları değiştirmek için şifre giriniz.")
        return

    st.sidebar.success("Yönetici girişi aktif")

    st.sidebar.markdown("### Has Çarpanları")

    yeni_carpanlar = {}

    for urun_adi, mevcut_carpan in st.session_state.carpanlar.items():
        yeni_carpanlar[urun_adi] = st.sidebar.number_input(
            f"{urun_adi}",
            min_value=0.000,
            max_value=20.000,
            value=float(mevcut_carpan),
            step=0.001,
            format="%.3f"
        )

    st.sidebar.markdown("### Takı Mağaza Oranları (%)")

    yeni_oranlar = {}

    for oran_adi, mevcut_oran in st.session_state.magaza_oranlari.items():
        yeni_oranlar[oran_adi] = st.sidebar.number_input(
            f"{oran_adi}",
            min_value=0.0,
            max_value=100.0,
            value=float(mevcut_oran),
            step=1.0,
            format="%.1f"
        )

    if st.sidebar.button("Fiyatları Güncelle"):
        st.session_state.carpanlar = yeni_carpanlar.copy()
        st.session_state.magaza_oranlari = yeni_oranlar.copy()
        st.sidebar.success("Çarpanlar güncellendi.")

    if st.sidebar.button("Varsayılan Değerlere Dön"):
        st.session_state.carpanlar = DEFAULT_CARPANLAR.copy()
        st.session_state.magaza_oranlari = DEFAULT_MAGAZA_ORANLARI.copy()
        st.sidebar.success("Varsayılan değerlere dönüldü.")


# =====================================================
# ARAYÜZ BAŞLANGICI
# =====================================================

yonetici_paneli()

st.markdown(
    "<div class='main-title'>💎 EP Kuyumculuk<br>Canlı Altın Fiyatları</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitle'>Güncel has altın fiyatına göre oluşturulan EP Kuyumculuk fiyat ekranı.</div>",
    unsafe_allow_html=True
)

veri = has_altin_al()

if not veri["basarili"]:
    st.error("Piyasa verilerine ulaşılamıyor. Lütfen birkaç dakika sonra tekrar deneyiniz.")

    with st.expander("Teknik hata detayları"):
        st.write(veri["hata"])

    st.stop()


has_altin = veri["has_altin"]
fiyatlar = fiyatlari_olustur(has_altin)

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
        <div class='gold-sub'>Çarpan: {st.session_state.carpanlar["24 Ayar Gram"]:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>22 Ayar Gram</div>
        <div class='gold-price'>{para_formatla(fiyatlar["22 Ayar Gram"])}</div>
        <div class='gold-sub'>Çarpan: {st.session_state.carpanlar["22 Ayar Gram"]:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>14 Ayar Gram</div>
        <div class='gold-price'>{para_formatla(fiyatlar["14 Ayar Gram"])}</div>
        <div class='gold-sub'>Çarpan: {st.session_state.carpanlar["14 Ayar Gram"]:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Çeyrek Altın</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Çeyrek Altın"])}</div>
        <div class='gold-sub'>Çarpan: {st.session_state.carpanlar["Çeyrek Altın"]:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Yarım Altın</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Yarım Altın"])}</div>
        <div class='gold-sub'>Çarpan: {st.session_state.carpanlar["Yarım Altın"]:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Tam Altın</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Tam Altın"])}</div>
        <div class='gold-sub'>Çarpan: {st.session_state.carpanlar["Tam Altın"]:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

with col7:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Ata Lira</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Ata Lira"])}</div>
        <div class='gold-sub'>Çarpan: {st.session_state.carpanlar["Ata Lira"]:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

with col8:
    st.markdown(f"""
    <div class='gold-card'>
        <div class='gold-name'>Cumhuriyet Altını</div>
        <div class='gold-price'>{para_formatla(fiyatlar["Cumhuriyet Altını"])}</div>
        <div class='gold-sub'>Çarpan: {st.session_state.carpanlar["Cumhuriyet Altını"]:.3f}</div>
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
        "Altın Ayarı",
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
    <b>Canlı Has Altın:</b> {para_formatla(has_altin)}<br>
    <b>Seçilen Ürün:</b> {ayar_secimi}<br>
    <b>Ürün Gramı:</b> {urun_gram:.2f} gr<br>
    <b>Veri Kaynağı:</b> {veri["kaynak"]}<br>
    <b>Son Güncelleme:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<div class='small-note'>Bu ekran bilgilendirme amaçlıdır. Nihai fiyat ürün modeli, işçilik, ayar, gram ve mağaza onayına göre netleşir.</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='footer-brand'>EP Kuyumculuk</div>",
    unsafe_allow_html=True
)