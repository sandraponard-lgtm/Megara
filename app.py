import streamlit as st
import requests
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

# --- SYSTÈME DE SÉCURITÉ & MOT DE PASSE ---
def check_password():
    """Renvoie True si l'utilisateur a saisi le bon mot de passe stocké dans les secrets."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Formulaire de connexion
    st.center = st.container()
    with st.center:
        st.title("🔒 Accès Sécurisé")
        password = st.text_input("Veuillez entrer le code d'accès pour utiliser l'application :", type="password")
        if st.button("Se connecter", type="primary"):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Code d'accès incorrect.")
    return False

# Si le mot de passe n'est pas bon, on arrête l'exécution ici
if not check_password():
    st.stop()

# --- CODE PRINCIPAL DE L'APPLICATION (ACCÈS AUTORISÉ) ---

st.title("📊 Analyseur & Extracteur de Contenu YouTube")
st.write("Analyse officielle et complète basée sur les métadonnées réelles de YouTube et la transcription de l'IA.")

# Sidebar épurée (les clés sont chargées de manière transparente)
with st.sidebar:
    st.header("Statut de l'application")
    st.success("🔒 Authentification réussie")
    st.caption("Données sécurisées via Streamlit Secrets")
    st.markdown("---")
    if st.button("Se déconnecter"):
        st.session_state["password_correct"] = False
        st.rerun()

# Champ de saisie unique
video_url = st.text_input("Entrez l'URL de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

def extract_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    return None

# Récupération des VRAIES métadonnées officielles (Titre, Chaîne, Date, Vues) via YouTube Data API
def get_official_youtube_details(v_id, yt_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={v_id}&key={yt_key}"
    try:
        res = requests.get(url).json()
        if "items" in res and len(res["items"]) > 0:
            item = res["items"][0]
            # Formatage de la date en JJ/MM/AAAA
            raw_date = item["snippet"]["publishedAt"][:10]  # AAAA-MM-JJ
            year, month, day = raw_date.split("-")
            clean_date = f"{day}/{month}/{year}"
            
            return {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "date": clean_date,
                "duration": item["contentDetails"]["duration"].replace("PT", "").lower(),
                "views": item["statistics"].get("viewCount", "0"),
                "lang": item["snippet"].get("defaultAudioLanguage", "FR").upper()
            }
    except Exception as e:
        pass
    return None

# Extraction de la transcription via 1min.ai
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
        "promptObject": {"videoUrl": url}
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            if isinstance(data, dict):
                transcript = data.get("result") or data.get("text") or data.get("transcript")
                if transcript: return transcript
                if "data" in data and isinstance(data["data"], dict):
                    return data["data"].get("result") or data["data"].get("text")
    except:
        pass
    return None

if st.button("Lancer l'analyse complète", type="primary"):
    if not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        video_id = extract_id(video_url)
        if not video_id:
            st.error("Impossible de détecter l'ID de la vidéo.")
        else:
            # Récupération sécurisée des clés depuis les secrets d'infrastructure
            gemini_key = st.secrets["GEMINI_API_KEY"]
            onemin_key = st.secrets["ONEMIN_API_KEY"]
            youtube_key = st.secrets["YOUTUBE_API_KEY"]
            
            with st.spinner("Étape 1/2 : Récupération des métadonnées officielles YouTube..."):
                details = get_official_youtube_details(video_id, youtube_key)
                
            with st.spinner("Étape 2/2 : Extraction du texte de la vidéo via 1min.ai..."):
                transcript_text = get_transcript_from_1min(video_url, onemin_key)
            
            if not details:
                st.error("Erreur d'authentification YouTube. Vérifiez 'YOUTUBE_API_KEY' dans vos Secrets Streamlit.")
            elif not transcript_text:
                st.error("1min.ai n'a pas pu extraire le texte. Vérifiez vos crédits ou votre clé 'ONEMIN_API_KEY'.")
            else:
                st.success("🎯 Métadonnées et transcription récupérées ! Génération du rapport structuré...")
                
                try:
                    client = genai.Client(api_key=gemini_key)
                    
                    prompt_text = f"""
                    Agis comme un analyste expert. Analyse attentivement la transcription textuelle fournie et rédige un rapport d'analyse structuré en français en te basant sur les données officielles transmises.

                    Respecte SCRUPULEUSEMENT le plan et le formatage suivant :

                    ## 📝 Résumé rapide
                    *(Rédige ici un résumé très condensé en 2 ou 3 phrases maximum, obligatoirement en italique)*

                    ---

                    ## ℹ️ Informations
                    - **Titre :** {details['title']}
                    - **Chaîne :** {details['channel']}
                    - **URL :** {video_url}
                    - **Date de publication :** {details['date']}
                    - **Durée :** {details['duration']}
                    - **Langue :** {details['lang']}
                    - **Vues :** {int(details['views']):,} (Mets des espaces pour séparer les milliers)

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
                    - **📚 Livres :** (Liste des livres, rapports ou documents cités d'après la transcription. Si aucun, écris "Aucun livre mentionné")
                    - **👤 Personnalités :** (Pour chaque personne, expert ou auteur cité dans le texte, applique STRICTEMENT ce format : 
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
                    
                    st.session_state['report_result'] = response.text
                    
                except Exception as e:
                    st.error(f"Erreur lors de la génération par l'IA : {str(e)}")

# Affichage des résultats et zone de copie rapide
if 'report_result' in st.session_state:
    st.markdown("---")
    st.subheader("🎬 Rapport d'Analyse Vidéo")
    st.markdown(st.session_state['report_result'])
    
    st.markdown("---")
    st.subheader("📋 Zone d'exportation rapide")
    st.write("Cliquez sur l'icône de copie en haut à droite du bloc pour l'ajouter dans XTile :")
    st.code(st.session_state['report_result'], language="markdown")
