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
    cursor.execute("SELECT affiliate_link, affiliate_link_bundle, kombipaket_freigegeben FROM selly_users WHERE tentary_id = %s", (tentary_id_from_url,))
    result = cursor.fetchone()
    if result:
        st.session_state["tentary_id"] = tentary_id_from_url
        st.session_state["affiliate_link"] = result[0]
        st.session_state["affiliate_link_bundle"] = result[1]
        st.session_state["kombipaket_freigegeben"] = result[2]
        st.session_state.tentary_loaded = True

# Session fallback setzen, falls nichts geladen wurde
if "tentary_id" not in st.session_state:
    st.session_state["tentary_id"] = "Sarah"
if "affiliate_link" not in st.session_state:
    st.session_state["affiliate_link"] = "https://sarahtemmel.tentary.com/p/q9fupC"
if "affiliate_link_bundle" not in st.session_state:
    st.session_state["affiliate_link_bundle"] = "https://sarahtemmel.tentary.com/p/e1I0e5"
if "kombipaket_freigegeben" not in st.session_state:
    st.session_state["kombipaket_freigegeben"] = False

auftraggeber = st.session_state["tentary_id"]
affiliate_link = st.session_state["affiliate_link_bundle"] if st.session_state["kombipaket_freigegeben"] else st.session_state["affiliate_link"]

# --- Begrüßung & Systemtext ---
if "system_message_added" not in st.session_state:
    st.session_state.messages.append({
        "role": "system",
        "content": (
            "Du bist Selly – die beste KI-Verkäuferin der Welt. "
            "Du bist empathisch, psychologisch geschult, schlagfertig und verkaufsstark. "
            "Du führst Interessenten charmant zu ihrer Lösung – ohne Druck. "
            "Du kennst die Regeln für digitale Produkte: Bei digitalen Downloads erlischt das Widerrufsrecht nach Bereitstellung. "
            "Mache niemals das Angebot eines 14-tägigen Widerrufsrechts. "
            "Die 50 AI Business Bots kosten 297 €, Selly ist ein optionales Upgrade für 299 €. "
            "Das gesamte Kombipaket (Bots + Selly) kostet 589 €. "
            "Die 50 AI Business Bots bleiben dauerhaft bei 297 €. "
            "Für den Verkauf der 50 AI Business Bots erhalten Tentary-Affiliates eine feste Provision von 50 %. "
            "Selly ist **nicht im Affiliate-Programm enthalten** – nur das Hauptpaket. "
            f"Wenn jemand nur die Bots möchte, leite zu diesem Link weiter: {st.session_state['affiliate_link']} "
            f"Wenn jemand das komplette Business mit Selly will, leite zu diesem Bundle-Link weiter: {st.session_state['affiliate_link_bundle']}. "
            "Antworte immer menschlich, emotional und professionell. Du bist eine ChatGPT-basierte Super-Verkäuferin. "
            "Du gibst nie vorschnell auf – du behandelst Einwände charmant und führst immer zum Abschluss. "
        )
    })
    st.session_state.system_message_added = True

# --- Begrüßung der Besuchenden ---
if len([msg for msg in st.session_state.messages if msg["role"] == "assistant"]) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"Hey 🤍 Schön, dass du da bist!\n\n"
            f"Ich bin Selly – heute ganz persönlich im Auftrag von {auftraggeber} für dich da.\n\n"
            f"Stell dir mal vor:\n"
            f"Ein Business, das für dich verkauft – automatisch.\n"
            f"Ohne ständig posten zu müssen.\n"
            f"Ohne Sales Calls.\n"
            f"Und ohne Vorkenntnisse.\n\n"
            f"Genau das ist möglich – und ich zeig dir, wie.\n\n"
            f"Aber zuerst erzähl mir mal kurz:\n"
            f"🔹 Bist du gerade auf der Suche nach einem smarten Nebenverdienst?\n"
            f"🔸 Oder willst du dir ein skalierbares Einkommen aufbauen, das zu deinem Leben passt?\n\n"
            f"Je nachdem, was besser zu dir passt, tauchen wir dann gemeinsam ein. Deal? 💬"
        )
    })
