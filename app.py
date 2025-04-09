import streamlit as st
import openai
import psycopg2
import re

# --- Testausgabe beim Laden ---
st.write("🚀 Neue Version geladen!")
st.write("🔐 PostgreSQL-Nutzer:", st.secrets["DB_USER"])

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Selly – deine KI Selling Queen", page_icon="👑", layout="centered")
st.markdown("<style>#MainMenu{visibility:hidden;} footer{visibility:hidden;}</style>", unsafe_allow_html=True)

# --- PostgreSQL-Verbindung ---
def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"]
    )

conn = get_connection()
cursor = conn.cursor()

# Tabelle anlegen (nur beim ersten Mal)
cursor.execute("""
CREATE TABLE IF NOT EXISTS selly_users (
    email TEXT PRIMARY KEY,
    affiliate_link TEXT NOT NULL
)
""")
conn.commit()

# --- Login in Sidebar (für Käufer sichtbar) ---
with st.sidebar:
    st.markdown("### 🔐 Login für Käufer")
    login_email = st.text_input("Deine Käufer-E-Mail:")
    if st.button("Login"):
        cursor.execute("SELECT affiliate_link FROM selly_users WHERE email = %s", (login_email,))
        result = cursor.fetchone()
        if result:
            st.session_state.authenticated = True
            st.session_state.user_email = login_email
            st.session_state.affiliate_link = result[0]
            st.success("✅ Zugang bestätigt! Selly verkauft ab jetzt mit deinem Link.")
        else:
            st.error("❌ Keine Berechtigung – bitte nur für Käufer.")

# --- Session States ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Begrüßung für alle Besucher ---
st.image("https://i.postimg.cc/xq1yKCRq/selly.jpg", width=250)
st.title("👑 Selly – deine KI Selling Queen")
st.write("""
Hey, ich bin Selly – deine KI Selling Queen 👑  
Ich zeige dir, wie du mit künstlicher Intelligenz dein eigenes Online-Business starten oder dein bestehendes Business auf ein neues Level bringst.

Antworte einfach im Chat – ich stelle dir ein paar gezielte Fragen und zeige dir dann deine Möglichkeiten 💬
""")

# Startnachricht (für Interessenten sichtbar)
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "system",
        "content": (
            "Du bist Selly – eine KI Selling Queen. "
            "Du bist spezialisiert auf Verkaufspsychologie, Copywriting und zielgerichtete Gespräche. "
            "Du erkennst sofort, wer vor dir steht, stellst die richtigen Fragen, baust Vertrauen auf und führst logisch zur Lösung: den 50 AI Business Bots. "
            "Du verkaufst nur dieses Produkt – professionell, empathisch und effizient."
        )
    })
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Hey, wie schön, dass du hier bist! 🤗\n\n"
            "Erzähl mir doch mal: Was ist dein größter Wunsch im Moment?\n\n"
            "👉 Möchtest du ortsunabhängig arbeiten und mehr Freiheit im Alltag?\n"
            "👉 Oder suchst du eine Möglichkeit, mit deinem Herzensthema online Geld zu verdienen?\n"
            "👉 Vielleicht hast du schon ein Business und willst automatisieren & skalieren?\n\n"
            "Ich höre dir zu – und zeig dir Schritt für Schritt, wie das mit den 50 AI Business Bots möglich ist! 💬"
        )
    })

# Chat anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Eingabe
user_input = st.chat_input("Schreib mir...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=st.session_state.messages,
            temperature=0.7
        )
        bot_reply = response["choices"][0]["message"]["content"]
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
        if st.session_state.authenticated:
            st.markdown(f"👉 **Hier ist dein persönlicher Link:** [Jetzt starten]({st.session_state.affiliate_link})")
        else:
            st.markdown("👉 **Willst du mehr erfahren?** Schreib mir einfach weiter!")

conn.close()
