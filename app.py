import streamlit as st
import requests
import time
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

st.title("📊 Analyseur & Extracteur de Contenu YouTube (via 1min.ai)")
st.write("Cette version utilise l'API de 1min.ai pour extraire le contenu sans blocage, et Gemini pour le rapport.")

# Sidebar pour les clés API
with st.sidebar:
    st.header("Configuration")
    gemini_key = st.text_input("1. Clé API Google Gemini", type="password", help="Obtenez-la sur Google AI Studio")
    onemin_key = st.text_input("2. Clé API 1min.ai", type="password", help="Récupérez-la sur votre compte 1min.ai")
    st.markdown("---")
    st.caption("Développé avec Streamlit, 1min.ai & Gemini API")

# Champ de saisie
video_url = st.text_input("Entrez l'URL de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

def get_transcript_from_1min(url, api_key):
    # Endpoint standard de 1min.ai
    api_url = "https://api.1min.ai/v1/audio/transcribe" 
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url,
        "language": "fr"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        
        # AJOUT TEMPORAIRE : On affiche la réponse brute pour comprendre le format
        st.subheader("🔍 Mode Diagnostic 1min.ai")
        st.write(f"Code HTTP reçu : {response.status_code}")
        try:
            st.json(response.json()) # Affiche le JSON propre dans l'interface
            data = response.json()
        except:
            st.text(f"Réponse texte brute : {response.text}")
            return None

        # Tentative d'extraction intelligente selon les formats connus de 1min.ai
        if response.status_code in [200, 201]:
            # Format 1: imbriqué dans un objet 'data'
            if "data" in data:
                sub_data = data["data"]
                if isinstance(sub_data, dict):
                    return sub_data.get("transcript") or sub_data.get("text") or sub_data.get("result")
                return str(sub_data)
            
            # Format 2: direct à la racine
            return data.get("transcript") or data.get("text") or data.get("result")
            
    except Exception as e:
        st.error(f"Erreur technique lors de l'appel : {str(e)}")
    return None


if st.button("Analyser la vidéo", type="primary"):
    if not gemini_key or not onemin_key:
        st.warning("Veuillez renseigner vos DEUX clés API dans la barre latérale.")
    elif not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        with st.spinner("1min.ai extrait le contenu de la vidéo (cela peut prendre un instant)..."):
            transcript_text = get_transcript_from_1min(video_url, onemin_key)
        
        if not transcript_text:
            st.error("L'API 1min.ai n'a pas réussi à récupérer ou transcrire cette vidéo. Vérifiez vos crédits ou l'URL.")
        else:
            st.success("🎯 Contenu récupéré par 1min.ai ! Génération du rapport par Gemini...")
            
            try:
                client = genai.Client(api_key=gemini_key)
                
                prompt_text = f"""
                Agis comme un analyste expert. Analyse attentivement la transcription/contenu de la vidéo YouTube suivante et rédige un rapport structuré en français.
                Respecte SCRUPULEUSEMENT le plan suivant :

                ## 📝 Résumé rapide
                *(Rédige ici un résumé très condensé en 2 ou 3 phrases maximum, obligatoirement en italique)*

                ---

                ## ℹ️ Informations
                - **Titre :** (Déduis le titre le plus probable)
                - **Chaîne :** (Identifie l'orateur ou la chaîne si mentionné)
                - **Date :** (Indique l'année ou l'époque si mentionnée)
                - **Durée :** (Estime la durée d'après le texte)
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
                - **📚 Livres :** (Liste des livres ou documents cités. Si aucun, écris "Aucun livre mentionné")
                - **👤 Personnalités :** (Liste des personnes, experts ou figures cités. Si aucune, écris "Aucune personnalité mentionnée")

                Voici le texte de la vidéo à analyser :
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
