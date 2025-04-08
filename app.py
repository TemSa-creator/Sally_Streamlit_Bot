import streamlit as st
import openai
import sqlite3
import re

# --- Konfiguration ---
st.set_page_config(page_title="Selly V4", page_icon="🤖", layout="centered")
st.markdown("<style>#MainMenu{visibility:hidden;} footer{visibility:hidden;}</style>", unsafe_allow_html=True)

# --- Datenbank verbinden ---
conn = sqlite3.connect('selly.db')
c = conn.cursor()

# Tabellen erstellen
c.execute('''CREATE TABLE IF NOT EXISTS allowed_emails (email TEXT PRIMARY KEY)''')
c.execute('''CREATE TABLE IF NOT EXISTS leads (name TEXT, email TEXT)''')
conn.commit()

# --- Demo-Mail einfügen (für dich) ---
demo_email = "saraharchan@gmail.com"
c.execute("INSERT OR IGNORE INTO allowed_emails (email) VALUES (?)", (demo_email,))
conn.commit()

# --- Login ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Selly Login")
    email_input = st.text_input("Gib bitte deine Käufer-E-Mail-Adresse ein:")
    if st.button("Login"):
        c.execute("SELECT * FROM allowed_emails WHERE email=?", (email_input,))
        if c.fetchone():
            st.session_state.authenticated = True
            st.session_state.user_email = email_input
            st.success("Zugang bestätigt!")
            st.experimental_rerun()
        else:
            st.error("Zugang verweigert – bitte nur für Käufer.")
            st.stop()

# --- GPT-Setup ---
st.title("🤖 Selly – Deine Verkaufs-Bot Queen")
st.write("Ich helfe dir, Leads zu sammeln & die 50 AI Business Bots zu verkaufen.")

openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "DEIN_OPENAI_KEY"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": (
            "Du bist Selly, ein empathischer Verkaufs-Chatbot. "
            "Du stellst Fragen zu Zielen, Blockaden und Visionen. "
            "Du führst Nutzer logisch zum Kauf der 50 AI Business Bots. "
            "Sprich deutsch, sei freundlich, motivierend & verkaufspsychologisch clever.")},
        {"role": "assistant", "content": "Hey, ich bin Selly! Was ist dein größtes Ziel im Online-Business?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"] if msg["role"] != "system" else "assistant"):
        st.markdown(msg["content"])

user_input = st.chat_input("Schreib mir...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=st.session_state.messages,
            temperature=0.7
        )
        bot_reply = response["choices"][0]["message"]["content"]
    except Exception as e:
        bot_reply = f"Fehler bei der Antwort: {e}"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

    # --- Lead-Erkennung ---
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
    if email_match:
        lead_email = email_match.group(0)
        name_match = re.search(r'Mein Name ist\s+([A-Za-zÄ-ÜÖä-üöß\s]+)', user_input) or \
                     re.search(r'Ich heiße\s+([A-Za-zÄ-ÜÖä-üöß\s]+)', user_input)
        lead_name = name_match.group(1).strip() if name_match else ""

        c.execute("INSERT INTO leads (name, email) VALUES (?, ?)", (lead_name, lead_email))
        conn.commit()
        st.success(f"Danke! Dein Lead wurde gespeichert: {lead_email}")
        st.markdown("👉 **Hier geht's zu deinem Angebot:** [Jetzt starten](https://sarahtemmel.tentary.com/p/q9fupC)")
        st.stop()
