import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="EP Kuyumculuk Satış Ekranı",
    page_icon="💎",
    layout="centered"
)

st.markdown("""
<style>
.main-title {
    font-size: 44px;
    font-weight: 800;
    color: #2c2c35;
    line-height: 1.2;
    margin-bottom: 25px;
}
.price-box { 
    font-size: 56px; 
    color: #D4AF37; 
    font-weight: 900; 
    text-align: center; 
    background: #050505; 
    padding: 28px; 
    border-radius: 18px; 
    border: 2px solid #D4AF37;
    box-shadow: 0 12px 35px rgba(0,0,0,0.18);
}
.info-box {
    background: #faf7ef;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #ead9a7;
    margin-top: 18px;
}
.small-note {
    font-size: 13px;
    color: #666;
    text-align: center;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)


def temizle_ve_cevir(fiyat):
    """
    6.750,50 / 6750.50 / 6,750.50 / 6750 gibi formatları float'a çevirir.
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
    JSON içinde farklı isimlerle gelebilecek gram altın satış fiyatını arar.
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
            r = requests.get(kaynak["url"], headers=headers, timeout=8)

            if r.status_code != 200:
                son_hatalar.append(f"{kaynak['ad']}: HTTP {r.status_code}")
                continue

            data = r.json()

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


st.markdown("<div class='main-title'>💎 EP Kuyumculuk<br>Canlı Satış Ekranı</div>", unsafe_allow_html=True)

sonuc = fiyat_al()
gram_altin = sonuc["fiyat"]

if gram_altin:
    col1, col2 = st.columns(2)

    with col1:
        urun_gram = st.number_input(
            "Ürün Gramı",
            min_value=0.10,
            value=5.00,
            step=0.10,
            format="%.2f"
        )

    with col2:
        isci_kar = st.number_input(
            "İşçilik / Kâr Oranı (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0
        )

    net_fiyat = (urun_gram * gram_altin) * (1 + (isci_kar / 100))

    st.markdown("---")

    st.markdown(
        f"<div class='price-box'>{net_fiyat:,.2f} TL</div>",
        unsafe_allow_html=True
    )

    st.markdown(f"""
    <div class='info-box'>
        <b>Ürün Gramı:</b> {urun_gram:.2f} gr<br>
        <b>Güncel Gram Altın:</b> {gram_altin:,.2f} TL<br>
        <b>Veri Kaynağı:</b> {sonuc["kaynak"]}<br>
        <b>Son Güncelleme:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "<div class='small-note'>Fiyatlar piyasa değişimlerine göre güncellenir. Nihai satış fiyatı mağaza onayına tabidir.</div>",
        unsafe_allow_html=True
    )

else:
    st.error("Piyasa verilerine ulaşılamıyor. Lütfen birkaç dakika sonra tekrar deneyiniz.")

    with st.expander("Teknik hata detayları"):
        st.write(sonuc["hata"])