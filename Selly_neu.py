import streamlit as st
import openai
from openai import OpenAI
import psycopg2
import re
import os

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Selly – deine KI Selling Queen", page_icon="👑", layout="centered")
st.markdown("<style>#MainMenu{visibility:hidden;} footer{visibility:hidden;}</style>", unsafe_allow_html=True)

# --- PostgreSQL-Verbindung ---
def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD")
    )

try:
    conn = get_connection()
    cursor = conn.cursor()

    # Tabellen erstellen, falls nicht vorhanden
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS selly_users (
        email TEXT PRIMARY KEY,
        affiliate_link TEXT NOT NULL,
        affiliate_link_bundle TEXT,
        kombipaket_freigegeben BOOLEAN DEFAULT FALSE,
        tentary_id TEXT UNIQUE
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS selly_tracking (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        tentary_id TEXT,
        user_input TEXT,
        email_erkannt TEXT
    )
    """)
    conn.commit()
except Exception as e:
    st.error(f"❌ Datenbankfehler: {e}")

# --- Session States ---
for key, default in {
    "authenticated": False,
    "messages": [],
    "tentary_loaded": False,
    "tentary_id": "Sarah",
    "affiliate_link": "https://sarahtemmel.tentary.com/p/q9fupC",
    "affiliate_link_bundle": "https://sarahtemmel.tentary.com/p/e1I0e5",
    "kombipaket_freigegeben": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- URL-Parameter auslesen ---
query_params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
tentary_id_from_url = query_params.get("a", [None])[0]

if tentary_id_from_url and not st.session_state.tentary_loaded:
    try:
        cursor.execute("""
            SELECT affiliate_link, affiliate_link_bundle, kombipaket_freigegeben 
            FROM selly_users 
            WHERE tentary_id = %s
        """, (tentary_id_from_url,))
        result = cursor.fetchone()
        if result:
            st.session_state["tentary_id"] = tentary_id_from_url
            st.session_state["affiliate_link"] = result[0]
            st.session_state["affiliate_link_bundle"] = result[1] or "https://sarahtemmel.tentary.com/p/e1I0e5"
            st.session_state["kombipaket_freigegeben"] = result[2]
            st.session_state.tentary_loaded = True
    except Exception as e:
        st.error(f"Fehler beim Laden des Affiliate-Links: {e}")

auftraggeber = st.session_state["tentary_id"]
affiliate_link = st.session_state["affiliate_link_bundle"] if st.session_state["kombipaket_freigegeben"] else st.session_state["affiliate_link"]

# --- Sidebar Login ---
with st.sidebar:
    st.markdown("### 🔐 Login für Käufer")
    login_email = st.text_input("Deine Käufer-E-Mail:")
    if st.button("Login"):
        try:
            cursor.execute("""
                SELECT affiliate_link, affiliate_link_bundle, kombipaket_freigegeben, tentary_id 
                FROM selly_users 
                WHERE email = %s
            """, (login_email,))
            result = cursor.fetchone()
            if result:
                st.session_state.authenticated = True
                st.session_state.user_email = login_email
                st.session_state.affiliate_link = result[0]
                st.session_state.affiliate_link_bundle = result[1]
                st.session_state.kombipaket_freigegeben = result[2]
                st.session_state.tentary_id = result[3]
                st.success("✅ Zugang bestätigt! Selly verkauft ab jetzt mit deinem Link.")

                if result[3]:
                    selly_link = f"https://selly-bot.onrender.com?a={result[3]}"
                    st.markdown(f"🔗 **Dein persönlicher Selly-Link:** [Jetzt teilen]({selly_link})")

                    if result[2]:
                        st.markdown(f"📦 **Bundle-Link (Bots + Selly):** [Zum Shop]({result[1]})")
                    else:
                        st.markdown(f"🤖 **Nur Bots-Link:** [Zum Shop]({result[0]})")
            else:
                st.error("❌ Keine Berechtigung – bitte nur für Käufer.")
        except Exception as e:
            st.error(f"Fehler beim Login: {e}")

# Der Rest des Codes bleibt unverändert ...
