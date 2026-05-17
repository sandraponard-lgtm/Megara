import streamlit as st
import requests
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

st.title("📊 Analyseur & Extracteur de Contenu YouTube")
st.write("Collez une URL YouTube pour générer une analyse complète basée sur la vraie transcription.")

# Sidebar pour les clés API
with st.sidebar:
    st.header("Configuration")
    gemini_key = st.text_input("1. Clé API Google Gemini", type="password", help="Obtenez-la sur Google AI Studio")
    youtube_key = st.text_input("2. Clé API YouTube Data v3", type="password", help="Obtenez-la sur Google Cloud Console")
    st.markdown("---")
    st.caption("Développé avec Streamlit & Gemini API")

# Champ de saisie
video_url = st.text_input("Entrez l'URL de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

def extract_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    return None

# Récupération des métadonnées officielles via YouTube API
def get_youtube_details(v_id, yt_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={v_id}&key={yt_key}"
    try:
        res = requests.get(url).json()
        if "items" in res and len(res["items"]) > 0:
            item = res["items"][0]
            return {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "description": item["snippet"].get("description", ""),
                "tags": ", ".join(item["snippet"].get("tags", [])),
                "date": item["snippet"]["publishedAt"][:10],
                "duration": item["contentDetails"]["duration"].replace("PT", "").lower(),
                "views": item["statistics"].get("viewCount", "0"),
                "lang": item["snippet"].get("defaultAudioLanguage", "fr")
            }
    except:
        pass
    return None

# Nouvelle fonction de récupération par interception (comme les sites web)
def get_scraped_transcript(v_id):
    try:
        # On utilise un micro-service de scraping public spécialisé dans l'interception de la piste ASR V3 de YouTube
        api_url = f"https://youtubetranscript.com/api/transcripts/{v_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200 and response.text:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            text_lines = [text_node.text for text_node in root.findall('text') if text_node.text]
            if text_lines:
                clean_text = " ".join(text_lines)
                return clean_text.replace("&#39;", "'").replace("&quot;", '"').replace("&amp;", "&")
    except:
        pass
    return None

if st.button("Analyser la vidéo", type="primary"):
    if not gemini_key or not youtube_key:
        st.warning("Veuillez renseigner vos DEUX clés API dans la barre latérale.")
    elif not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        video_id = extract_id(video_url)
        if not video_id:
            st.error("Impossible de détecter l'ID de la vidéo.")
        else:
            with st.spinner("Récupération des données et de la transcription réelle..."):
                details = get_youtube_details(video_id, youtube_key)
                transcript_text = get_scraped_transcript(video_id)
            
            if not details:
                st.error("Impossible de récupérer les informations de la vidéo.")
            else:
                # Indicateur visuel pour savoir si on a bien le texte complet
                if transcript_text:
                    st.success("🎯 Transcription réelle récupérée avec succès !")
                    context_status = "Texte complet extrait de la vidéo"
                else:
                    st.warning("⚠️ Mode de secours activé (analyse par description).")
                    transcript_text = f"Titre: {details['title']}. Description: {details['description']}"
                    context_status = "Description et chapitres uniquement"

                try:
                    client = genai.Client(api_key=gemini_key)
                    
                    prompt_text = f"""
                    Agis comme un analyste expert. Tu dois rédiger un rapport d'analyse structuré en français basé sur les informations et la transcription fournies.
                    
                    Voici les données de la vidéo :
                    - **Titre officiel :** {details['title']}
                    - **Chaîne :** {details['channel']}
                    - **Contenu/Transcription à analyser :** {transcript_text}

                    Respecte SCRUPULEUSEMENT le plan suivant pour ta réponse :

                    ## 📝 Résumé rapide
                    *(Rédige ici un résumé très condensé en 2 ou 3 phrases maximum, obligatoirement en italique)*

                    ---

                    ## ℹ️ Informations
                    - **Titre :** {details['title']}
                    - **Chaîne :** {details['channel']}
                    - **Date :** {details['date']}
                    - **Durée :** {details['duration']}
                    - **Langue :** {details['lang'].upper()}
                    - **Vues :** {int(details['views']):,} (Mets des espaces pour séparer les milliers)

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
                    - **📚 Livres :** (Liste des livres ou documents cités d'après le texte. Si aucun, écris "Aucun livre mentionné")
                    - **👤 Personnalités :** (Liste des personnes, experts ou figures cités. Si aucune, écris "Aucune personnalité mentionnée")
                    """
                    
                    with st.spinner("Gemini génère votre rapport personnalisé..."):
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt_text
                        )
                    
                    st.markdown("---")
                    st.subheader("🎬 Rapport d'Analyse Vidéo")
                    st.caption(f"Source des données : {context_status}")
                    st.markdown(response.text)
                        
                except Exception as e:
                    st.error(f"Erreur lors de la génération par l'IA : {str(e)}")
