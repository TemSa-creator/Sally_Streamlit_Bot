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
    .stAlert {display: none !important;}
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
if "product_entries" not in st.session_state:
    st.session_state.product_entries = 1

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
        cursor.execute("SELECT * FROM selly_users WHERE email = %s", (login_email,))
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            user_data = dict(zip(columns, result))

            st.session_state.authenticated = True
            st.session_state.user_email = login_email
            st.session_state.affiliate_link = user_data.get("affiliate_link")
            st.session_state.tentary_id = user_data.get("tentary_id")
            st.session_state.affiliate_link_bundle = user_data.get("affiliate_link_bundle") or "https://sarahtemmel.tentary.com/p/e1I0e5"
            st.session_state.instagram_automation = user_data.get("instagram_automation")
            st.session_state.user_products = user_data
            st.session_state.tentary_loaded = True

            st.success("✅ Zugang bestätigt! Selly verkauft ab jetzt mit deinem Link.")
            if user_data.get("tentary_id"):
                st.markdown(f"🔗 **Dein persönlicher Selly-Link:** [Jetzt teilen](https://selly-bot.onrender.com?a={user_data.get('tentary_id')})")
                st.markdown(f"🌝 **Selly ist im Auftrag von `{user_data.get('tentary_id')}` aktiv.**")
        else:
            st.error("❌ Keine Berechtigung – bitte nur für Käufer.")

    st.markdown("---")
    st.markdown("""
    📄 [Impressum](https://sarahtemmel.tentary.com/legal/207493326/contact)  
    🔐 [Datenschutz](https://sarahtemmel.tentary.com/legal/207493326/privacy)  
    ✨ <sub>Powered by Selly – The Empire</sub>
    """, unsafe_allow_html=True)

# --- Zusatzbereich: Instagram Automation ("Selly says") ---
if st.session_state.authenticated:
    st.sidebar.markdown("### 🧠 Selly says: Instagram Automatisierung")
    with st.sidebar.form("selly_says_form"):
        automation_trigger = st.text_input("Trigger (z. B. 'mehr infos')", st.session_state.user_products.get("instagram_trigger", ""))
        automation_message = st.text_area("Was soll Selly automatisch sagen, wenn der Trigger erkannt wird?", st.session_state.user_products.get("instagram_automation", ""))

        # Vorschau der Antwort
        if automation_trigger and automation_message:
            st.info(f"**Wenn jemand auf Instagram '{automation_trigger}' schreibt, sagt Selly:**\n\n{automation_message}")

        submit_automation = st.form_submit_button("🔖 Automation speichern")

        if submit_automation:
            cursor.execute("""
                UPDATE selly_users SET
                    instagram_automation = %s,
                    instagram_trigger = %s
                WHERE email = %s
            """, (automation_message, automation_trigger, st.session_state.user_email))
            conn.commit()
            st.sidebar.success("✅ Selly Automation erfolgreich gespeichert!")

    # --- Dynamische Produktauswahl ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Zusätzliche Produkte")

    if st.sidebar.button("+ Weiteres Produkt hinzufügen"):
        st.session_state.product_entries += 1

    with st.sidebar.form("dynamic_product_form"):
        for i in range(st.session_state.product_entries):
            st.markdown(f"#### Produkt {i + 1}")
            name = st.text_input(f"Produktname {i + 1}", key=f"pname_{i}")
            desc = st.text_area(f"Produktbeschreibung {i + 1}", key=f"pdesc_{i}")
            link = st.text_input(f"Produktlink {i + 1}", key=f"plink_{i}")
        save_products = st.form_submit_button("📂 Alle Produkte speichern")
        if save_products:
            for i in range(st.session_state.product_entries):
                name = st.session_state.get(f"pname_{i}")
                desc = st.session_state.get(f"pdesc_{i}")
                link = st.session_state.get(f"plink_{i}")
                if name and desc and link:
                    cursor.execute("""
                        INSERT INTO selly_products (email, product_name, product_description, product_link)
                        VALUES (%s, %s, %s, %s)
                    """, (st.session_state.user_email, name, desc, link))
            conn.commit()
            st.sidebar.success("✅ Alle Produkte erfolgreich gespeichert!")

conn.close()
