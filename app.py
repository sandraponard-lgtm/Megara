import streamlit as st
import requests
import sys
from google import genai

# Configuration de la page
st.set_page_config(page_title="Analyseur YouTube", page_icon="📊", layout="wide")

# --- INJECTION CSS : OPTIMISATION COMPACTE MAXIMALE ---
st.markdown("""
<style>
    /* Thème global */
    .stApp {
        background-color: #0f0f13;
        color: #e2e8f0;
    }
    
    /* En-tête ultra-compact (marge réduite au maximum pour mobile) */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 1.6rem;
        background: linear-gradient(45deg, #a78bfa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: -2.5rem;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 2px;
        margin-bottom: 1rem;
    }

    /* Forcer l'alignement horizontal de l'input et du bouton sur la même ligne */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
    }

    /* Style personnalisé pour les onglets horizontaux natifs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(23, 23, 33, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 6px 12px;
        color: #94a3b8;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- SYSTÈME DE SÉCURITÉ ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.markdown('<h2 style="text-align:center; margin-top:20%;">🔒 Accès Sécurisé</h2>', unsafe_allow_html=True)
    password = st.text_input("Code d'accès :", type="password")
    if st.button("Se connecter", type="primary"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Code d'accès incorrect.")
    return False

if not check_password():
    st.stop()

# --- INITIALISATION DES LOGS ---
if "debug_logs" not in st.session_state:
    st.session_state["debug_logs"] = []

def add_log(message):
    st.session_state["debug_logs"].append(message)

# --- LOGIQUE TECHNIQUE (PASSAGE UNIQUE SÉCURISÉ) ---
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
            add_log("✅ API YouTube : Métadonnées récupérées.")
            return {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "date": f"{day}/{month}/{year}",
                "duration": item["contentDetails"]["duration"].replace("PT", "").lower(),
                "views": item["statistics"].get("viewCount", "0")
            }
    except Exception as e:
        add_log(f"❌ API YouTube Erreur : {str(e)}")
    return None

def get_transcript_from_1min(url, api_key):
    api_url = "https://api.1min.ai/api/features" 
    headers = {"API-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "type": "YOUTUBE_TRANSCRIBER",
        "model": "gpt-4o",
        "conversationId": "YOUTUBE_TRANSCRIBER",
        "promptObject": {"videoUrl": url}
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        add_log(f"📡 1min.ai : HTTP {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            add_log(f"📄 1min.ai JSON (extrait) : {str(data)[:600]}...")
            
            # Niveau 1 : Racine du JSON
            if "resultObject" in data and data["resultObject"]:
                if isinstance(data["resultObject"], list) and len(data["resultObject"]) > 0:
                    return data["resultObject"][0]
                return str(data["resultObject"])

            # Niveau 2 : aiRecordDetail
            record_detail = data.get("aiRecordDetail", {})
            if isinstance(record_detail, dict):
                prompt_obj = record_detail.get("promptObject", {})
                if isinstance(prompt_obj, dict) and "prompt" in prompt_obj:
                    raw_text = prompt_obj["prompt"]
                    if "xml data for reference:" in raw_text.lower():
                        return raw_text.split("```xml")[-1].replace("```", "").strip()
                    return raw_text

            # Niveau 3 : Structure imbriquée dans aiRecord
            ai_record = data.get("aiRecord", {})
            if isinstance(ai_record, dict):
                inner_detail = ai_record.get("aiRecordDetail", {}) or ai_record
                if isinstance(inner_detail, dict):
                    p_obj = inner_detail.get("promptObject", {})
                    if isinstance(p_obj, dict) and "prompt" in p_obj:
                        return p_obj["prompt"]
                    if "resultObject" in inner_detail:
                        res_obj = inner_detail["resultObject"]
                        if isinstance(res_obj, list) and len(res_obj) > 0: return res_obj[0]
                        return str(res_obj)

            add_log("⚠️ Parseur : Donnée introuvable dans la structure JSON.")
    except Exception as e:
        add_log(f"❌ 1min.ai Erreur critique : {str(e)}")
    return None

# --- INTERFACE GRAPHIQUE COMPACTE ---
st.markdown('<h1 class="main-title">Analyseur YouTube</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Résumé, points clés et chiffres extraits en quelques secondes</p>', unsafe_allow_html=True)

# Ligne URL + Bouton alignés
col_url, col_btn = st.columns([3, 1])

with col_url:
    video_url = st.text_input("URL DE LA VIDÉO", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")

with col_btn:
    trigger_analyse = st.button("Analyser", type="primary", use_container_width=True)

# Traitement de l'analyse au clic
if trigger_analyse:
    if not video_url:
        st.warning("Veuillez entrer une URL.")
    else:
        st.session_state["debug_logs"] = [] # Reset logs
        add_log(f"🚀 Lancement de l'analyse : {video_url}")
        
        video_id = extract_id(video_url)
        if not video_id:
            st.error("ID Vidéo YouTube introuvable dans l'URL.")
        else:
            yt_key = st.secrets.get("YOUTUBE_API_KEY", "")
            onemin_key = st.secrets.get("ONEMIN_API_KEY", "")
            gemini_key = st.secrets.get("GEMINI_API_KEY", "")

            with st.spinner("Transcription (1min.ai)..."):
                transcript_text = get_transcript_from_1min(video_url, onemin_key)
            
            if not transcript_text:
                st.error("Impossible de récupérer la transcription. Vérifie la console de diagnostic.")
            else:
                with st.spinner("Métadonnées (YouTube)..."):
                    details = get_official_youtube_details(video_id, yt_key)
                
                if not details:
                    meta_prompt_part = f"- **Titre :** (Déduis-le)\n- **Chaîne :** (Déduis-la)\n- **URL :** {video_url}\n- **Date :** Inconnue"
                else:
                    meta_prompt_part = f"- **Titre :** {details['title']}\n- **Chaîne :** {details['channel']}\n- **URL :** {video_url}\n- **Date :** {details['date']}\n- **Durée :** {details['duration']}\n- **Vues :** {int(details['views']):,} vues"

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
                    
                    with st.spinner("Génération du rapport (Gemini)..."):
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt_text
                        )
                    
                    sections = response.text.split("===SECTION_SEPARATOR===")
                    st.session_state['report_data'] = {
                        "synth": sections[0].strip() if len(sections) > 0 else "",
                        "detail": sections[1].strip() if len(sections) > 1 else "",
                        "points": sections[2].strip() if len(sections) > 2 else "",
                        "citations": sections[3].strip() if len(sections) > 3 else ""
                    }
                    add_log("🤖 Rapport complet généré avec succès par Gemini.")
                    st.rerun()
                    
                except Exception as e:
                    add_log(f"❌ Gemini Erreur : {str(e)}")
                    st.error(f"Erreur d'analyse IA : {str(e)}")

# --- RENDU DE LA NAVIGATION HORIZONTALE ET DES SECTIONS ---
if 'report_data' in st.session_state:
    data = st.session_state['report_data']
    
    tab_synth, tab_detail, tab_points, tab_cit, tab_export = st.tabs([
        "📊 Synthèse", "📖 Analyse détaillée", "💡 Points clés", "💬 Citations", "📋 Export XTile"
    ])
    
    with tab_synth:
        st.markdown(data["synth"])
    with tab_detail:
        st.markdown(data["detail"])
    with tab_points:
        st.markdown(data["points"])
    with tab_cit:
        st.markdown(data["citations"])
    with tab_export:
        st.subheader("📋 Rapport complet au format brut")
        full_markdown = f"{data['synth']}\n\n---\n\n{data['detail']}\n\n---\n\n{data['points']}\n\n---\n\n{data['citations']}"
        st.code(full_markdown, language="markdown")

# --- CONSOLE DE DIAGNOSTIC ---
st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
with st.expander("🛠️ Console de Diagnostic technique (Debug)", expanded=False):
    st.subheader("⚙️ Vérification des Secrets")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1: st.metric("GEMINI_API_KEY", "Présente ✅" if "GEMINI_API_KEY" in st.secrets else "Absente ❌")
    with col_s2: st.metric("ONEMIN_API_KEY", "Présente ✅" if "ONEMIN_API_KEY" in st.secrets else "Absente ❌")
    with col_s3: st.metric("YOUTUBE_API_KEY", "Présente ✅" if "YOUTUBE_API_KEY" in st.secrets else "Absente ❌")
        
    st.subheader("📜 Logs d'exécution")
    if st.session_state["debug_logs"]:
        st.code("\n".join(st.session_state["debug_logs"]), language="text")
    else:
        st.info("Aucun log disponible pour le moment. Lance une analyse.")
