import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

# Fonction pour extraire l'ID de la vidéo à partir de l'URL
def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Fonction pour récupérer le texte de la transcription (Version de secours ultra-compatible)
def get_youtube_transcript(video_id):
    try:
        # On récupère la liste des transcriptions disponibles pour la vidéo
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # On essaie d'abord de trouver une version française (manuelle ou automatique)
        try:
            transcript = transcript_list.find_transcript(['fr'])
        except:
            # Si pas de français, on cherche de l'anglais
            transcript = transcript_list.find_transcript(['en'])
            
        # On extrait le texte
        data = transcript.fetch()
        full_text = " ".join([entry['text'] for entry in data])
        return full_text
        
    except Exception as e:
        st.error(f"Impossible de récupérer les sous-titres : {str(e)}")
        return None


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
        video_id = extract_video_id(video_url)
        
        if not video_id:
            st.error("URL YouTube invalide. Vérifiez le format.")
        else:
            with st.spinner("Extraction des sous-titres en cours..."):
                transcript = get_youtube_transcript(video_id)
            
            if transcript:
                st.success("Transcription récupérée avec succès ! Analyse IA en cours...")
                
                try:
                    client = genai.Client(api_key=api_key)
                    
                    prompt = f"""
                    Agis comme un analyste expert. Analyse la transcription textuelle de la vidéo YouTube suivante et rédige un rapport structuré en français.
                    
                    Règles d'or : 
                    - Si la transcription contient des erreurs évidentes liées aux sous-titres automatiques, corrige le sens intelligemment.
                    - Reste strictement fidèle aux propos de la vidéo.

                    Format attendu :
                    
                    ## 📝 Résumé Global
                    (Rédige un résumé condensé et percutant de la vidéo en un ou deux paragraphes maximum)
                    
                    ---
                    
                    ## 💡 Idées Clés & Bullet Points
                    (Liste à puces des concepts essentiels développés dans la vidéo)
                    
                    ---
                    
                    ## 💬 Citations Marquantes
                    (Extraits ou phrases fortes prononcées)
                    
                    ---
                    
                    ## 🔢 Chiffres Clés & Données
                    (Liste des données chiffrées, statistiques, dates ou métriques importantes mentionnées)
                    
                    Transcription à analyser :
                    {transcript}
                    """
                    
                    with st.spinner("L'IA génère vos insights..."):
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt,
                        )
                    
                    st.markdown("---")
                    st.subheader("🎬 Résultats de l'Analyse")
                    st.markdown(response.text)
                    
                    with st.expander("Voir la transcription brute complète"):
                        st.write(transcript)
                        
                except Exception as e:
                    st.error(f"Erreur lors de la génération par l'IA : {str(e)}")
