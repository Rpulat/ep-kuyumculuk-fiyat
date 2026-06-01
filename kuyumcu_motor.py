import streamlit as st
import requests
from datetime import datetime

# =========================
# SAYFA AYARLARI
# =========================

st.set_page_config(
    page_title="ENES PULAT Kuyumculuk Canlı Altın Fiyatları",
    page_icon="💎",
    layout="wide"
)

# =========================
# TASARIM
# =========================

st.markdown("""
<style>
.main-title {
    font-size: 46px;
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
    font-size: 28px;
    font-weight: 800;
    color: #2c2c35;
    margin-top: 25px;
    margin-bottom: 18px;
}

.gold-card {
    background: #050505;
    border: 2px solid #D4AF37;
    border-radius: 18px;
    padding: 24px 18px;
    text-align: center;
    box-shadow: 0 12px 35px rgba(0,0,0,0.15);
    min-height: 155px;
}

.gold-name {
    color: #ffffff;
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 14px;
}

.gold-price {
    color: #D4AF37;
    font-size: 30px;
    font-weight: 900;
    user-select: none;
}

.gold-sub {
    color: #aaa;
    font-size: 13px;
    margin-top: 8px;
}

.price-box { 
    font-size: 56px; 
    color: #D4AF37; 
    font-weight: 900; 
    text-align: center; 
    background: #050505; 
    padding: 35px 20px; 
    border-radius: 20px; 
    border: 2px solid #D4AF37;
    box-shadow: 0 16px 45px rgba(0,0,0,0.18);
    user-select: none;
}

.info-box {
    background: #faf7ef;
    padding: 20px;
    border-radius: 14px;
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


# =========================
# YARDIMCI FONKSİYONLAR
# =========================

def temizle_ve_cevir(fiyat):
    """
    Fiyat formatlarını sayıya çevirir.
    6.647,92 -> 6647.92
    6647.92 -> 6647.92
    6,647.92 -> 6647.92
    """
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
    """
    JSON verisi içinde isme göre fiyat arar.
    Örneğin: gram altın, çeyrek altın, yarım altın, tam altın.
    """
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


# =========================
# CANLI VERİ MOTORU
# =========================

@st.cache_data(ttl=60)
def altin_verilerini_al():
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
                or veri_icinden_fiyat_bul(data, ["ga"])
            )

            ceyrek_altin = veri_icinden_fiyat_bul(data, ["ceyrek"])
            yarim_altin = veri_icinden_fiyat_bul(data, ["yarim"])
            tam_altin = veri_icinden_fiyat_bul(data, ["tam", "altin"])
            ata_lira = veri_icinden_fiyat_bul(data, ["ata"])
            cumhuriyet_altini = veri_icinden_fiyat_bul(data, ["cumhuriyet"])

            if gram_altin and gram_altin > 0:
                return {
                    "basarili": True,
                    "kaynak": kaynak["ad"],
                    "gram_altin": gram_altin,
                    "24_ayar_gram": gram_altin,
                    "22_ayar_gram": gram_altin * 0.916,
                    "14_ayar_gram": gram_altin * 0.585,
                    "ceyrek_altin": ceyrek_altin,
                    "yarim_altin": yarim_altin,
                    "tam_altin": tam_altin,
                    "ata_lira": ata_lira,
                    "cumhuriyet_altini": cumhuriyet_altini,
                    "hata": None
                }

            son_hatalar.append(f"{kaynak['ad']}: gram altın bulunamadı")

        except Exception as e:
            son_hatalar.append(f"{kaynak['ad']}: {str(e)}")

    return {
        "basarili": False,
        "kaynak": None,
        "hata": son_hatalar
    }


# =========================
# ARAYÜZ
# =========================

st.markdown(
    "<div class='main-title'>💎 EP Kuyumculuk<br>Canlı Altın Fiyatları</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitle'>Güncel altın fiyatları ve yaklaşık takı fiyat hesaplama ekranı.</div>",
    unsafe_allow_html=True
)

veri = altin_verilerini_al()

if veri["basarili"]:

    st.markdown("<div class='section-title'>Canlı Altın Fiyatları</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class='gold-card'>
            <div class='gold-name'>24 Ayar Gram</div>
            <div class='gold-price'>{para_formatla(veri["24_ayar_gram"])}</div>
            <div class='gold-sub'>Gram altın satış</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='gold-card'>
            <div class='gold-name'>22 Ayar Gram</div>
            <div class='gold-price'>{para_formatla(veri["22_ayar_gram"])}</div>
            <div class='gold-sub'>Yaklaşık has değer</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='gold-card'>
            <div class='gold-name'>14 Ayar Gram</div>
            <div class='gold-price'>{para_formatla(veri["14_ayar_gram"])}</div>
            <div class='gold-sub'>Yaklaşık has değer</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class='gold-card'>
            <div class='gold-name'>Çeyrek Altın</div>
            <div class='gold-price'>{para_formatla(veri["ceyrek_altin"])}</div>
            <div class='gold-sub'>Piyasa satış</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.markdown(f"""
        <div class='gold-card'>
            <div class='gold-name'>Yarım Altın</div>
            <div class='gold-price'>{para_formatla(veri["yarim_altin"])}</div>
            <div class='gold-sub'>Piyasa satış</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown(f"""
        <div class='gold-card'>
            <div class='gold-name'>Tam Altın</div>
            <div class='gold-price'>{para_formatla(veri["tam_altin"])}</div>
            <div class='gold-sub'>Piyasa satış</div>
        </div>
        """, unsafe_allow_html=True)

    with col7:
        st.markdown(f"""
        <div class='gold-card'>
            <div class='gold-name'>Ata Lira</div>
            <div class='gold-price'>{para_formatla(veri["ata_lira"])}</div>
            <div class='gold-sub'>Piyasa satış</div>
        </div>
        """, unsafe_allow_html=True)

    with col8:
        st.markdown(f"""
        <div class='gold-card'>
            <div class='gold-name'>Cumhuriyet Altını</div>
            <div class='gold-price'>{para_formatla(veri["cumhuriyet_altini"])}</div>
            <div class='gold-sub'>Piyasa satış</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("<div class='section-title'>Takı Fiyat Hesaplama</div>", unsafe_allow_html=True)

    hesap_col1, hesap_col2 = st.columns(2)

    with hesap_col1:
        ayar_secimi = st.selectbox(
            "Altın Ayarı",
            ["14 Ayar", "22 Ayar", "24 Ayar"]
        )

    with hesap_col2:
        urun_gram = st.number_input(
            "Ürün Gramı",
            min_value=0.10,
            value=1.00,
            step=0.10,
            format="%.2f"
        )

    if ayar_secimi == "14 Ayar":
        baz_fiyat = veri["14_ayar_gram"]
        magaza_orani = 20.0
    elif ayar_secimi == "22 Ayar":
        baz_fiyat = veri["22_ayar_gram"]
        magaza_orani = 12.0
    else:
        baz_fiyat = veri["24_ayar_gram"]
        magaza_orani = 5.0

    hesaplanan_fiyat = (urun_gram * baz_fiyat) * (1 + (magaza_orani / 100))

    st.markdown(
        f"<div class='price-box'>{para_formatla(hesaplanan_fiyat)}</div>",
        unsafe_allow_html=True
    )

    st.markdown(f"""
    <div class='info-box'>
        <b>Seçilen Ayar:</b> {ayar_secimi}<br>
        <b>Ürün Gramı:</b> {urun_gram:.2f} gr<br>
        <b>Güncel Gram Altın:</b> {para_formatla(veri["gram_altin"])}<br>
        <b>Veri Kaynağı:</b> {veri["kaynak"]}<br>
        <b>Son Güncelleme:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}
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

else:
    st.error("Piyasa verilerine ulaşılamıyor. Lütfen birkaç dakika sonra tekrar deneyiniz.")

    with st.expander("Teknik hata detayları"):
        st.write(veri["hata"])