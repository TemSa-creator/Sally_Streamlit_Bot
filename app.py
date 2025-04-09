import streamlit as st
import openai
import sqlite3
import re

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Selly – Verkaufs-Bot Queen", page_icon="🤖", layout="centered")
st.markdown("<style>#MainMenu{visibility:hidden;} footer{visibility:hidden;}</style>", unsafe_allow_html=True)

# --- Datenbank ---
conn = sqlite3.connect('selly.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS allowed_emails (email TEXT PRIMARY KEY)''')
c.execute('''CREATE TABLE IF NOT EXISTS leads (name TEXT, email TEXT)''')
conn.commit()

# --- Demo-Mail für Testzugang ---
demo_email = "saraharchan@gmail.com"
c.execute("INSERT OR IGNORE INTO allowed_emails (email) VALUES (?)", (demo_email,))
conn.commit()

# --- Session vorbereiten ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Login Sidebar ---
with st.sidebar:
    st.markdown("### 🔐 Login für Käufer")
    login_email = st.text_input("Deine Käufer-E-Mail:", key="login_email")
    if st.button("Login", key="login_button"):
        c.execute("SELECT * FROM allowed_emails WHERE email=?", (login_email,))
        if c.fetchone():
            st.session_state.authenticated = True
            st.session_state.user_email = login_email
            st.success("Zugang bestätigt!")
        else:
            st.error("Zugang verweigert – bitte nur für Käufer.")
            st.stop()

# --- Öffentliche Begrüßung ---
st.image("https://i.postimg.cc/xq1yKCRq/selly.jpg", width=250)
st.title("🤖 Selly – Deine Verkaufs-Bot Queen")
st.write("""
Hey, ich bin Selly!  
Willst du wissen, wie du dir mit KI ein eigenes Online-Business aufbauen oder dein bestehendes Business skalieren kannst?

Ich stelle dir ein paar Fragen – und zeige dir dann, ob & wie die **50 AI Business Bots** zu dir passen.  
Antworte einfach im Chat! 💬
""")

# --- GPT & Chatbereich nur für Käufer aktivieren ---
if st.session_state.authenticated:

    openai.api_key = st.secrets["OPENAI_API_KEY"]

    if len(st.session_state.messages) == 0:
        st.session_state.messages = [
            {"role": "system", "content": (
                "Du bist Selly, eine empathische Verkaufs-KI. "
                "Du führst Anfänger und Fortgeschrittene durch ein Gespräch, um herauszufinden, ob die 50 AI Business Bots zu ihnen passen. "
                "Du stellst Fragen, erkennst Ziele und präsentierst eine Lösung. "
                "Antworte menschlich, professionell und verkaufspsychologisch clever."
            )},
            {"role": "assistant", "content": (
                "Hey, schön, dass du da bist! 😊\n\n"
                "Bevor ich dir zeige, wie du mit den 50 AI Business Bots starten kannst, erzähl mir ein bisschen was über dich:\n\n"
                "👉 Hast du schon ein Online-Business oder fängst du ganz neu an?\n"
                "👉 Was ist aktuell deine größte Herausforderung – Content, Reichweite oder Verkauf?\n"
                "👉 Und was wünschst du dir in den nächsten 30 Tagen für dein Business?\n\n"
                "Ich hör zu – schreib einfach drauf los 💬"
            )}
        ]

    # Chatverlauf anzeigen
    for msg in st.session_state.messages:
        if msg["role"] == "system":
            continue
        with st.chat_message(msg["role"]):
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

        # Leads automatisch speichern
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
        if email_match:
            lead_email = email_match.group(0)
            name_match = re.search(r'Mein Name ist\s+([A-Za-zÄ-ÜÖä-üöß\s]+)', user_input) or \
                         re.search(r'Ich heiße\s+([A-Za-zÄ-Üä-üöß\s]+)', user_input)
            lead_name = name_match.group(1).strip() if name_match else ""

            c.execute("INSERT INTO leads (name, email) VALUES (?, ?)", (lead_name, lead_email))
            conn.commit()
            st.success(f"Danke! Dein Lead wurde gespeichert: {lead_email}")
            st.markdown("👉 **Hier geht's zu deinem Angebot:** [Jetzt starten](https://sarahtemmel.tentary.com/p/q9fupC)")
