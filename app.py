import streamlit as st
import re
from google import genai
from google.genai import types  # Import indispensable pour injecter la vraie vidéo

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
        # Nettoyage de l'URL pour s'assurer qu'elle est au format standard attendu par Google
        if "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
            clean_url = f"https://www.youtube.com/watch?v={video_id}"
        elif "watch?v=" in video_url:
            video_id = video_url.split("watch?v=")[1].split("&")[0]
            clean_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            clean_url = video_url

        st.success("Connexion à Gemini réussie ! Récupération et analyse de la vraie vidéo en cours...")
        
        try:
            # Initialisation du client Gemini
            client = genai.Client(api_key=api_key)
            
            # Configuration stricte du prompt d'analyse
            prompt_text = """
            Agis comme un analyste expert. Analyse le contenu de la vidéo YouTube fournie (visuel et audio/sous-titres) et rédige un rapport structuré en français.
            
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
            
            # Appel au modèle en passant l'URL comme un fichier multimédia natif
            with st.spinner("Gemini examine la vidéo... Cela peut prendre 15 à 45 secondes selon la durée."):
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=types.Content(
                        parts=[
                            types.Part.from_uri(
                                file_uri=clean_url,
                                mime_type="video/mp4"  # Indique à Gemini qu'il doit traiter l'URL comme une vidéo
                            ),
                            types.Part.from_text(text=prompt_text)
                        ]
                    )
                )
            
            # Affichage des résultats
            st.markdown("---")
            st.subheader("🎬 Résultats de l'Analyse")
            st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Erreur lors de la génération par l'IA : {str(e)}")
