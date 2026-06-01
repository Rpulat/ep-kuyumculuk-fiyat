import streamlit as st
import requests

# 1. Sayfa Yapılandırması
st.set_page_config(page_title="EP Kuyumculuk Satış Ekranı", layout="centered")

st.markdown("""
    <style>
    .big-price { 
        font-size: 60px; 
        color: #D4AF37; 
        font-weight: bold; 
        text-align: center; 
        background: #000; 
        padding: 20px; 
        border-radius: 10px; 
        border: 2px solid #D4AF37; 
    }
    </style>
""", unsafe_allow_html=True)


# Gelen farklı formatlardaki verileri (Örn: 2.450,50) tek tip hesaplanabilir sayıya çevirir
def temizle_ve_cevir(fiyat_str):
    fiyat_str = str(fiyat_str)
    if "." in fiyat_str and "," in fiyat_str:
        fiyat_str = fiyat_str.replace(".", "").replace(",", ".")
    elif "," in fiyat_str:
        fiyat_str = fiyat_str.replace(",", ".")
    return float(fiyat_str)


# 2. Stabil ve Yedekli Veri Motoru
@st.cache_data(ttl=60)
def fiyat_al():
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 1. Kaynak: Truncgil Finans (Bulut sunucularından engellenmez, ücretsiz ve garantilidir)
    try:
        response = requests.get("https://finans.truncgil.com/today.json", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "gram-altin" in data:
                return temizle_ve_cevir(data["gram-altin"]["Selling"])
            elif "gram-has-altin" in data:
                return temizle_ve_cevir(data["gram-has-altin"]["Selling"])
    except:
        pass

    # 2. Kaynak: Genelpara (İlk kaynakta sorun olursa arka planda gizlice devreye girer)
    try:
        response = requests.get("https://api.genelpara.com/embed/altin.json", headers=headers, timeout=5)
        if response.status_code == 200:
            return temizle_ve_cevir(response.json()['GA']['satis'])
    except:
        pass

    return None


# 3. Arayüz Tasarımı
st.title("💎 EP Kuyumculuk - Canlı Satış Ekranı")

gram_altin = fiyat_al()

if gram_altin:
    col1, col2 = st.columns(2)
    with col1:
        urun_gram = st.number_input("Ürün Gramı:", min_value=0.1, value=5.0, step=0.1)
    with col2:
        isci_kar = st.slider("İşçilik/Kâr Oranı (%):", 0, 50, 10)

    # Hesaplama
    net_fiyat = (urun_gram * gram_altin) * (1 + (isci_kar / 100.0))

    # Müşteri Gösterimi
    st.markdown("---")
    st.markdown(f"<div class='big-price'>{net_fiyat:,.2f} TL</div>", unsafe_allow_html=True)
    st.write(f"Güncel Gram Altın (Piyasa): {gram_altin:,.2f} TL")
else:
    st.error("Piyasa verilerine ulaşılamıyor. Lütfen sayfayı yenileyiniz.")