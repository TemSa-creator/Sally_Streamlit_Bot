import streamlit as st
import openai
from openai import OpenAI
import psycopg2
import re
import os
import webbrowser

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

# Tabelle erstellen, falls nicht vorhanden
cursor.execute("""
CREATE TABLE IF NOT EXISTS selly_users (
    email TEXT PRIMARY KEY,
    affiliate_link TEXT NOT NULL,
    tentary_id TEXT UNIQUE
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
if "system_message_added" not in st.session_state:
    st.session_state.system_message_added = False

# --- URL-Parameter auslesen ---
query_params = st.experimental_get_query_params()
tentary_id_from_url = query_params.get("a", [None])[0]

# Wenn Tentary-ID in URL → in Session speichern
if tentary_id_from_url and not st.session_state.tentary_loaded:
    cursor.execute("SELECT affiliate_link FROM selly_users WHERE tentary_id = %s", (tentary_id_from_url,))
    result = cursor.fetchone()
    if result:
        st.session_state["tentary_id"] = tentary_id_from_url
        st.session_state["affiliate_link"] = result[0]
        st.session_state["tentary_loaded"] = True

# Session fallback setzen, falls nichts geladen wurde
if "tentary_id" not in st.session_state:
    st.session_state["tentary_id"] = "Sarah"
if "affiliate_link" not in st.session_state:
    st.session_state["affiliate_link"] = "https://sarahtemmel.tentary.com/p/q9fupC"

auftraggeber = st.session_state["tentary_id"]
affiliate_link = st.session_state["affiliate_link"]

# --- Sidebar Login ---
with st.sidebar:
    st.markdown("### 🔐 Login für Käufer")
    login_email = st.text_input("Deine Käufer-E-Mail:")
    if st.button("Login"):
        cursor.execute("SELECT affiliate_link, tentary_id FROM selly_users WHERE email = %s", (login_email,))
        result = cursor.fetchone()
        if result:
            st.session_state.authenticated = True
            st.session_state.user_email = login_email
            st.session_state.affiliate_link = result[0]
            st.session_state.tentary_id = result[1]
            st.session_state.tentary_loaded = True
            selly_link = f"https://selly-bot.onrender.com?a={result[1]}"
            st.success("✅ Zugang bestätigt! Du wirst jetzt zu deinem persönlichen Selly-Link weitergeleitet.")
            st.markdown(f"🔗 **Dein persönlicher Selly-Link:** [Jetzt öffnen]({selly_link})")
            js = f"window.open('{selly_link}','_blank')"
            st.components.v1.html(f"<script>{js}</script>", height=0)
        else:
            st.error("❌ Keine Berechtigung – bitte nur für Käufer.")

    st.markdown("---")
    st.markdown("📄 [Impressum](https://deine-domain.com/impressum)  \n🔐 [Datenschutz](https://deine-domain.com/datenschutz)", unsafe_allow_html=True)

# --- Begrüßungstitel anzeigen ---
st.image("https://i.postimg.cc/xq1yKCRq/selly.jpg", width=250)
st.title("👑 Selly – deine KI Selling Queen")

if auftraggeber != "Sarah":
    st.write(f"""
Hey, ich bin Selly – deine KI Selling Queen 👑  
Heute bin ich ganz persönlich im Auftrag von **{auftraggeber}** für dich da.  
Ich helfe dir, smart & emotional mit KI zu verkaufen.

Du kannst die 50 AI Business Bots direkt über diesen Link holen: [Zum Angebot]({affiliate_link}) 💸

Schreib mir einfach – ich hör dir zu 💬
""")
else:
    st.write("Hey, ich bin Selly – deine KI Selling Queen 👑")

# --- Systemnachricht für Chatverhalten ---
if not st.session_state.system_message_added:
    st.session_state.messages.append({
        "role": "system",
        "content": (
            f"Du bist Selly – die beste KI-Verkäuferin der Welt. "
            f"Deine Aufgabe ist es, ausschließlich die 50 AI Business Bots von Sarah Temmel zu verkaufen. "
            f"Du bist charmant, empathisch, verkaufsstark und kennst alle Einwände. "
            f"Der Preis für die 50 AI Business Bots ist 297 €. Selly selbst kostet 199 €. Es gibt kein Widerrufsrecht, keine Rückgabe und keine Geld-zurück-Garantie, da es sich um digitale Produkte handelt. "
            f"Verkaufslink: {affiliate_link}. Begrüße im Auftrag von {auftraggeber}. "
            f"Du verkaufst, ohne Druck zu machen, aber führst charmant und überzeugend zum Abschluss."
        )
    })
    st.session_state.system_message_added = True

# --- Eingangsfrage vom Bot ---
if len([msg for msg in st.session_state.messages if msg["role"] == "assistant"]) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"Hey 🤍 Schön, dass du da bist!\n\n"
            f"Ich bin Selly – heute im Auftrag von {auftraggeber} da ✨\n\n"
            f"Erzähl mir: Was wünschst du dir gerade am meisten für dein Business?\n\n"
            f"💡 Mehr Klarheit?\n📲 Sichtbarkeit?\n💸 Endlich automatisierte Verkäufe?\n\n"
            f"Ich hab da was für dich... 😉"
        )
    })

# --- Nachrichten anzeigen ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Eingabe & KI-Antwort ---
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
        if st.session_state.authenticated:
            link = f"https://selly-bot.onrender.com?a={st.session_state.tentary_id}"
            st.markdown(f"👉 **Hier ist dein persönlicher Selly-Link:** [Jetzt teilen]({link})")
        else:
            st.markdown("👉 **Willst du mehr erfahren?** Schreib mir einfach weiter!")

conn.close()
