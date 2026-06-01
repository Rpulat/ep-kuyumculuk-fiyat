import streamlit as st
import requests

# Sayfa Yapılandırması
st.set_page_config(page_title="EP Kuyumculuk Satış Ekranı", layout="centered")

st.markdown("""
    <style>
    .big-price { font-size: 60px; color: #D4AF37; font-weight: bold; text-align: center; background: #000; padding: 20px; border-radius: 10px; border: 2px solid #D4AF37; }
    </style>
""", unsafe_allow_html=True)


# Stabil Veri Motoru (Özel API Anahtarı İle)
@st.cache_data(ttl=60)
def fiyat_al():
    try:
        # Senin özel altin.in API anahtarın doğrudan URL'ye eklendi.
        # Bu sayede Streamlit Cloud (Bulut) sunucuları engellemeye takılmayacak.
        url = "https://api.altin.in/api/current?key=hapi_749b7fd0f03041ce93fe1855ecd9c5d7"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.json()

        # Eğer yine hata olursa, hatanın tam sebebini (Örn: 403, 429 gibi) ekrana yazdıracak
        st.error(f"Sunucu Reddetme Kodu: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Sistem Hatası: {e}")
        return None


st.title("💎 EP Kuyumculuk - Canlı Satış Ekranı")

data = fiyat_al()

if data and 'gram_altin' in data:
    gram_altin = float(data['gram_altin']['satis'])

    col1, col2 = st.columns(2)
    with col1:
        urun_gram = st.number_input("Ürün Gramı:", min_value=0.1, value=5.0, step=0.1)
    with col2:
        isci_kar = st.slider("İşçilik/Kâr Oranı (%):", 0, 50, 10)

    net_fiyat = (urun_gram * gram_altin) * (1 + (isci_kar / 100))

    st.markdown("---")
    st.markdown(f"<div class='big-price'>{net_fiyat:,.2f} TL</div>", unsafe_allow_html=True)
    st.write(f"Güncel Gram Altın: {gram_altin} TL")
else:
    st.warning("Veri çekilemiyor. API anahtarının süresi dolmuş veya günlük kullanım limiti aşılmış olabilir.")