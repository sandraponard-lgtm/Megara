import streamlit as st
import requests
import time
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

st.title("📊 Analyseur & Extracteur de Contenu YouTube (via 1min.ai)")
st.write("Cette version utilise l'API officielle de 1min.ai pour extraire le texte, puis Gemini pour structurer le rapport.")

# Sidebar pour les clés API
with st.sidebar:
    st.header("Configuration")
    gemini_key = st.text_input("1. Clé API Google Gemini", type="password", help="Obtenez-la sur Google AI Studio")
    onemin_key = st.text_input("2. Clé API 1min.ai", type="password", help="Récupérez-la sur votre compte 1min.ai")
    st.markdown("---")
    st.caption("Développé avec Streamlit, 1min.ai & Gemini API")

# Champ de saisie
video_url = st.text_input("Entrez l'URL de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

# Fonction officielle adaptée à la documentation 1min.ai
def get_transcript_from_1min(url, api_key):
    # Route unique de l'API Feature de 1min.ai
    api_url = "https://api.1min.ai/api/features" 
    
    # Headers obligatoires selon leur doc
    headers = {
        "API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    # Payload strict demandé par le module YOUTUBE_TRANSCRIBER
    payload = {
        "type": "YOUTUBE_TRANSCRIBER",
        "model": "gpt-4o",  # Modèle d'extraction par défaut de leur côté
        "conversationId": "YOUTUBE_TRANSCRIBER",
        "promptObject": {
            "videoUrl": url
        }
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            # 1min.ai renvoie souvent un statut immédiat ou le résultat direct dans une clé text/result
            if isinstance(data, dict):
                # Extraction du texte selon la structure de leur réponse
                transcript = data.get("result") or data.get("text") or data.get("transcript")
                if transcript:
                    return transcript
                # Si imbriqué dans un sous-objet 'data'
                if "data" in data and isinstance(data["data"], dict):
                    return data["data"].get("result") or data["data"].get("text")
            return str(data)
        else:
            st.error(f"Erreur de l'API 1min.ai (Code {response.status_code}) : {response.text}")
    except Exception as e:
        st.error(f"Erreur technique lors de l'appel : {str(e)}")
    return None

if st.button("Analyser la vidéo", type="primary"):
    if not gemini_key or not onemin_key:
        st.warning("Veuillez renseigner vos DEUX clés API dans la barre latérale.")
    elif not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        with st.spinner("1min.ai extrait le contenu de la vidéo... Cela peut prendre 15 à 45 secondes."):
            transcript_text = get_transcript_from_1min(video_url, onemin_key)
        
        if not transcript_text:
            st.error("Impossible de récupérer la transcription de la vidéo via 1min.ai.")
        else:
            st.success("🎯 Transcription récupérée avec succès par 1min.ai ! Génération du rapport par Gemini...")
            
            try:
                client = genai.Client(api_key=gemini_key)
                
                prompt_text = f"""
                Agis comme un analyste expert. Analyse attentivement la transcription textuelle de la vidéo YouTube fournie ci-dessous et rédige un rapport structuré en français.
                Respecte SCRUPULEUSEMENT le plan suivant :

                ## 📝 Résumé rapide
                *(Rédige ici un résumé très condensé en 2 ou 3 phrases maximum, obligatoirement en italique)*

                ---

                ## ℹ️ Informations
                - **Titre :** (Déduis le titre exact ou probable de la vidéo d'après le contexte)
                - **Chaîne :** (Identifie l'orateur ou la chaîne d'après le texte)
                - **Date :** (La date ou l'époque estimée d'après les propos)
                - **Durée :** (Estime la durée ou indique "Non calculé")
                - **Langue :** Français
                - **Vues :** Non extrait

                ---

                ## 📖 Résumé détaillé
                (Rédige une analyse en profondeur de la vidéo, structurée en plusieurs paragraphes clairs et détaillés)

                ---

                ## 💡 Points clés
                (Génère une liste structurée et NUMÉROTÉE des concepts essentiels développés)

                ---

                ## 🔢 Chiffres clés
                (Liste à puces des statistiques, données chiffrées importantes ou métriques mentionnées)

                ---

                ## 📌 Références citées
                - **📚 Livres :** (Liste des livres, ouvrages ou documents cités d'après la transcription. Si aucun, écris "Aucun livre mentionné")
                - **👤 Personnalités :** (Liste des personnes, auteurs, experts ou figures historiques cités. Si aucune, écris "Aucune personnalité mentionnée")

                Voici le contenu de la vidéo extrait par 1min.ai à analyser :
                {transcript_text}
                """
                
                with st.spinner("Gemini finalise votre rapport personnalisé..."):
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_text
                    )
                
                st.markdown("---")
                st.subheader("🎬 Rapport d'Analyse Vidéo")
                st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"Erreur lors de la génération par l'IA : {str(e)}")
