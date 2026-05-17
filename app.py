import streamlit as st
import requests
import time
import sys
from google import genai

# Configuration de la page avec thème sombre natif forcé via le design
st.set_page_config(page_title="Analyseur YouTube", page_icon="📊", layout="wide")

# --- INJECTION CSS POUR INTERFACE MODERNE ET TABS FIXES ---
st.markdown("""
<style>
    /* Style global et arrière-plan sombre */
    .stApp {
        background-color: #0f0f13;
        color: #e2e8f0;
    }
    
    /* Titre moderne effet dégradé */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        background: linear-gradient(45deg, #a78bfa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 3rem;
    }

    /* Container style Glassmorphism */
    .glass-card {
        background: rgba(23, 23, 33, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 2.5rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 2rem;
    }

    /* Barre d'onglets FIXE en haut de la page lors du scroll */
    .fixed-nav {
        position: fixed;
        top: 2.85rem;
        left: 0;
        right: 0;
        background: rgba(15, 15, 19, 0.95);
        backdrop-filter: blur(8px);
        z-index: 9999;
        display: flex;
        justify-content: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding: 0.5rem 0;
    }
    
    /* Espacement pour éviter que le contenu passe sous la barre fixe */
    .scroll-padding {
        padding-top: 4rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SYSTÈME DE SÉCURITÉ ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.markdown('<div class="glass-card" style="max-width:500px; margin: 10% auto;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center;">🔒 Accès Sécurisé</h2>', unsafe_allow_html=True)
    password = st.text_input("Code d'accès :", type="password")
    if st.button("Se connecter", type="primary"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Code d'accès incorrect.")
    st.markdown('</div>', unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()

# --- INITIALISATION DES ÉTATS ET DU BUFFER DE DEBUG ---
if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = "📊 Synthèse"
if "debug_logs" not in st.session_state:
    st.session_state["debug_logs"] = []

def add_log(message):
    st.session_state["debug_logs"].append(message)

# --- LOGIQUE D'EXTRACTION ---
def extract_id(url):
    if "youtu.be/" in url: return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url: return url.split("watch?v=")[1].split("&")[0]
    return None

def get_official_youtube_details(v_id, yt_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={v_id}&key={yt_key}"
    try:
        res = requests.get(url).json()
        if "items" in res and len(res["items"]) > 0:
            item = res["items"][0]
            raw_date = item["snippet"]["publishedAt"][:10]
            year, month, day = raw_date.split("-")
            add_log("✅ API YouTube : Métadonnées récupérées avec succès.")
            return {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "date": f"{day}/{month}/{year}",
                "duration": item["contentDetails"]["duration"].replace("PT", "").lower(),
                "views": item["statistics"].get("viewCount", "0"),
                "lang": item["snippet"].get("defaultAudioLanguage", "FR").upper()
            }
        else:
            add_log(f"⚠️ API YouTube : Réponse vide ou structure incorrecte.")
    except Exception as e:
        add_log(f"❌ API YouTube Erreur : {str(e)}")
    return None

# Extraction robuste : 1 seul POST payant, puis bouclage de vérification en GET (Gratuit)
def get_transcript_from_1min(url, api_key):
    api_url_base = "https://api.1min.ai/api/features" 
    headers = {"API-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "type": "YOUTUBE_TRANSCRIBER",
        "model": "gpt-4o",
        "conversationId": "YOUTUBE_TRANSCRIBER",
        "promptObject": {"videoUrl": url}
    }
    try:
        # 1. UNIQUE Requête POST (Lancement de la tâche - Débit de crédit unique)
        response = requests.post(api_url_base, json=payload, headers=headers)
        add_log(f"📡 1min.ai (POST Initial) : HTTP {response.status_code}")
        if response.status_code not in [200, 201]:
            return None
            
        data = response.json()
        
        # Extraction de l'UUID pour le suivi gratuit
        task_uuid = data.get("aiRecord", {}).get("uuid")
        if not task_uuid:
            add_log("❌ Impossible de récupérer l'UUID de la tâche dans la réponse initiale.")
            return None
            
        add_log(f"🆔 Tâche 1min.ai enregistrée. UUID: {task_uuid}")

        # 2. Boucle de vérification en mode GET (Vérification de statut gratuite, sans surcoût)
        # On tente de rafraîchir le statut toutes les 4 secondes, max 12 fois (48s max)
        status_url = f"https://api.1min.ai/api/features/{task_uuid}"
        
        for attempt in range(12):
            add_log(f"🔄 Vérification du statut (Essai {attempt + 1}/12)...")
            
            # Extraction des données si elles sont déjà présentes dans l'état actuel
            if isinstance(data, dict):
                # Cas 1 : Le texte est prêt (SUCCESS)
                if data.get("aiRecord", {}).get("status") == "SUCCESS" or "resultObject" in data:
                    if "aiRecordDetail" in data and isinstance(data["aiRecordDetail"], dict):
                        prompt_obj = data["aiRecordDetail"].get("promptObject", {})
                        if isinstance(prompt_obj, dict) and "prompt" in prompt_obj:
                            raw_text = prompt_obj["prompt"]
                            if "xml data for reference:" in raw_text.lower():
                                return raw_text.split("```xml")[-1].replace("```", "").strip()
                            return raw_text
                    
                    if "resultObject" in data and isinstance(data["resultObject"], list) and len(data["resultObject"]) > 0:
                        return data["resultObject"][0]
                
                # Cas 2 : Toujours en traitement, ou structure de départ incomplète
                add_log(f"⏳ Statut actuel : {data.get('aiRecord', {}).get('status', 'PROCESSING')}. En attente...")
            
            # Attendre avant d'interroger à nouveau l'état (GET gratuit)
            time.sleep(4)
            refresh_res = requests.get(status_url, headers={"API-KEY": api_key})
            if refresh_res.status_code == 200:
                data = refresh_res.json()
            else:
                add_log(f"⚠️ Échec du rafraîchissement GET : HTTP {refresh_res.status_code}")
                
        add_log("❌ Temps d'attente maximum dépassé pour la transcription 1min.ai.")
    except Exception as e:
        add_log(f"❌ 1min.ai Erreur critique : {str(e)}")
    return None

# --- NAVIGATION INTERNE (TABS FIXES) ---
if 'report_data' in st.session_state:
    cols = st.columns(5)
    tabs_list = ["📊 Synthèse", "📖 Analyse détaillée", "💡 Points clés", "💬 Citations", "📋 Export XTile"]
    
    st.markdown('<div class="fixed-nav">', unsafe_allow_html=True)
    for i, tab_name in enumerate(tabs_list):
        with cols[i]:
            is_active = st.session_state["current_tab"] == tab_name
            if st.button(tab_name, key=f"nav_{tab_name}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state["current_tab"] = tab_name
                st.rerun()
    st.markdown('</div><div class="scroll-padding"></div>', unsafe_allow_html=True)

# --- INTERFACE VISUELLE ---
st.markdown('<h1 class="main-title">Analyseur YouTube</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Résumé, points clés, chiffres et références extraits en quelques secondes</p>', unsafe_allow_html=True)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
video_url = st.text_input("URL DE LA VIDÉO", placeholder="https://www.youtube.com/watch?v=...")
st.markdown('</div>', unsafe_allow_html=True)

if st.button("Lancer l'analyse complète", type="primary"):
    if not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        st.session_state["debug_logs"] = [] 
        add_log(f"🚀 Nouvelle analyse demandée pour l'URL : {video_url}")
        
        video_id = extract_id(video_url)
        add_log(f"🆔 ID vidéo extrait : {video_id}")
        
        if not video_id:
            st.error("ID Vidéo introuvable.")
        else:
            yt_key = st.secrets.get("YOUTUBE_API_KEY", "")
            onemin_key = st.secrets.get("ONEMIN_API_KEY", "")
            gemini_key = st.secrets.get("GEMINI_API_KEY", "")

            with st.spinner("Extraction et génération de la transcription (Patientez pendant le traitement initial)..."):
                transcript_text = get_transcript_from_1min(video_url, onemin_key)
            
            if not transcript_text:
                st.error("Erreur : Impossible d'obtenir la transcription. Relancez l'analyse dans quelques secondes, le traitement est peut-être en train de finir chez 1min.ai.")
            else:
                add_log(f"📝 Transcription récupérée avec succès ({len(transcript_text)} caractères)")
                with st.spinner("Récupération des métadonnées YouTube..."):
                    details = get_official_youtube_details(video_id, yt_key)
                
                if not details:
                    meta_prompt_part = f"""
                    - **Titre :** (Déduis le titre le plus probable d'après le texte)
                    - **Chaîne :** (Déduis le nom de la chaîne ou du locuteur principal d'après le texte)
                    - **URL :** {video_url}
                    - **Date :** (Déduis l'année ou la date si mentionnée, sinon indique 'Inconnue')
                    - **Vues :** Donnée indisponible
                    """
                else:
                    meta_prompt_part = f"""
                    - **Titre :** {details['title']}
                    - **Chaîne :** {details['channel']}
                    - **URL :** {video_url}
                    - **Date :** {details['date']}
                    - **Durée :** {details['duration']}
                    - **Vues :** {int(details['views']):,} vues
                    """

                try:
                    client = genai.Client(api_key=gemini_key)
                    
                    prompt_text = f"""
                    Analyse la transcription de cette vidéo YouTube et génère des blocs de données structurés en français selon les instructions exactes suivantes.
                    Ne mets aucun blabla d'introduction ou de conclusion. Sépare STRICTEMENT chaque grande section par la chaîne de caractères "===SECTION_SEPARATOR===".

                    [SECTION 1: SYNTHESE]
                    Rédige un résumé rapide en 2 ou 3 phrases maximum, obligatoirement en italique.
                    Ajoute ensuite les métadonnées exactement sous cette forme de liste :
                    {meta_prompt_part}

                    ===SECTION_SEPARATOR===

                    [SECTION 2: DETAIL]
                    Rédige un résumé en profondeur de la vidéo, structurée en plusieurs paragraphes clairs, denses et très détaillés.

                    ===SECTION_SEPARATOR===

                    [SECTION 3: POINTS_CLES]
                    Génère une liste numérotée des concepts essentiels développés.
                    Ensuite, crée une sous-section nommée "### 🔢 Chiffres clés par Thématiques". Regroupe obligatoirement TOUTES les statistiques et données chiffrées de la vidéo sous des titres thématiques clairs (ex: ### Économie, ### Données démographiques, etc.).

                    ===SECTION_SEPARATOR===

                    [SECTION 4: CITATIONS_REFERENCES]
                    Crée une rubrique "### 💬 Citations fortes". Extrais au moins 3 à 5 citations textuelles marquantes ou phrases clés dites dans la vidéo. Pour chaque citation, ajoute obligatoirement entre parenthèses juste après une explication du contexte ou de ce qu'elle implique. Formate ainsi : "« Citation » *(Contexte explicatif)*".
                    Ajoute ensuite la liste des Livres et Personnalités (avec brève description de qui ils sont).

                    Transcription :
                    {transcript_text}
                    """
                    
                    with st.spinner("Gemini génère le rapport d'analyse..."):
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt_text
                        )
                    
                    add_log("🤖 API Gemini : Réponse générée.")
                    sections = response.text.split("===SECTION_SEPARATOR===")
                    st.session_state['report_data'] = {
                        "synth": sections[0].strip() if len(sections) > 0 else "",
                        "detail": sections[1].strip() if len(sections) > 1 else "",
                        "points": sections[2].strip() if len(sections) > 2 else "",
                        "citations": sections[3].strip() if len(sections) > 3 else ""
                    }
                    st.session_state["current_tab"] = "📊 Synthèse"
                    st.rerun()
                    
                except Exception as e:
                    add_log(f"❌ Gemini Erreur : {str(e)}")
                    st.error(f"Erreur d'analyse IA : {str(e)}")

# --- RENDU DE L'ONGLET SÉLECTIONNÉ ---
if 'report_data' in st.session_state:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    active = st.session_state["current_tab"]
    data = st.session_state['report_data']
    
    if active == "📊 Synthèse":
        st.markdown(data["synth"])
    elif active == "📖 Analyse détaillée":
        st.markdown(data["detail"])
    elif active == "💡 Points clés":
        st.markdown(data["points"])
    elif active == "💬 Citations":
        st.markdown(data["citations"])
    elif active == "📋 Export XTile":
        st.subheader("📋 Copie brute du rapport complet")
        full_markdown = f"{data['synth']}\n\n---\n\n{data['detail']}\n\n---\n\n{data['points']}\n\n---\n\n{data['citations']}"
        st.code(full_markdown, language="markdown")
        
    st.markdown('</div>', unsafe_allow_html=True)

# --- ZONE DE DEBUG DYNAMIQUE EN BAS DE PAGE ---
st.markdown("<br><br><hr style='border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
with st.expander("🛠️ Console de Diagnostic technique (Debug)", expanded=False):
    st.subheader("⚙️ État des Secrets & de l'Environnement")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1: st.metric("GEMINI_API_KEY", "Présente ✅" if "GEMINI_API_KEY" in st.secrets else "Absente ❌")
    with col_s2: st.metric("ONEMIN_API_KEY", "Présente ✅" if "ONEMIN_API_KEY" in st.secrets else "Absente ❌")
    with col_s3: st.metric("YOUTUBE_API_KEY", "Présente ✅" if "YOUTUBE_API_KEY" in st.secrets else "Absente ❌")
        
    st.markdown(f"**Version Python :** `{sys.version.split()[0]}` | **Version Streamlit :** `{st.__version__}`")
    st.subheader("📜 Logs d'exécution de la dernière action")
    if st.session_state["debug_logs"]:
        st.code("\n".join(st.session_state["debug_logs"]), language="text")
    else:
        st.info("Aucun log disponible.")
