import streamlit as st
import requests
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

st.title("📊 Analyseur & Extracteur de Contenu YouTube (via 1min.ai)")
st.write("Générez une analyse enrichie et exportable d'une vidéo YouTube sans aucun blocage.")

# Sidebar pour les clés API
with st.sidebar:
    st.header("Configuration")
    gemini_key = st.text_input("1. Clé API Google Gemini", type="password", help="Obtenez-la sur Google AI Studio")
    onemin_key = st.text_input("2. Clé API 1min.ai", type="password", help="Récupérez-la sur votre compte 1min.ai")
    st.markdown("---")
    st.caption("Développé avec Streamlit, 1min.ai & Gemini API")

# Champ de saisie
video_url = st.text_input("Entrez l'URL de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

# Fonction officielle de transcription via 1min.ai
def get_transcript_from_1min(url, api_key):
    api_url = "https://api.1min.ai/api/features" 
    headers = {
        "API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "type": "YOUTUBE_TRANSCRIBER",
        "model": "gpt-4o",
        "conversationId": "YOUTUBE_TRANSCRIBER",
        "promptObject": {
            "videoUrl": url
        }
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            if isinstance(data, dict):
                transcript = data.get("result") or data.get("text") or data.get("transcript")
                if transcript:
                    return transcript
                if "data" in data and isinstance(data["data"], dict):
                    return data["data"].get("result") or data["data"].get("text")
            return str(data)
        else:
            st.error(f"Erreur de l'API 1min.ai (Code {response.status_code})")
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
            st.success("🎯 Transcription récupérée ! Génération du rapport enrichi par Gemini...")
            
            try:
                client = genai.Client(api_key=gemini_key)
                
                # Prompt ultra-précis configuré selon vos exigences
                prompt_text = f"""
                Agis comme un analyste expert. Analyse attentivement la transcription textuelle fournie et rédige un rapport d'analyse structuré en français.
                Tu dois obligatoirement déduire le titre, le nom de la chaîne et la date de publication d'après les indices contextuels du texte.

                Informations de contexte :
                - URL source demandée : {video_url}

                Respecte SCRUPULEUSEMENT le plan et le formatage suivant :

                ## 📝 Résumé rapide
                *(Rédige ici un résumé très condensé en 2 ou 3 phrases maximum, obligatoirement en italique)*

                ---

                ## ℹ️ Informations
                - **Titre :** (Analyse le texte et déduis le titre exact ou le sujet principal le plus probable)
                - **Chaîne :** (Identifie précisément le nom du créateur, de l'intervenant ou de la chaîne de publication)
                - **URL :** {video_url}
                - **Date :** (Déduis la date de publication, l'année ou l'époque d'après les propos tenus)
                - **Langue :** Français

                ---

                ## 📖 Résumé détaillé
                (Rédige une analyse en profondeur de la vidéo, structurée en plusieurs paragraphes clairs, denses et détaillés)

                ---

                ## 💡 Points clés
                (Génère une liste structurée et NUMÉROTÉE des concepts essentiels développés)

                ---

                ## 🔢 Chiffres clés
                (Liste à puces des statistiques, données chiffrées importantes ou métriques mentionnées)

                ---

                ## 📌 Références citées
                - **📚 Livres :** (Liste des livres, rapports, œuvres ou documents cités d'après la transcription. Si aucun, écris "Aucun livre mentionné")
                - **👤 Personnalités :** (Pour chaque personne, expert, auteur ou figure historique cité dans le texte, applique STRICTEMENT ce format : 
                * **Nom de la personne** : Brève description de qui elle est, son rôle et sa pertinence par rapport au sujet traité.
                Si aucune personnalité n'est citée, écris "Aucune personnalité mentionnée".)

                Voici la transcription brute à analyser :
                {transcript_text}
                """
                
                with st.spinner("Gemini finalise votre rapport personnalisé..."):
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_text
                    )
                
                # Stockage du résultat dans la session Streamlit pour permettre la copie
                st.session_state['report_result'] = response.text
                
            except Exception as e:
                st.error(f"Erreur lors de la génération par l'IA : {str(e)}")

# Affichage des résultats s'ils existent dans la session
if 'report_result' in st.session_state:
    st.markdown("---")
    st.subheader("🎬 Rapport d'Analyse Vidéo")
    
    # Zone de rendu visuel propre pour la lecture
    st.markdown(st.session_state['report_result'])
    
    st.markdown("---")
    st.subheader("📋 Zone d'exportation rapide")
    st.write("Cliquez sur l'icône de copie en haut à droite du bloc ci-dessous pour ajouter le rapport dans votre presse-papiers et le coller dans votre application (XTile, Obsidian, etc.) :")
    
    # Utilisation d'un bloc de code Streamlit avec bouton de copie natif en 1 clic
    st.code(st.session_state['report_result'], language="markdown")
