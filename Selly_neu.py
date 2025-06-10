# selly_neu.py

from flask import Flask, request, jsonify
import openai
import psycopg2
import re

# Konfiguration
OPENAI_API_KEY = "dein_openai_api_key"
DATABASE_CONFIG = {
    'dbname': 'dein_db_name',
    'user': 'dein_db_user',
    'password': 'dein_db_passwort',
    'host': 'dein_host',
    'port': '5432'
}

# Initialisierung
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)

# --- Datenbank Abfrage: prüfe, ob Affiliate ID freigegeben ---
def is_affiliate_allowed(affiliate_id):
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT selly_freigeschaltet, produktfreigabe
            FROM affiliates
            WHERE affiliate_id = %s
        """, (affiliate_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            freigeschaltet, produktfreigabe = result
            return freigeschaltet == True, produktfreigabe
        else:
            return False, ""
    except Exception as e:
        print("DB Error:", e)
        return False, ""

# --- OpenAI Anfrage ---
def ask_openai(system_message, user_message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print("OpenAI Error:", e)
        return "❌ Fehler bei der Verbindung zur KI."

# --- Systemprompt vorbereiten ---
def get_system_prompt(produktfreigabe):
    # Produkte in der Freigabe erkennen
    produkte = []
    if "bots" in produktfreigabe:
        produkte.append("die 50 AI Business Bots (297€)")
    if "bundle" in produktfreigabe:
        produkte.append("das Bundle inkl. Selly und Insta Master (499€)")
    if "selly" in produktfreigabe:
        produkte.append("Selly – die Verkaufs-KI (199€)")
    # Hier kannst du weitere Produkte ergänzen!

    produkttext = " und ".join(produkte) if produkte else "keine Produkte"

    system_message = f"""
    Du bist Selly – die empathische Verkaufs-KI von Sarah Temmel. 
    Du sprichst mit Interessenten und hilfst ihnen, passende Produkte zu finden und zu kaufen.

    Der aktuelle Affiliate hat folgende Produkte freigeschaltet: {produkttext}.

    Regeln:
    - Verkaufe nur diese Produkte.
    - Wenn Produkte nicht freigegeben sind → sage: "Das Produkt kann ich aktuell nicht anbieten."
    - Baue Vertrauen auf, beantworte Fragen klar.
    - Verwende keine komplizierten Begriffe.
    - Du bist freundlich, sympathisch, kompetent.

    Preise:
    - 50 AI Business Bots → 297 €
    - Bundle inkl. Selly und Insta Master → 499 €
    - Selly → 199 €

    Schließe Verkäufe freundlich ab und leite zum Affiliate-Link weiter:

    👉 Kauflink: https://www.50aibusinessbots.com/?aff={affiliate_id}

    Wichtig:
    - Du sprichst DU an.
    - Du machst keine unseriösen oder unrealistischen Versprechungen.
    - Du nutzt Verkaufspsychologie: Vertrauen, Klarheit, Nutzen kommunizieren.
    """

    return system_message

# --- Flask API Route ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    affiliate_id = data.get("affiliate_id", "ROOT")
    user_message = data.get("message", "")

    # Sonderfall: Auth Check
    if user_message.lower() == "auth-check":
        freigeschaltet, _ = is_affiliate_allowed(affiliate_id)
        if freigeschaltet:
            return jsonify({"reply": "✅ Zugriff erlaubt für Affiliate."})
        else:
            return jsonify({"reply": "❌ Kein Zugriff für diese Affiliate-ID."})

    # Prüfen ob freigeschaltet + welche Produkte
    freigeschaltet, produktfreigabe = is_affiliate_allowed(affiliate_id)

    if not freigeschaltet:
        return jsonify({"reply": "❌ Du bist aktuell nicht für Selly freigeschaltet."})

    # System Prompt bauen
    system_message = get_system_prompt(produktfreigabe)

    # Antwort von OpenAI holen
    reply = ask_openai(system_message, user_message)

    return jsonify({"reply": reply})

# --- Main ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
