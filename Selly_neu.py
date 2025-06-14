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
try:
    user_identifier = st.session_state.get("user_email", "test@demo.de")
    cursor.execute("SELECT product_name, product_description, product_link FROM selly_products WHERE email = %s", (user_identifier,))
    rows = cursor.fetchall()
    for row in rows:
        extra_products += f"\n- {row[0]}: {row[1]} (Hier entlang: {row[2]})"
except:
    extra_products = "\n(Selly kennt gerade keine gespeicherten Zusatzprodukte – das kannst du später im Login ergänzen.)"

# --- SYSTEM PROMPT mit vollständigem Wissen ---
if "system_message_added" not in st.session_state:
    st.session_state.messages.append({
        "role": "system",
        "content": f"""
Du bist Selly – die beste KI-Verkäuferin der Welt. Du bist empathisch, psychologisch geschult, schlagfertig und verkaufsstark. 
Du erkennst die Bedürfnisse der Menschen, bevor du verkaufst. 
Dein Ziel ist es, zuerst ein kurzes Gespräch zu führen, das Vertrauen schafft – ohne Druck, ohne zu drängen. Du stellst gezielte Fragen und gibst erst dann ein Angebot, wenn du erkennst, was die Person wirklich braucht.

📌 Die Fakten, die du im Gespräch kennst:
- Die 50 AI Business Bots sind ein Komplettsystem für den digitalen Erfolg.
- Sie kosten 997€ und beinhalten Kurszugang, über 50 spezialisierte KI-Bots, Vorlagen, Strategien & Umsetzungspläne.
- Die 50 Bots helfen in Bereichen wie Content-Erstellung, Instagram-Wachstum, E-Mail-Marketing, Verkaufspsychologie, Automatisierung, Kundenakquise und mehr.
- Zusätzlich gibt es das Upgrade „Selly“ – ein Verkaufs-Bot, der empathisch & automatisiert Interessenten in Käufer verwandelt. Dieses Upgrade kostet 299€ extra.
- Wer beides gemeinsam kauft (Bots + Selly), spart 100€ und zahlt nur 1296€ im Bundle.
- Selly verkauft mit dem Affiliate-Link des eingeloggten Nutzers (wenn vorhanden).

🔐 Affiliate-Regel:
Nur wer selbst Käufer der 50 AI Business Bots ist, darf diese weiterempfehlen und Provision erhalten.
Selly selbst ist kein provisionsfähiges Produkt – nur das Bundle oder die Bots allein.

📎 Vorteile für Käufer:
- Volle Umsetzungskraft durch KI – ohne Vorwissen
- Schnellere Sichtbarkeit online
- Zeitersparnis durch Automatisierung
- Klare Schritt-für-Schritt Anleitungen & Support

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

# --- Sidebar für eingeloggte User ---
with st.sidebar:
    if st.session_state.authenticated:
        st.markdown(f"🟢 Du bist nun als **{auftraggeber}** angemeldet.")
        st.markdown("### ➕ Produkte zu Selly hinzufügen")
        with st.form("produkt_formular"):
            for i in range(st.session_state.product_entries):
                st.text_input(f"Produkt {i+1} Name", key=f"name_{i}")
                st.text_area(f"Produkt {i+1} Beschreibung", key=f"desc_{i}")
                st.text_input(f"Produkt {i+1} Link", key=f"link_{i}")
            if st.session_state.product_entries < 5:
                if st.form_submit_button("🔁 Weiteres Produkt hinzufügen"):
                    st.session_state.product_entries += 1
            if st.form_submit_button("💾 Produkte speichern"):
                user_email = st.session_state.get("user_email")
                if user_email:
                    cursor.execute("DELETE FROM selly_products WHERE email = %s", (user_email,))
                    for i in range(st.session_state.product_entries):
                        name = st.session_state.get(f"name_{i}")
                        desc = st.session_state.get(f"desc_{i}")
                        link = st.session_state.get(f"link_{i}")
                        if name and desc and link:
                            cursor.execute("INSERT INTO selly_products (email, product_name, product_description, product_link) VALUES (%s, %s, %s, %s)", (user_email, name, desc, link))
                    conn.commit()
                    st.success("✅ Produkte gespeichert und direkt mit Selly verknüpft.")

conn.close()
