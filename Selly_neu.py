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
    .st-emotion-cache-yn7mcw {display: none;}
    .st-emotion-cache-1wmy9hl {display: none;}
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

if tentary_id_from_url and not st.session_state.tentary_loaded:
    cursor.execute("SELECT affiliate_link, affiliate_link_bundle FROM selly_users WHERE tentary_id = %s", (tentary_id_from_url,))
    result = cursor.fetchone()
    if result:
        st.session_state["tentary_id"] = tentary_id_from_url
        st.session_state["affiliate_link"] = result[0]
        st.session_state["affiliate_link_bundle"] = result[1] or "https://sarahtemmel.tentary.com/p/e1I0e5"
        st.session_state.tentary_loaded = True

if "tentary_id" not in st.session_state:
    st.session_state["tentary_id"] = "Sarah"
if "affiliate_link" not in st.session_state:
    st.session_state["affiliate_link"] = "https://sarahtemmel.tentary.com/p/q9fupC"
if "affiliate_link_bundle" not in st.session_state:
    st.session_state["affiliate_link_bundle"] = "https://sarahtemmel.tentary.com/p/e1I0e5"

auftraggeber = st.session_state["tentary_id"]
affiliate_link = st.session_state["affiliate_link"]
affiliate_link_bundle = st.session_state["affiliate_link_bundle"]

# --- Sidebar ---
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

            cursor.execute("""
                SELECT product_1_name, product_2_name, product_3_name, product_4_name, product_5_name
                FROM selly_users WHERE email = %s
            """, (login_email,))
            products = cursor.fetchone()

            if products and all(products):
                cursor.execute("""
                    UPDATE selly_users SET instagram_automation = TRUE WHERE email = %s
                """, (login_email,))
                conn.commit()
                st.session_state.instagram_automation = True

            st.success("✅ Zugang bestätigt! Selly verkauft ab jetzt mit deinem Link.")
            if result[1]:
                st.markdown(f"🔗 **Dein persönlicher Selly-Link:** [Jetzt teilen](https://selly-bot.onrender.com?a={result[1]})")
                st.markdown(f"🌝 **Selly ist im Auftrag von `{result[1]}` aktiv.**")
        else:
            st.error("❌ Keine Berechtigung – bitte nur für Käufer.")

    st.markdown("---")
    st.markdown("📄 [Impressum](https://sarahtemmel.tentary.com/legal/207493326/contact)  \n🔐 [Datenschutz](https://sarahtemmel.tentary.com/legal/207493326/privacy)  \n✨ <sub>Powered by Selly – The Empire</sub>", unsafe_allow_html=True)

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

    if st.session_state.authenticated:
        st.sidebar.markdown("""### 📋 Meine Produkte bearbeiten  
<sub>👉 Hinweis: Deine hier gespeicherten Produkte werden von Selly automatisch im Gespräch berücksichtigt, wenn es für den Interessenten sinnvoll ist. Selly bringt sie als charmante, smarte Empfehlung ein, niemals plump.</sub>""", unsafe_allow_html=True)
        with st.sidebar.form("produkte_form"):
            p1_name = st.text_input("Produkt 1 Name")
            p1_desc = st.text_area("Produkt 1 Beschreibung")
            p1_link = st.text_input("Produkt 1 Link")

            p2_name = st.text_input("Produkt 2 Name")
            p2_desc = st.text_area("Produkt 2 Beschreibung")
            p2_link = st.text_input("Produkt 2 Link")

            p3_name = st.text_input("Produkt 3 Name")
            p3_desc = st.text_area("Produkt 3 Beschreibung")
            p3_link = st.text_input("Produkt 3 Link")

            p4_name = st.text_input("Produkt 4 Name")
            p4_desc = st.text_area("Produkt 4 Beschreibung")
            p4_link = st.text_input("Produkt 4 Link")

            p5_name = st.text_input("Produkt 5 Name")
            p5_desc = st.text_area("Produkt 5 Beschreibung")
            p5_link = st.text_input("Produkt 5 Link")

            submit_button = st.form_submit_button("💾 Speichern")

            if submit_button:
                cursor.execute("""
                    UPDATE selly_users SET
                        product_1_name = %s,
                        product_1_desc = %s,
                        product_1_link = %s,
                        product_2_name = %s,
                        product_2_desc = %s,
                        product_2_link = %s,
                        product_3_name = %s,
                        product_3_desc = %s,
                        product_3_link = %s,
                        product_4_name = %s,
                        product_4_desc = %s,
                        product_4_link = %s,
                        product_5_name = %s,
                        product_5_desc = %s,
                        product_5_link = %s
                    WHERE email = %s
                """, (
                    p1_name, p1_desc, p1_link,
                    p2_name, p2_desc, p2_link,
                    p3_name, p3_desc, p3_link,
                    p4_name, p4_desc, p4_link,
                    p5_name, p5_desc, p5_link,
                    st.session_state.user_email
                ))
                conn.commit()
                st.sidebar.success("✅ Produkte erfolgreich gespeichert!")
