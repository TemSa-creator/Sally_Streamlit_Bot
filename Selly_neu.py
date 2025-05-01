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
            else:
                st.error("❌ Keine Berechtigung – bitte nur für Käufer.")
        except Exception as e:
            st.error(f"Fehler beim Login: {e}")

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

# --- Bild & Begrüßung ---
st.image("https://i.postimg.cc/xq1yKCRq/selly.jpg", width=250)

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

# --- Nachrichtenverlauf anzeigen ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Eingabe & Antwortverarbeitung ---
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

    # Leads erkennen
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
    if email_match:
        lead_email = email_match.group(0)
        st.success(f"🎉 Danke für deine Nachricht, {lead_email}!")

    # Tracking speichern
    try:
        cursor.execute("""
            INSERT INTO selly_tracking (tentary_id, user_input, email_erkannt)
            VALUES (%s, %s, %s)
        """, (
            st.session_state.get("tentary_id", "Unbekannt"),
            user_input,
            email_match.group(0) if email_match else None
        ))
        conn.commit()
    except:
        pass

try:
    conn.close()
except:
    pass
