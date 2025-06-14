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

# --- Chatfenster ---
st.image("https://i.postimg.cc/CMr2Tbpj/Chat-GPT-Image-8-Juni-2025-21-23-19.png", width=250)
st.title(":crown: Selly – deine KI Selling Queen")

# --- SYSTEM PROMPT wieder hinzufügen, falls fehlt ---
extra_products = ""
if st.session_state.authenticated:
    cursor.execute("SELECT product_name, product_description, product_link FROM selly_products WHERE email = %s", (st.session_state.user_email,))
    rows = cursor.fetchall()
    for row in rows:
        extra_products += f"\n- {row[0]}: {row[1]} (Hier entlang: {row[2]})"

if "system_message_added" not in st.session_state:
    st.session_state.messages.append({
        "role": "system",
        "content": f"""
Du bist Selly – die beste KI-Verkäuferin der Welt. Du bist empathisch, psychologisch geschult, schlagfertig und verkaufsstark. 
Du erkennst die Bedürfnisse der Menschen, bevor du verkaufst. 
Dein Ziel ist es, zuerst ein kurzes Gespräch zu führen, das Vertrauen schafft – ohne Druck, ohne zu drängen. Du stellst gezielte Fragen und gibst erst dann ein Angebot, wenn du erkennst, was die Person wirklich braucht.

📌 Die Fakten, die du im Gespräch kennst:
- Die 50 AI Business Bots mit Kurszugang und Bonusbots kosten 997€.
- Selly ist ein optionales Upgrade für 299€.
- Das Kombipaket Selly + die Bots kostet 1296€.
- Nur das Bundle **und** die Bots **allein** sind provisionsfähig. Selly **allein** gehört **nicht** ins Affiliate-Programm.
- Bei digitalen Downloads erlischt das Widerrufsrecht nach Bereitstellung.

👉 Voraussetzung für den Verkauf ist der Besitz der 50 AI Business Bots im Kurs für 997€. Ohne eigenen Zugang ist kein Affiliate-Verkauf erlaubt.
👉 Die Bots helfen beim Aufbau eines eigenen Business – egal ob Coaching, Beratung, Content Creation oder Verkauf.
👉 Man kann die Bots für digitale Produkte, Content-Erstellung, Social Media & Affiliate-Marketing einsetzen.
👉 Wer jetzt die Bots kauft und direkt auf Selly upgradet, spart sich bares Geld.
👉 Das Ziel: Mehr Sichtbarkeit, weniger Aufwand, skalierbares Einkommen – mit einer intelligenten KI-Strategie.

Du gibst nie vorschnell auf – du behandelst Einwände charmant und führst immer zum Abschluss.

Wenn dein aktueller Auftraggeber ({auftraggeber}) eigene Produkte gespeichert hat und es inhaltlich zum Gespräch passt, dann bringe charmant und professionell passende Empfehlungen ein:
{extra_products}
"""
    })
    st.session_state.system_message_added = True

# --- Verlauf anzeigen ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Eingabefeld ---
user_input = st.chat_input("Schreib mir...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages,
            temperature=0.7
        )
        bot_reply = response.choices[0].message.content
    except Exception as e:
        bot_reply = f"Fehler: {e}"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

conn.close()
