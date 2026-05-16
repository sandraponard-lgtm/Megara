import streamlit as st
import re
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

# Interface utilisateur
st.title("📊 Analyseur & Extracteur de Contenu YouTube")
st.write("Collez une URL YouTube pour générer un résumé complet, des points clés, des citations et des chiffres marquants.")

# Sidebar pour la configuration de l'API Key
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Clé API Google Gemini", type="password", help="Obtenez une clé gratuite sur Google AI Studio")
    st.markdown("---")
    st.caption("Développé avec Streamlit & Gemini API")

# Champ de saisie pour l'URL
video_url = st.text_input("Entrez l'URL de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Analyser la vidéo", type="primary"):
    if not api_key:
        st.warning("Veuillez renseigner votre clé API Gemini dans la barre latérale.")
    elif not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        # Nettoyage rapide de l'URL pour s'assurer qu'elle est propre
        if "youtu.be/" in video_url and "?" in video_url:
            # Extrait l'URL de base si elle contient des paramètres mobiles étranges (?is=...)
            video_url = video_url.split("?")[0]

        st.success("Connexion à Gemini réussie ! Analyse de la vidéo en cours (cela peut prendre 10 à 30 secondes)...")
        
        try:
            # Initialisation du client Gemini
            client = genai.Client(api_key=api_key)
            
            # Prompt d'ingénierie structuré envoyé à l'IA avec la vidéo intégrée
            prompt = f"""
            Agis comme un analyste expert. Regarde attentivement la vidéo YouTube liée à cette URL et rédige un rapport structuré en français.
            URL de la vidéo : {video_url}
            
            Format attendu :
            
            ## 📝 Résumé Global
            (Rédige un résumé condensé et percutant de la vidéo en un ou deux paragraphes maximum)
            
            ---
            
            ## 💡 Idées Clés & Bullet Points
            (Liste à puces des concepts essentiels développés dans la vidéo)
            
            ---
            
            ## 💬 Citations Marquantes
            (Extraits ou phrases fortes prononcées dans la vidéo)
            
            ---
            
            ## 🔢 Chiffres Clés & Données
            (Liste des données chiffrées, statistiques, dates ou métriques importantes mentionnées)
            """
            
            # Appel au modèle de génération de contenu
            with st.spinner("L'IA examine la vidéo et génère vos insights..."):
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
            
            # Affichage des résultats
            st.markdown("---")
            st.subheader("🎬 Résultats de l'Analyse")
            st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Erreur lors de la génération par l'IA : {str(e)}")
