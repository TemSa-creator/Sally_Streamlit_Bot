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

# --- Sidebar ---
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

# --- Begrüßung & Selly Bild ---
st.image("https://i.postimg.cc/CMr2Tbpj/Chat-GPT-Image-8-Juni-2025-21-23-19.png", width=250)
st.title(":crown: Selly – deine KI Selling Queen")

# --- SYSTEM PROMPT ---
if "system_message_added" not in st.session_state:
    products_text = ""
    if st.session_state.get("user_products"):
        for i in range(1, 6):
            name = st.session_state.user_products.get(f"product_{i}_name")
            desc = st.session_state.user_products.get(f"product_{i}_desc")
            link = st.session_state.user_products.get(f"product_{i}_link")
            if name and desc and link:
                products_text += f"\n- {name}: {desc} (Hier entlang: {link})"

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

Wenn der Nutzer kaufen möchte, biete ihm beide Optionen charmant an:
1. Die 50 AI Business Bots für 997€, die sofort einsetzbar sind. Mit starkem Support und Kurszugang zu verschiedenen Modulen.
2. Oder das Kombipaket mit Selly für 1296€, wenn er gleich alles automatisieren will.
Verwende dabei die Links affiliate_link = {affiliate_link}, affiliate_link_bundle = {affiliate_link_bundle}.

Wenn der Nutzer sich für eine Option entscheidet oder direkt nach dem Link fragt, gib den entsprechenden Link sofort und klar aus.

Wenn der Nutzer direkt sagt, dass er kaufen möchte (z.B. „Ich will das“, „Ich will kaufen“, „Gib mir den Link“, „Ich bin bereit“, „Wo kann ich bezahlen“), dann gib ihm sofort den passenden Kauf-Link aus – ohne weitere Rückfragen.

Wenn dein aktueller Auftraggeber ({auftraggeber}) eigene Produkte gespeichert hat und es inhaltlich zum Gespräch passt, dann bringe charmant und professionell passende Empfehlungen ein:
{products_text}

Erwähne Produkte niemals plump oder unpassend. Du bist wie eine menschliche Top-Verkäuferin.
"""
    })
    st.session_state.system_message_added = True

# --- Begrüßung ---
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

# --- Meine Produkte bearbeiten ---
if st.session_state.authenticated:
    st.sidebar.markdown("### 📋 Meine Produkte bearbeiten\n"
                        "<sub>👉 Hinweis: Deine hier gespeicherten Produkte werden von Selly automatisch im Gespräch berücksichtigt, wenn es für den Interessenten sinnvoll ist.</sub>",
                        unsafe_allow_html=True)
    with st.sidebar.form("produkte_form"):
        p1_name = st.text_input("Produkt 1 Name", st.session_state.user_products.get("product_1_name", ""))
        p1_desc = st.text_area("Produkt 1 Beschreibung", st.session_state.user_products.get("product_1_desc", ""))
        p1_link = st.text_input("Produkt 1 Link", st.session_state.user_products.get("product_1_link", ""))

        p2_name = st.text_input("Produkt 2 Name", st.session_state.user_products.get("product_2_name", ""))
        p2_desc = st.text_area("Produkt 2 Beschreibung", st.session_state.user_products.get("product_2_desc", ""))
        p2_link = st.text_input("Produkt 2 Link", st.session_state.user_products.get("product_2_link", ""))

        p3_name = st.text_input("Produkt 3 Name", st.session_state.user_products.get("product_3_name", ""))
        p3_desc = st.text_area("Produkt 3 Beschreibung", st.session_state.user_products.get("product_3_desc", ""))
        p3_link = st.text_input("Produkt 3 Link", st.session_state.user_products.get("product_3_link", ""))

        p4_name = st.text_input("Produkt 4 Name", st.session_state.user_products.get("product_4_name", ""))
        p4_desc = st.text_area("Produkt 4 Beschreibung", st.session_state.user_products.get("product_4_desc", ""))
        p4_link = st.text_input("Produkt 4 Link", st.session_state.user_products.get("product_4_link", ""))

        p5_name = st.text_input("Produkt 5 Name", st.session_state.user_products.get("product_5_name", ""))
        p5_desc = st.text_area("Produkt 5 Beschreibung", st.session_state.user_products.get("product_5_desc", ""))
        p5_link = st.text_input("Produkt 5 Link", st.session_state.user_products.get("product_5_link", ""))

        submit_button = st.form_submit_button("💾 Speichern")

        if submit_button:
            cursor.execute("""
                UPDATE selly_users SET
                    product_1_name = %s,
                    product_1_desc = %s,
                    product_1_link = %s,
                    product_2_name = %s,
                    product_2_desc = %s,
                    product_2_link = %s,
                    product_3_name = %s,
                    product_3_desc = %s,
                    product_3_link = %s,
                    product_4_name = %s,
                    product_4_desc = %s,
                    product_4_link = %s,
                    product_5_name = %s,
                    product_5_desc = %s,
                    product_5_link = %s
                WHERE email = %s
            """, (
                p1_name, p1_desc, p1_link,
                p2_name, p2_desc, p2_link,
                p3_name, p3_desc, p3_link,
                p4_name, p4_desc, p4_link,
                p5_name, p5_desc, p5_link,
                st.session_state.user_email
            ))
            conn.commit()
            st.sidebar.success("✅ Produkte erfolgreich gespeichert!")

conn.close()
