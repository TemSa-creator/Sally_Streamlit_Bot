import streamlit as st
import openai
import psycopg2
import re

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Selly – Verkaufs-Bot Queen", page_icon="🤖", layout="centered")
st.markdown("<style>#MainMenu{visibility:hidden;} footer{visibility:hidden;}</style>", unsafe_allow_html=True)

# --- PostgreSQL-Verbindung ---
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="DEIN_PASSWORT_HIER"  # 🔁 Passwort anpassen
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

# --- Login in Sidebar ---
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
            st.success("✅ Zugang bestätigt!")
        else:
            st.error("❌ Keine Berechtigung – bitte nur für Käufer.")

# Sessions initialisieren
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Begrüßung für alle Besucher ---
st.image("https://i.postimg.cc/xq1yKCRq/selly.jpg", width=250)
st.title("🤖 Selly – Deine Verkaufs-Bot Queen")
st.write("""
Hey, ich bin Selly!  
Willst du wissen, wie du dir mit KI ein eigenes Online-Business aufbauen oder dein bestehendes Business skalieren kannst?

Ich stelle dir ein paar Fragen – und zeige dir dann, ob & wie die **50 AI Business Bots** zu dir passen.  
Antworte einfach im Chat! 💬
""")

# Startnachricht
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Hey, schön, dass du hier bist! 🤗\n\n"
            "Darf ich dir ein paar Fragen stellen, um zu sehen, ob die 50 AI Business Bots zu dir passen?\n\n"
            "👉 Hast du schon ein Business oder willst du gerade erst starten?\n"
            "👉 Was stresst dich aktuell am meisten – Content, Reichweite oder Verkauf?\n"
            "👉 Und was wünschst du dir in den nächsten 30 Tagen für dein Business?"
        )
    })

# Verlauf anzeigen
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
            messages=[
                {"role": "system", "content": (
                    "Du bist Selly, eine empathische Verkaufs-KI. "
                    "Du hilfst Nutzern dabei, herauszufinden, ob die 50 AI Business Bots zu ihnen passen. "
                    "Du stellst gezielte Fragen, motivierst und führst logisch zum Kauf."
                )}
            ] + st.session_state.messages,
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
            st.markdown("👉 **Möchtest du mehr erfahren?** Schreib mir einfach weiter!")

conn.close()
