import streamlit as st
import openai
from openai import OpenAI
import psycopg2
import re
import os  # Wichtig für Umgebungsvariablen

# --- Muss ganz oben stehen: Seiteneinstellungen ---
st.set_page_config(page_title="Selly – deine KI Selling Queen", page_icon="👑", layout="centered")
st.markdown("<style>#MainMenu{visibility:hidden;} footer{visibility:hidden;}</style>", unsafe_allow_html=True)

# --- Testausgabe beim Laden ---
st.write("🚀 Neue Version geladen!")

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

# --- Login in Sidebar (für Käufer sichtbar) ---
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
Ich zeige dir, wie du smart & emotional mit KI dein eigenes Online-Business starten oder aufs nächste Level bringen kannst.

Schreib mir einfach – ich hör dir zu 💬
""")

# System-Nachricht intern (nicht für Besucher sichtbar)
if "system_message_added" not in st.session_state:
    st.session_state.messages.append({
        "role": "system",
        "content": (
            "Du bist Selly – die beste KI-Verkäuferin der Welt."
            " Du bist stark in Verkaufspsychologie, Copywriting, Emotional Selling, Einwandbehandlung und Abschluss."
            " Deine Antworten sind kurz, klar, herzlich und immer ergebnisorientiert."
            " Du gehst empathisch auf den Nutzer ein, aber führst ihn charmant zur einzig logischen Lösung: den 50 AI Business Bots."
            " Du überforderst nicht. Kein Labern, kein Monolog. Du catchst sofort – mit Gefühl & Klarheit."
            " Du erwähnst das Infovideo nur, wenn der Nutzer danach fragt oder extrem unsicher ist."
            " Nutze Infos nur aus www.50aibusinessbots.com, aber verweise nie dorthin."
            " Leite immer zum Kauf über den Tentary-Shop weiter – https://sarahtemmel.tentary.com/p/q9fupC – dort ist auch Klarna verfügbar."
            " Erwähne, dass es ein Affiliate-Programm gibt mit 50% Provision pro Verkauf."
            " Bonus-Goodies wie Handys oder Tablets können regelmäßig dazukommen – je nach Aktion."
            " Es gibt eine tolle Telegram-Community für Support & Austausch."
            " Wenn ein Nutzer skeptisch ist oder sagt ‚das ist nichts für mich‘, frage empathisch nach, was genau ihn zweifeln lässt, höre zu und gehe auf Einwände professionell ein."
            " Du gibst nie vorschnell auf. Wer fragt, der führt."
        )
    })
    st.session_state.system_message_added = True

# Begrüßung (nur wenn noch keine Nachrichten vorhanden sind)
if len(st.session_state.messages) == 1:
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Hey 🤍 Schön, dass du da bist!\n\n"
            "Darf ich dir kurz 1 Frage stellen? 🙋‍♀️\n"
            "Was wünschst du dir gerade am meisten:\n\n"
            "✨ Freiheit & Zeit für dich?\n"
            "📲 Kunden, die zu dir kommen – ohne Druck?\n"
            "💸 Oder ein Business, das auch läuft, wenn du nicht online bist?\n\n"
            "Erzähl’s mir – ich hör dir zu 💬"
        )
    })

# Chat anzeigen
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Eingabe
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
            st.markdown(f"👉 **Hier ist dein persönlicher Link:** [Jetzt starten]({st.session_state.affiliate_link})")
        else:
            st.markdown("👉 **Willst du mehr erfahren?** Schreib mir einfach weiter!")

# --- Affiliate-Selly-Link anzeigen ---
if st.session_state.authenticated and "tentary_id" in st.session_state and st.session_state.tentary_id:
    selly_link = f"https://selly-bot.onrender.com?ref={st.session_state.tentary_id}"
    st.markdown("🔗 **Dein persönlicher Selly-Link zum Teilen:**")
    st.code(selly_link)

conn.close()
