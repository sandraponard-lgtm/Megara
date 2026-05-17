import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

st.title("📊 Analyseur & Extracteur de Contenu YouTube")
st.write("Collez une URL YouTube pour générer une analyse complète et officielle grâce aux API Google.")

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

# Fonction officielle pour récupérer les vraies infos de la vidéo
def get_youtube_details(v_id, yt_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={v_id}&key={yt_key}"
    try:
        res = requests.get(url).json()
        if "items" in res and len(res["items"]) > 0:
            item = res["items"][0]
            return {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "date": item["snippet"]["publishedAt"][:10],
                "duration": item["contentDetails"]["duration"].replace("PT", "").lower(),
                "views": item["statistics"].get("viewCount", "Non disponible"),
                "lang": item["snippet"].get("defaultAudioLanguage", "fr")
            }
    except:
        pass
    return None

# Fonction officielle pour récupérer les sous-titres via l'API de transcription YouTube
def get_official_transcript(v_id):
    try:
        # Étape A: Demander la liste des pistes de sous-titres disponibles
        video_info_url = f"https://video.google.com/timedtext?v={v_id}&type=list"
        response = requests.get(video_info_url)
        
        lang_code = "fr"  # Par défaut on cherche du français
        if "lang_code=\"fr\"" not in response.text and "lang_code=\"en\"" in response.text:
            lang_code = "en"  # Repli sur l'anglais si pas de français
            
        # Étape B: Télécharger le fichier XML des sous-titres choisis
        transcript_url = f"https://video.google.com/timedtext?v={v_id}&lang={lang_code}"
        xml_response = requests.get(transcript_url)
        
        # Étape C: Nettoyer le XML pour ne garder que le texte brut
        if xml_response.text:
            root = ET.fromstring(xml_response.text)
            text_lines = [text_node.text for text_node in root.findall('text') if text_node.text]
            return " ".join(text_lines)
    except:
        pass
    return None

if st.button("Analyser la vidéo", type="primary"):
    if not gemini_key or not youtube_key:
        st.warning("Veuillez renseigner vos DEUX clés API dans la barre latérale (Gemini et YouTube).")
    elif not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        video_id = extract_id(video_url)
        if not video_id:
            st.error("Impossible de détecter l'ID de la vidéo.")
        else:
            with st.spinner("Récupération des métadonnées et sous-titres officiels..."):
                details = get_youtube_details(video_id, youtube_key)
                transcript_text = get_official_transcript(video_id)
            
            if not details:
                st.error("Impossible de récupérer les informations de la vidéo. Vérifiez votre clé API YouTube.")
            else:
                # Si pas de sous-titres, on prévient Gemini pour qu'il travaille sur le titre et la description
                if not transcript_text:
                    st.warning("⚠️ Aucun sous-titre textuel trouvé pour cette vidéo. Gemini va analyser la vidéo d'après son titre.")
                    transcript_text = f"Vidéo intitulée '{details['title']}' de la chaîne '{details['channel']}'."

                try:
                    client = genai.Client(api_key=gemini_key)
                    
                    prompt_text = f"""
                    Agis comme un analyste expert. Rédige un rapport d'analyse structuré en français basé sur les informations et la transcription fournies ci-dessous. Respecte SCRUPULEUSEMENT ce plan :

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
                    (Génère une liste structurée et NUMÉROTÉE des concepts essentiels développés dans la vidéo)

                    ---

                    ## 🔢 Chiffres clés
                    (Liste à puces des statistiques, données chiffrées importantes ou métriques mentionnées)

                    ---

                    ## 📌 Références citées
                    - **📚 Livres :** (Liste des livres, ouvrages ou documents cités d'après la transcription. Si aucun, écris "Aucun livre mentionné")
                    - **👤 Personnalités :** (Liste des personnes, auteurs, experts cités. Si aucune, écris "Aucune personnalité mentionnée")

                    Voici le contenu textuel de la vidéo à analyser :
                    {transcript_text}
                    """
                    
                    with st.spinner("Gemini génère votre rapport personnalisé..."):
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt_text
                        )
                    
                    st.markdown("---")
                    st.subheader("🎬 Rapport d'Analyse Vidéo")
                    st.markdown(response.text)
                        
                except Exception as e:
                    st.error(f"Erreur lors de la génération par l'IA : {str(e)}")
