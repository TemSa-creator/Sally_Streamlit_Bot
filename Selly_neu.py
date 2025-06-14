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

# --- Sidebar Login ---
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

# --- Zusatzbereich: Instagram Automation ---
if st.session_state.authenticated:
    st.sidebar.markdown("### 🧐 Selly says: Instagram Automatisierung")
    with st.sidebar.form("selly_says_form"):
        automation_trigger = st.text_input("Trigger (z. B. 'mehr infos')", st.session_state.user_products.get("instagram_trigger", ""))
        automation_message = st.text_area("Was soll Selly automatisch sagen, wenn der Trigger erkannt wird?", st.session_state.user_products.get("instagram_automation", ""))

        if automation_trigger and automation_message:
            st.info(f"**Wenn jemand auf Instagram '{automation_trigger}' schreibt, sagt Selly:**\n\n{automation_message}")

        submit_automation = st.form_submit_button("🔗 Automation speichern")

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
    st.sidebar.markdown("### 🗓️ Zusätzliche Produkte")

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

# --- Produkte auch im Prompt verwenden ---
extra_products = ""
if st.session_state.authenticated:
    cursor.execute("SELECT product_name, product_description, product_link FROM selly_products WHERE email = %s", (st.session_state.user_email,))
    rows = cursor.fetchall()
    for row in rows:
        extra_products += f"\n- {row[0]}: {row[1]} (Hier entlang: {row[2]})"

# --- SYSTEM PROMPT ---
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

conn.close()
