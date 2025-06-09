import streamlit as st
import openai
from openai import OpenAI
import psycopg2
import re
import os
import subprocess
import sys

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Selly – deine KI Selling Queen", page_icon="👑", layout="centered")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-yn7mcw {display: none;} /* Warning Box ausblenden */
    .st-emotion-cache-1wmy9hl {display: none;} /* fallback class bei neuen Streamlit Builds */
    </style>
    """, unsafe_allow_html=True)

# --- PostgreSQL-Verbindung ---
def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD")
    )

conn = get_connection()
cursor = conn.cursor()

# --- Session States ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tentary_loaded" not in st.session_state:
    st.session_state.tentary_loaded = False

# --- URL-Parameter auslesen ---
query_params = st.experimental_get_query_params()
tentary_id_from_url = query_params.get("a", [None])[0]

# Wenn Tentary-ID in URL → in Session speichern
if tentary_id_from_url and not st.session_state.tentary_loaded:
    cursor.execute("SELECT affiliate_link, affiliate_link_bundle FROM selly_users WHERE tentary_id = %s", (tentary_id_from_url,))
    result = cursor.fetchone()
    if result:
        st.session_state["tentary_id"] = tentary_id_from_url
        st.session_state["affiliate_link"] = result[0]
        st.session_state["affiliate_link_bundle"] = result[1] or "https://sarahtemmel.tentary.com/p/e1I0e5"
        st.session_state.tentary_loaded = True

# Session fallback setzen, falls nichts geladen wurde
if "tentary_id" not in st.session_state:
    st.session_state["tentary_id"] = "Sarah"
if "affiliate_link" not in st.session_state:
    st.session_state["affiliate_link"] = "https://sarahtemmel.tentary.com/p/q9fupC"
if "affiliate_link_bundle" not in st.session_state:
    st.session_state["affiliate_link_bundle"] = "https://sarahtemmel.tentary.com/p/e1I0e5"

auftraggeber = st.session_state["tentary_id"]
affiliate_link = st.session_state["affiliate_link"]
affiliate_link_bundle = st.session_state["affiliate_link_bundle"]

# --- Sidebar Login ---
with st.sidebar:
    st.markdown("### 🔐 Login für Käufer")
    login_email = st.text_input("Deine Käufer-E-Mail:")
    if st.button("Login"):
        cursor.execute("SELECT affiliate_link, tentary_id, affiliate_link_bundle, instagram_automation FROM selly_users WHERE email = %s", (login_email,))
        result = cursor.fetchone()
        if result:
            st.session_state.authenticated = True
            st.session_state.user_email = login_email
            st.session_state.affiliate_link = result[0]
            st.session_state.tentary_id = result[1]
            st.session_state.affiliate_link_bundle = result[2] or "https://sarahtemmel.tentary.com/p/e1I0e5"
            st.session_state.instagram_automation = result[3]
            st.session_state.tentary_loaded = True
            st.success("✅ Zugang bestätigt! Selly verkauft ab jetzt mit deinem Link.")
            if result[1]:
                st.markdown(f"🔗 **Dein persönlicher Selly-Link:** [Jetzt teilen](https://selly-bot.onrender.com?a={result[1]})")
                st.markdown(f"🐝 **Selly ist im Auftrag von `{result[1]}` aktiv.**")
        else:
            st.error("❌ Keine Berechtigung – bitte nur für Käufer.")

    st.markdown("---")
    st.markdown("📄 [Impressum](https://deine-domain.com/impressum)  \n🔐 [Datenschutz](https://deine-domain.com/datenschutz)", unsafe_allow_html=True)

    # --- Premium Bereich: Instagram Automation & Booster ---
    if st.session_state.authenticated and st.session_state.get("instagram_automation", False):
        st.sidebar.success("✅ Premium aktiviert")
        st.sidebar.markdown("### 🚀 Instagram Automation & Reichweiten-Booster")

        insta_mode = st.sidebar.radio("Welche Funktion willst du aktivieren?", ["📩 DM-Automation", "📢 Reichweite aufbauen"])

        if insta_mode == "📩 DM-Automation":
            st.sidebar.markdown("**Trigger auswählen:**")
            trigger = st.sidebar.selectbox("Wann soll eine Nachricht gesendet werden?", [
                "Keyword in Kommentar", "Kommentar unter Beitrag", "Neue Nachricht", "Keyword in Nachricht"
            ])
            nachricht = st.sidebar.text_area("Nachricht, die gesendet werden soll")
            beitrags_id = st.sidebar.text_input("Beitrags-ID oder Link (wenn nötig)")
            st.sidebar.button("⚙️ Automatisierung speichern")

        if insta_mode == "📢 Reichweite aufbauen":
            zielgruppe = st.sidebar.radio("Zielgruppe:", ["Eigene Follower", "Follower von Nutzer", "Hashtag-Suche"])
            zielwert = st.sidebar.text_input("Benutzername oder Hashtag (ohne @/#)")
            likes = st.sidebar.selectbox("Anzahl Likes pro Tag", [50, 100, 200])
            follows = st.sidebar.selectbox("Anzahl Follows pro Tag", [10, 20, 50])
            comments = st.sidebar.selectbox("Anzahl Kommentare pro Tag", [5, 10, 20])

            if st.sidebar.button("🚀 Booster starten"):
                username = zielwert if zielgruppe == "Follower von Nutzer" else "default"
                subprocess.Popen([sys.executable, "headless_bot.py", username])
                st.sidebar.success("✅ Booster gestartet! Instagram Automation läuft jetzt im Hintergrund.")

# --- Begrüßungstitel anzeigen ---
st.image("https://i.postimg.cc/CMr2Tbpj/Chat-GPT-Image-8-Juni-2025-21-23-19.png", width=250)
st.title("👑 Selly – deine KI Selling Queen")

# --- Rest bleibt unverändert (dein bestehender Chat Block bleibt wie im Ursprungs-Code)
