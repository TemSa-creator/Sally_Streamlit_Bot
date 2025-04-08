import streamlit as st

def generate_reels_idea(zielgruppe, plattform):
    if plattform.lower() == "instagram":
        return f"Reels-Idee: Zeige in 15 Sekunden, wie {zielgruppe} mit nur einem Klick ihre Online-Reichweite verdoppeln – mit den 50 AI Business Bots. Hook: 'Du willst Kunden, aber keine Zeit für Content?' Call-to-Action: 'Link in Bio!'"
    return f"Reels-Idee: Zeige deiner Community, wie {zielgruppe} mit KI Geld verdienen können. Nutze einen Vorher-Nachher-Slide oder eine " + \
           "Satz-für-Satz-Story mit Voiceover."

def generate_bio_caption(instagram_name):
    return f"In meiner Bio (@{instagram_name}) findest du den Link zu den 50 AI Business Bots, die mein Business komplett verändert haben."

def generate_dm_text(name):
    return f"Hey {name}! Ich hab was richtig Geniales entdeckt: Die 50 AI Business Bots. Die nehmen dir den ganzen Stress mit Content, Verkauf & Automatisierung ab. Magst du mal reinschauen? Hier ist mein Link: [Affiliate-Link]"

def generate_sales_copy(affiliate_link):
    return f"Diese 50 Business-Bots sind für alle, die smart statt hart arbeiten wollen. Kein Vorwissen. Kein Technik-Kram. Nur starten & verdienen. \\nJetzt sichern → {affiliate_link}"

def generate_instruction():
    return "Nutze Tools wie ManyChat oder dein Insta-Profil, um Selly in deine Bio oder Reels einzubinden. Der Bot verkauft für dich – du brauchst nur den Link teilen."

st.title("Selly - Die Verkaufs-Bot Queen")
st.markdown("**Dein smarter Verkaufs-Coach für die 50 AI Business Bots**")

name = st.text_input("Wie heißt du?")
affiliate_link = st.text_input("Was ist dein Affiliate-Link?")
instagram_name = st.text_input("Wie heißt dein Instagram-Profil? (optional)")
zielgruppe = st.text_input("Wen willst du erreichen? (z. B. Coaches, Mamas, Networkerinnen...)")
plattform = st.selectbox("Wo willst du posten?", ["Instagram", "Pinterest", "TikTok", "Facebook"])

if st.button("Generieren"):
    st.subheader("Dein Reels-Post")
    st.write(generate_reels_idea(zielgruppe, plattform))

    st.subheader("Bio-Caption")
    st.write(generate_bio_caption(instagram_name or "deinprofil"))

    st.subheader("DM-Text")
    st.write(generate_dm_text(name or "du"))

    st.subheader("Verkaufstext")
    st.write(generate_sales_copy(affiliate_link or "[Dein Affiliate-Link hier eintragen]"))

    st.subheader("Anleitung")
    st.write(generate_instruction())
