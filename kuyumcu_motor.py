import streamlit as st
import requests

# Sayfa Yapılandırması
st.set_page_config(page_title="Enes Pulat Kuyumculuk Satış Ekranı", layout="centered")

# Tasarım Stilleri (Altın Sarısı ve Siyah Premium Tema)
st.markdown("""
    <style>
    .big-price { 
        font-size: 80px; 
        color: #D4AF37; 
        font-weight: bold; 
        text-align: center; 
        background: #000; 
        padding: 30px; 
        border-radius: 15px; 
        border: 3px solid #D4AF37;
    }
    .stApp { background-color: #fcfcfc; }
    </style>
""", unsafe_allow_html=True)


# Veri Çekme Motoru (Stabil & Key Gerektirmez)
@st.cache_data(ttl=60)  # Veriyi 60 saniyede bir günceller, hızlı çalışır
def fiyat_al():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://api.doviz.com/api/v1/currencies/gram-altin/latest"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


# Arayüz
st.title("💎 EP Kuyumculuk - Canlı Satış Ekranı")

data = fiyat_al()

if data:
    # Veri İşleme
    gram_altin = float(data['selling'])

    # Kullanıcı Girişleri
    col1, col2 = st.columns(2)
    with col1:
        urun_gram = st.number_input("Ürün Gramı:", min_value=0.1, value=5.0, step=0.1)
    with col2:
        isci_kar = st.slider("İşçilik/Kâr Oranı (%):", 0, 50, 10)

    # Hesaplama
    net_fiyat = (urun_gram * gram_altin) * (1 + (isci_kar / 100))

    # Sonuç Gösterimi
    st.markdown("---")
    st.markdown("<p style='text-align:center;'>MÜŞTERİYE SUNULACAK FİYAT</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-price'>{net_fiyat:,.2f} TL</div>", unsafe_allow_html=True)

    st.write(f"Anlık Gram Altın Alış/Satış: {gram_altin} TL")
else:
    st.error("Bağlantı hatası: İnternet bağlantınızı kontrol edin.")