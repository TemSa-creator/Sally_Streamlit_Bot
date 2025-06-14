import streamlit as st
import openai
from openai import OpenAI
import psycopg2
import os

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Selly – deine KI Selling Queen", layout="centered")
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

# --- SYSTEMWISSEN über Bots ---
if "system_message_added" not in st.session_state:
    st.session_state.messages.append({
        "role": "system",
        "content": f"""
Du bist Selly – die beste KI-Verkäuferin der Welt. Du bist empathisch, psychologisch geschult und verkaufsstark. 

📌 Hier ist das Wissen über die Hauptprodukte:
- Die 50 AI Business Bots mit Kurszugang und Bonusbots kosten 997€.
- Selly ist ein optionales Upgrade für 299€.
- Das Kombipaket Selly + die Bots kostet 1296€.
- Nur das Bundle **und** die Bots **allein** sind provisionsfähig. Selly **allein** gehört **nicht** ins Affiliate-Programm.
- Bei digitalen Downloads erlischt das Widerrufsrecht nach Bereitstellung.
- Die Bots helfen beim Aufbau eines Online-Business in Coaching, Beratung, Content Creation oder Verkauf.
- Der Zugang erfolgt sofort mit Kursmodulen, PDF-Guides, Bonus-Bots und Community.
- Wer direkt auf Selly upgradet, spart bares Geld und automatisiert den Verkauf.

Wenn jemand kaufen will, biete:
1. Die 50 AI Business Bots für 997€ – Link: {affiliate_link}
2. Das Kombipaket Selly + Bots für 1296€ – Link: {affiliate_link_bundle}

Handle immer wie eine kluge, menschliche Verkäuferin.
"""
    })
    st.session_state.system_message_added = True

# --- Selly Bild & Begrüßung ---
st.image("https://i.postimg.cc/CMr2Tbpj/Chat-GPT-Image-8-Juni-2025-21-23-19.png", width=250)
st.title("👑 Selly – deine KI Selling Queen")

if len([msg for msg in st.session_state.messages if msg["role"] == "assistant"]) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"Hey ❤️ Schön, dass du da bist!\n\n"
            f"Ich bin Selly – heute im Auftrag von {auftraggeber} da ✨\n\n"
            f"Darf ich dir kurz 1 Frage stellen?\nWas wünschst du dir gerade am meisten:\n\n"
            f"💡 Mehr Freiheit?\n"
            f"📲 Kunden, die auf dich zukommen?\n"
            f"💸 Ein Business, das automatisch verkauft?\n\n"
            f"Ich hätte da was für dich... Frag mich einfach 😉"
        )
    })

# --- Chatverlauf ---
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

# --- Sidebar Login und Impressum ---
with st.sidebar:
    if not st.session_state.authenticated:
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
                st.session_state.user_products = user_data
                st.session_state.tentary_loaded = True
                st.success("✅ Du bist jetzt eingeloggt – Selly ist aktiv.")
            else:
                st.error("❌ Keine Berechtigung – bitte nur für Käufer.")

    if st.session_state.authenticated:
        st.markdown("---")
        st.markdown(f"### 📢 Hier ist dein Link zum Teilen für Selly")
        st.code(f"https://selly-bot.onrender.com/?a={st.session_state.tentary_id}")

        st.markdown("---")
        st.markdown("### 📋 Meine Produkte bearbeiten")
        with st.form("produkte_form"):
            for i in range(1, 6):
                name = st.text_input(f"Produkt {i} Name", st.session_state.user_products.get(f"product_{i}_name", ""))
                desc = st.text_area(f"Produkt {i} Beschreibung", st.session_state.user_products.get(f"product_{i}_desc", ""))
                link = st.text_input(f"Produkt {i} Link", st.session_state.user_products.get(f"product_{i}_link", ""))

            if st.form_submit_button("💾 Speichern"):
                cursor.execute("""
                    UPDATE selly_users SET
                        product_1_name = %s, product_1_desc = %s, product_1_link = %s,
                        product_2_name = %s, product_2_desc = %s, product_2_link = %s,
                        product_3_name = %s, product_3_desc = %s, product_3_link = %s,
                        product_4_name = %s, product_4_desc = %s, product_4_link = %s,
                        product_5_name = %s, product_5_desc = %s, product_5_link = %s
                    WHERE email = %s
                """, (
                    st.session_state.user_products.get("product_1_name", ""),
                    st.session_state.user_products.get("product_1_desc", ""),
                    st.session_state.user_products.get("product_1_link", ""),
                    st.session_state.user_products.get("product_2_name", ""),
                    st.session_state.user_products.get("product_2_desc", ""),
                    st.session_state.user_products.get("product_2_link", ""),
                    st.session_state.user_products.get("product_3_name", ""),
                    st.session_state.user_products.get("product_3_desc", ""),
                    st.session_state.user_products.get("product_3_link", ""),
                    st.session_state.user_products.get("product_4_name", ""),
                    st.session_state.user_products.get("product_4_desc", ""),
                    st.session_state.user_products.get("product_4_link", ""),
                    st.session_state.user_products.get("product_5_name", ""),
                    st.session_state.user_products.get("product_5_desc", ""),
                    st.session_state.user_products.get("product_5_link", ""),
                    st.session_state.user_email
                ))
                conn.commit()
                st.success("✅ Produkte gespeichert!")

    st.markdown("---")
    st.markdown("""
    [Impressum](https://sarahtemmel.tentary.com/legal/207493326/contact)  
    [Datenschutz](https://sarahtemmel.tentary.com/legal/207493326/privacy)  
    <sub>Powered by Selly – The Empire</sub>
    """, unsafe_allow_html=True)

conn.close()
