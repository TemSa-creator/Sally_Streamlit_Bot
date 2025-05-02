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

# Tabelle erstellen, falls nicht vorhanden
cursor.execute("""
CREATE TABLE IF NOT EXISTS selly_users (
    email TEXT PRIMARY KEY,
    affiliate_link TEXT NOT NULL,
    tentary_id TEXT UNIQUE,
    affiliate_link_bundle TEXT
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
    cursor.execute("SELECT affiliate_link, affiliate_link_bundle FROM selly_users WHERE tentary_id = %s", (tentary_id_from_url,))
    result = cursor.fetchone()
    if result:
        st.session_state["tentary_id"] = tentary_id_from_url
        st.session_state["affiliate_link"] = result[0]
        st.session_state["affiliate_link_bundle"] = result[1] or "https://sarahtemmel.tentary.com/p/e1I0e5"
        st.session_state.tentary_loaded = True

# Session fallback setzen, falls nichts geladen wurde
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
        cursor.execute("SELECT affiliate_link, tentary_id, affiliate_link_bundle FROM selly_users WHERE email = %s", (login_email,))
        result = cursor.fetchone()
        if result:
            st.session_state.authenticated = True
            st.session_state.user_email = login_email
            st.session_state.affiliate_link = result[0]
            st.session_state.tentary_id = result[1]
            st.session_state.affiliate_link_bundle = result[2] or "https://sarahtemmel.tentary.com/p/e1I0e5"
            st.session_state.tentary_loaded = True
            st.success("✅ Zugang bestätigt! Selly verkauft ab jetzt mit deinem Link.")
            if result[1]:
                st.markdown(f"🔗 **Dein persönlicher Selly-Link:** [Jetzt teilen](https://selly-bot.onrender.com?a={result[1]})")
                st.markdown(f"🤝 **Selly ist im Auftrag von `{result[1]}` aktiv.**")
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

Schreib mir einfach – ich hör dir zu 💬
""")
else:
    st.write("Hey, ich bin Selly – deine KI Selling Queen 👑")

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
            "Wer jetzt die Bots kauft und direkt auf Selly upgradet, spart sich bares Geld. Das Kombipaket kostet 589 € "
            "Die 50 AI Business Bots bleiben dauerhaft bei 297 €. "
            "Für den Verkauf der 50 AI Business Bots erhalten Tentary-Affiliates eine feste Provision von 50 %. "
            "Selly ist **nicht im Affiliate-Programm enthalten** – nur im Bundle, aber nicht einzeln."
            f"Leite immer zum offiziellen Tentary-Shop weiter: {affiliate_link} "
            f"\n👉 Das Bundle findest du hier: {affiliate_link_bundle} "
            "\nAntworte immer menschlich, emotional und professionell. Du bist eine ChatGPT-basierte Super-Verkäuferin. "
            "Du gibst nie vorschnell auf – du behandelst Einwände charmant und führst immer zum Abschluss. "
            f"Wenn du die 50 AI Business Bots kaufen möchtest, klick hier: {affiliate_link} "
        )
    })
    st.session_state.system_message_added = True

if len([msg for msg in st.session_state.messages if msg["role"] == "assistant"]) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"Hey 🤍 Schön, dass du da bist!\n\n"
            f"Ich bin Selly – heute im Auftrag von {auftraggeber} da ✨\n\n"
            f"Darf ich dir kurz 1 Frage stellen?\n"
            f"Was wünschst du dir gerade am meisten:\n\n"
            f"💡 Mehr Freiheit?\n"
            f"📲 Kunden, die auf dich zukommen?\n"
            f"💸 Ein Business, das automatisch verkauft?\n\n"
            f"Ich hätte da was für dich... Frag mich einfach 😉"
        )
    })

# --- Nachrichtenverlauf anzeigen ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Eingabe ---
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
            st.markdown(f"🔗 **Hier ist dein persönlicher Selly-Link:** [Jetzt teilen]({link})")
        else:
            st.markdown("🔗 **Willst du mehr erfahren?** Schreib mir einfach weiter!")

conn.close()
