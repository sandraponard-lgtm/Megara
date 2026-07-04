import streamlit as st
import requests
import io
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
    
    /* En-tête ultra-compact */
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

    /* Forcer l'alignement horizontal de l'input et du bouton */
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

# --- PASSERELLE INTEGRATION PCLOUD ---
def save_to_pcloud(filename, content):
    base_url = st.secrets.get("PCLOUD_ENDPOINT", "https://eapi.pcloud.com")
    username = st.secrets.get("PCLOUD_USERNAME", "")
    password = st.secrets.get("PCLOUD_PASSWORD", "")
    
    if not username or not password:
        add_log("⚠️ Configuration pCloud manquante dans les secrets.")
        return False
        
    try:
        file_buffer = io.BytesIO(content.encode('utf-8'))
        file_buffer.name = filename
        
        upload_url = f"{base_url}/uploadfile"
        params = {
            "username": username,
            "password": password,
            "path": "/",
            "nopartial": 1,
            "renameifexists": 1
        }
        
        files = {'file': file_buffer}
        res = requests.post(upload_url, params=params, files=files)
        
        if res.status_code == 200 and res.json().get("result") == 0:
            add_log(f"💾 Historisation réussie sur pCloud : {filename}")
            return True
        else:
            add_log(f"❌ Échec de sauvegarde pCloud : {res.text}")
    except Exception as e:
        add_log(f"❌ Erreur critique lors de la liaison pCloud : {str(e)}")
    return False

# --- LOGIQUE DE PARSING ---
def extract_id(url):
    if not url: return "texte_manuel"
    if "youtu.be/" in url: return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url: return url.split("watch?v=")[1].split("&")[0]
    return "texte_manuel"

def get_official_youtube_details(v_id, yt_key):
    if v_id == "texte_manuel": return None
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
            
            if "resultObject" in data and data["resultObject"]:
                if isinstance(data["resultObject"], list) and len(data["resultObject"]) > 0: return data["resultObject"][0]
                return str(data["resultObject"])

            record_detail = data.get("aiRecordDetail", {})
            if isinstance(record_detail, dict):
                prompt_obj = record_detail.get("promptObject", {})
                if isinstance(prompt_obj, dict) and "prompt" in prompt_obj:
                    raw_text = prompt_obj["prompt"]
                    if "xml data for reference:" in raw_text.lower(): return raw_text.split("```xml")[-1].replace("```", "").strip()
                    return raw_text

            ai_record = data.get("aiRecord", {})
            if isinstance(ai_record, dict):
                inner_detail = ai_record.get("aiRecordDetail", {}) or ai_record
                if isinstance(inner_detail, dict):
                    p_obj = inner_detail.get("promptObject", {})
                    if isinstance(p_obj, dict) and "prompt" in p_obj: return p_obj["prompt"]
                    if "resultObject" in inner_detail:
                        res_obj = inner_detail["resultObject"]
                        if isinstance(res_obj, list) and len(res_obj) > 0: return res_obj[0]
                        return str(res_obj)
    except Exception as e:
        add_log(f"❌ 1min.ai Erreur critique : {str(e)}")
    return None

# --- INTERFACE GRAPHIQUE COMPACTE ---
st.markdown('<h1 class="main-title">Analyseur YouTube</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Résumé, points clés et chiffres extraits en quelques secondes</p>', unsafe_allow_html=True)

col_url, col_btn = st.columns([3, 1])

with col_url:
    video_url = st.text_input("URL DE LA VIDÉO", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")

with col_btn:
    trigger_analyse = st.button("Analyser", type="primary", use_container_width=True)

with st.expander("📝 Option : Coller directement une transcription brute", expanded=False):
    manual_transcript = st.text_area("Colle ton texte ou ta transcription ici", height=150, placeholder="Copie ton texte ici...")

if trigger_analyse:
    if not video_url and not manual_transcript.strip():
        st.warning("Veuillez entrer une URL ou coller une transcription.")
    else:
        st.session_state["debug_logs"] = [] 
        video_id = extract_id(video_url)
        
        yt_key = st.secrets.get("YOUTUBE_API_KEY", "")
        onemin_key = st.secrets.get("ONEMIN_API_KEY", "")
        gemini_key = st.secrets.get("GEMINI_API_KEY", "")
        
        transcript_text = None
        
        if manual_transcript.strip():
            add_log("📝 Source : Utilisation de la transcription manuelle.")
            transcript_text = manual_transcript.strip()
        else:
            add_log(f"🚀 Source : Analyse via URL {video_url}")
            with st.spinner("Transcription..."):
                transcript_text = get_transcript_from_1min(video_url, onemin_key)
        
        if not transcript_text:
            st.error("Impossible d'obtenir un texte à analyser.")
        else:
            details = get_official_youtube_details(video_id, yt_key) if video_id != "texte_manuel" else None
            title_clean = details['title'] if details else "Analyse_Manuelle"
            
            if details:
                meta_prompt_part = f"- **Titre :** {details['title']}\n- **Chaîne :** {details['channel']}\n- **URL :** {video_url}\n- **Date :** {details['date']}\n- **Durée :** {details['duration']}\n- **Vues :** {int(details['views']):,} vues"
            else:
                meta_prompt_part = f"- **Titre :** (Déduis le titre d'après le texte)\n- **Chaîne :** (Déduis la chaîne)\n- **URL :** {video_url if video_url else 'Saisie manuelle'}"

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

                [SECTION 2: RESUME_FLASH]
                Rédige une liste à puces (bullet points) ultra-synthétique contenant entre 4 et 6 points clés essentiels pour comprendre la vidéo en moins de 10 secondes. Chaque point doit être court et percutant.

                ===SECTION_SEPARATOR===

                [SECTION 3: DETAIL]
                Rédige un résumé en profondeur de la vidéo, structurée en plusieurs paragraphes clairs, denses et très détaillés.

                ===SECTION_SEPARATOR===

                [SECTION 4: POINTS_CLES]
                Génère une liste numérotée des concepts essentiels développés.
                Ensuite, crée une sous-section nommée "### 🔢 Chiffres clés par Thématiques". Regroupe obligatoirement TOUTES les statistiques et données chiffrées de la vidéo sous des titres thématiques clairs.

                ===SECTION_SEPARATOR===

                [SECTION 5: CITATIONS_REFERENCES]
                Crée une rubrique "### 💬 Citations fortes". Extrais au moins 3 à 5 citations textuelles marquantes ou phrases clés dites dans la vidéo. Formate ainsi : "« Citation » *(Contexte explicatif)*".
                Ajoute ensuite la liste des Livres et Personnalités mentionnés.

                Transcription :
                {transcript_text}
                """
                
                with st.spinner("Génération du rapport..."):
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_text
                    )
                
                sections = response.text.split("===SECTION_SEPARATOR===")
                
                st.session_state['report_data'] = {
                    "synth": sections[0].strip() if len(sections) > 0 else "",
                    "flash": sections[1].strip() if len(sections) > 1 else "",
                    "detail": sections[2].strip() if len(sections) > 2 else "",
                    "points": sections[3].strip() if len(sections) > 3 else "",
                    "citations": sections[4].strip() if len(sections) > 4 else ""
                }
                
                full_markdown_content = f"# {title_clean}\n\n## 📊 Synthèse & Métadonnées\n{st.session_state['report_data']['synth']}\n\n---\n\n## 📋 Résumé Flash\n{st.session_state['report_data']['flash']}\n\n---\n\n## 📖 Analyse détaillée\n{st.session_state['report_data']['detail']}\n\n---\n\n## 💡 Points clés & Chiffres\n{st.session_state['report_data']['points']}\n\n---\n\n## 💬 Citations & Références\n{st.session_state['report_data']['citations']}\n"
                
                safe_title = "".join([c for c in title_clean if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                filename = f"YT_{video_id}_{safe_title[:30]}.md".replace(" ", "_")
                
                save_to_pcloud(filename, full_markdown_content)
                st.rerun()
                
            except Exception as e:
                add_log(f"❌ Gemini Erreur : {str(e)}")
                st.error(f"Erreur d'analyse IA : {str(e)}")

# --- RENDU DE LA NAVIGATION HORIZONTALE ET DES SECTIONS ---
if 'report_data' in st.session_state:
    data = st.session_state['report_data']
    
    tab_synth, tab_flash, tab_detail, tab_points, tab_cit, tab_export = st.tabs([
        "📊 Synthèse", "⚡ Résumé Flash", "📖 Analyse détaillée", "💡 Points clés", "💬 Citations", "📋 Export & Copie"
    ])
    
    with tab_synth: st.markdown(data["synth"])
    with tab_flash: st.markdown(data["flash"])
    with tab_detail: st.markdown(data["detail"])
    with tab_points: st.markdown(data["points"])
    with tab_cit: st.markdown(data["citations"])
    with tab_export:
        full_md = f"{data['synth']}\n\n---\n\n### ⚡ Résumé Flash\n{data['flash']}\n\n---\n\n{data['detail']}\n\n---\n\n{data['points']}\n\n---\n\n{data['citations']}"
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            st.subheader("📝 Format Markdown brut")
            st.code(full_md, language="markdown")
            
        with col_exp2:
            st.subheader("🎨 Format Texte Riche (Prêt à copier)")
            st.info("Utilise le bouton de copie en haut à droite du bloc pour récupérer le texte pré-formaté proprement (titres gras, puces) pour Word ou Teams.")
            
            # Reconstruction propre et native sans bibliothèque externe
            rich_clean = full_md.replace("### ", "").replace("**", "")
            st.text_area("Texte Formaté", value=rich_clean, height=350)

# --- CONSOLE DE DIAGNOSTIC ---
st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
with st.expander("🛠️ Console de Diagnostic technique (Debug)", expanded=False):
    st.subheader("📜 Logs d'exécution")
    if st.session_state["debug_logs"]:
        st.code("\n".join(st.session_state["debug_logs"]), language="text")
