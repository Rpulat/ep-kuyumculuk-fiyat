import streamlit as st
import requests
from datetime import datetime

# =========================
# SAYFA AYARLARI
# =========================

st.set_page_config(
    page_title="EP Kuyumculuk Altın Fiyat Hesaplama",
    page_icon="💎",
    layout="centered"
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
    margin-bottom: 30px;
    text-align: center;
}

.subtitle {
    font-size: 18px;
    color: #666;
    text-align: center;
    margin-top: -15px;
    margin-bottom: 35px;
}

.price-box { 
    font-size: 60px; 
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
# FİYAT FORMAT TEMİZLEME
# =========================

def temizle_ve_cevir(fiyat):
    """
    Fiyat formatlarını sayıya çevirir.
    Örnek:
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


def recursive_find_price(data, possible_keys):
    """
    API'den gelen JSON içinde gram altın satış fiyatını arar.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()

            if key_lower in possible_keys:
                if isinstance(value, dict):
                    for sell_key in ["Selling", "selling", "SATIS", "satis", "Satış", "satis_fiyat"]:
                        if sell_key in value:
                            return temizle_ve_cevir(value[sell_key])
                else:
                    return temizle_ve_cevir(value)

        for value in data.values():
            result = recursive_find_price(value, possible_keys)
            if result:
                return result

    elif isinstance(data, list):
        for item in data:
            result = recursive_find_price(item, possible_keys)
            if result:
                return result

    return None


# =========================
# CANLI FİYAT VERİSİ
# =========================

@st.cache_data(ttl=60)
def fiyat_al():
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
            "ad": "Truncgil eski",
            "url": "https://finans.truncgil.com/today.json"
        },
        {
            "ad": "GenelPara yeni",
            "url": "https://api.genelpara.com/json/?list=altin&sembol=GA"
        },
        {
            "ad": "GenelPara eski",
            "url": "https://api.genelpara.com/embed/altin.json"
        }
    ]

    possible_keys = {
        "gram-altin",
        "gram has altin",
        "gram-has-altin",
        "gram altın",
        "gram altin",
        "ga",
        "gram"
    }

    son_hatalar = []

    for kaynak in kaynaklar:
        try:
            response = requests.get(kaynak["url"], headers=headers, timeout=8)

            if response.status_code != 200:
                son_hatalar.append(f"{kaynak['ad']}: HTTP {response.status_code}")
                continue

            data = response.json()
            fiyat = recursive_find_price(data, possible_keys)

            if fiyat and fiyat > 0:
                return {
                    "fiyat": fiyat,
                    "kaynak": kaynak["ad"],
                    "hata": None
                }

            son_hatalar.append(f"{kaynak['ad']}: fiyat bulunamadı")

        except Exception as e:
            son_hatalar.append(f"{kaynak['ad']}: {str(e)}")

    return {
        "fiyat": None,
        "kaynak": None,
        "hata": son_hatalar
    }


# =========================
# ARAYÜZ
# =========================

st.markdown(
    "<div class='main-title'>💎 EP Kuyumculuk<br>Güncel Altın Fiyat Hesaplama</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitle'>Ürün gramını girerek yaklaşık satış fiyatını öğrenebilirsiniz.</div>",
    unsafe_allow_html=True
)

sonuc = fiyat_al()
gram_altin = sonuc["fiyat"]

if gram_altin:

    urun_gram = st.number_input(
        "Ürün Gramı",
        min_value=0.10,
        value=1.00,
        step=0.10,
        format="%.2f"
    )

    # Müşteriye gösterilmeyen mağaza oranı
    # Bunu daha sonra istersen 8, 10, 12, 15 gibi değiştirebiliriz.
    magaza_orani = 10.0

    hesaplanan_fiyat = (urun_gram * gram_altin) * (1 + (magaza_orani / 100))

    st.markdown("---")

    st.markdown(
        f"<div class='price-box'>{hesaplanan_fiyat:,.2f} TL</div>",
        unsafe_allow_html=True
    )

    st.markdown(f"""
    <div class='info-box'>
        <b>Ürün Gramı:</b> {urun_gram:.2f} gr<br>
        <b>Güncel Gram Altın:</b> {gram_altin:,.2f} TL<br>
        <b>Son Güncelleme:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "<div class='small-note'>Bu ekran bilgilendirme amaçlıdır. Nihai fiyat ürün modeli, işçilik ve mağaza onayına göre netleşir.</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='footer-brand'>EP Kuyumculuk</div>",
        unsafe_allow_html=True
    )

else:
    st.error("Piyasa verilerine ulaşılamıyor. Lütfen birkaç dakika sonra tekrar deneyiniz.")

    with st.expander("Teknik hata detayları"):
        st.write(sonuc["hata"])