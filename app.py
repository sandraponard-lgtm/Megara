import streamlit as st
import requests
import io
import sys
import re
from google import genai

# Configuration de la page
st.set_page_config(page_title="Analyseur YouTube", page_icon="📊", layout="wide")

# --- INJECTION CSS : GLASSMORPHISM & OPTIMISATION MOBILE ---
st.markdown("""
<style>
    /* Thème global et arrière-plan immersif */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #09090b);
        color: #f4f4f5;
    }
    
    /* En-tête ultra-condensé et discret */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.2rem;
        background: linear-gradient(90deg, #c084fc, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: -3.5rem;
        margin-bottom: 8px;
        text-align: left;
    }

    /* Suppression des marges Streamlit pour compacter l'affichage */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    div[data-testid="stForm"], .stTextInput, .stTextArea, .stButton {
        margin-bottom: 6px !important;
    }

    /* Style des conteneurs en Glassmorphism pur */
    .glass-card {
        background: rgba(23, 23, 37, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
    }

    /* Alignement horizontal compact */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
        gap: 6px !important;
    }

    /* Onglets de consultation style Glassmorphism */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        margin-top: 10px;
        background: rgba(255, 255, 255, 0.03);
        padding: 4px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        border-radius: 6px;
        padding: 6px 10px;
        color: #a1a1aa;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255, 75, 75, 0.2) !important;
        border: 1px solid rgba(255, 75, 75, 0.4) !important;
        color: #ffffff !important;
        backdrop-filter: blur(4px);
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

# --- CONVERTISSEUR LIGHT MARKDOWN -> HTML PROPRE ---
def md_to_clean_html(text):
    if not text: return ""
    
    text = re.sub(r'^\[SECTION\s*\d+\s*:.*?\]\s*\n?', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'\[SECTION.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'#+\s*.*?(Synthèse|Résumé Flash|Analyse détaillée|Points clés|Citations).*?\n', '', text, flags=re.IGNORECASE)

    lines = text.split('\n')
    html_output = []
    in_list = False
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            if in_list:
                html_output.append("</ul>\n")
                in_list = False
            continue
            
        if line_str.startswith('#'):
            if in_list:
                html_output.append("</ul>\n")
                in_list = False
            title_text = line_str.lstrip('#').strip()
            html_output.append(f"<h3 style='color: #c084fc; margin-top: 12px; margin-bottom: 4px; font-size:1.05rem;'>{title_text}</h3>\n")
            continue
            
        if line_str.startswith('- ') or line_str.startswith('* ') or line_str.startswith('• '):
            if not in_list:
                html_output.append("<ul style='margin-top: 2px; margin-bottom: 2px; padding-left: 16px;'>\n")
                in_true = True
                in_list = True
            bullet_content = re.sub(r'^[-*•]\s*', '', line_str)
            bullet_content = re.sub(r'\*\*(.*?)\*\*|\_\_(.*?)\_\_', r'<b>\1\2</b>', bullet_content)
            html_output.append(f"<li style='margin-bottom: 2px; font-size:0.9rem;'>{bullet_content}</li>\n")
            continue
            
        if in_list:
            html_output.append("</ul>\n")
            in_list = False
            
        line_str = re.sub(r'\*\*(.*?)\*\*|\_\_(.*?)\_\_', r'<b>\1\2</b>', line_str)
        line_str = re.sub(r'\*(.*?)\*|\_(.*?)\_', r'<i>\1\2</i>', line_str)
        html_output.append(f"<p style='margin-top: 2px; margin-bottom: 2px; line-height: 1.35; font-size:0.9rem;'>{line_str}</p>\n")
        
    if in_list:
        html_output.append("</ul>\n")
        
    return "".join(html_output)

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
            return {
                "title": item["snippet"]["title"], "channel": item["snippet"]["channelTitle"],
                "date": f"{day}/{month}/{year}", "duration": item["contentDetails"]["duration"].replace("PT", "").lower(),
                "views": item["statistics"].get("viewCount", "0")
            }
    except:
        return None

def get_transcript_from_1min(url, api_key):
    api_url = "https://api.1min.ai/api/features" 
    headers = {"API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"type": "YOUTUBE_TRANSCRIBER", "model": "gpt-4o", "conversationId": "YOUTUBE_TRANSCRIBER", "promptObject": {"videoUrl": url}}
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            if "resultObject" in data and data["resultObject"]:
                if isinstance(data["resultObject"], list) and len(data["resultObject"]) > 0: return data["resultObject"][0]
                return str(data["resultObject"])
    except:
        return None

# --- INTERFACE DESIGN COMPACTE ---
st.markdown('<h1 class="main-title">📊 Analyseur YouTube</h1>', unsafe_allow_html=True)

# Zone d'inputs groupée dans une carte Glassmorphism unique et ouverte
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
col_url, col_btn = st.columns([2.8, 1.2])
with col_url:
    video_url = st.text_input("URL", placeholder="Lien YouTube...", label_visibility="collapsed")
with col_btn:
    trigger_analyse = st.button("Analyser", type="primary", use_container_width=True)

# Saisie manuelle directement ouverte (sans collapse / expander)
manual_transcript = st.text_area("Saisie manuelle (Texte ou Transcription brute)", placeholder="Ou colle un texte / transcription directement ici...", height=90)
st.markdown('</div>', unsafe_allow_html=True)

if trigger_analyse:
    if not video_url and not manual_transcript.strip():
        st.warning("Veuillez entrer une URL ou coller une transcription.")
    else:
        video_id = extract_id(video_url)
        yt_key = st.secrets.get("YOUTUBE_API_KEY", "")
        onemin_key = st.secrets.get("ONEMIN_API_KEY", "")
        gemini_key = st.secrets.get("GEMINI_API_KEY", "")
        
        transcript_text = manual_transcript.strip() if manual_transcript.strip() else get_transcript_from_1min(video_url, onemin_key)
        
        if not transcript_text:
            st.error("Impossible d'obtenir un texte à analyser.")
        else:
            client = genai.Client(api_key=gemini_key)
            
            details = get_official_youtube_details(video_id, yt_key) if video_id != "texte_manuel" else None
            if details:
                title_clean = details['title']
                meta_part = f"- **Titre :** {details['title']}\n- **Chaîne :** {details['channel']}\n- **URL :** {video_url}"
            else:
                with st.spinner("Génération du titre..."):
                    try:
                        title_prompt = f"Génère uniquement un titre court, percutant et sans guillemets (maximum 8 mots) pour résumer ce texte :\n\n{transcript_text[:2000]}"
                        title_res = client.models.generate_content(model='gemini-2.5-flash', contents=title_prompt)
                        title_clean = title_res.text.strip().replace('"', '')
                    except:
                        title_clean = "Analyse de Texte Saisie"
                meta_part = f"- **Titre :** {title_clean}\n- **Source :** Saisie manuelle directe"

            try:
                prompt_text = f"Analyse cette transcription et sépare strictement chaque bloc par le délimiteur '===SECTION_SEPARATOR==='.\nNe répète pas le délimiteur à l'intérieur des blocs.\n\n[SECTION 1: SYNTHESE]\nRésumé global en 2 phrases italiques.\n{meta_part}\n===SECTION_SEPARATOR===\n[SECTION 2: RESUME_FLASH]\n4 à 6 puces percutantes.\n===SECTION_SEPARATOR===\n[SECTION 3: DETAIL]\nRésumé dense structuré en paragraphes.\n===SECTION_SEPARATOR===\n[SECTION 4: POINTS_CLES]\nListe des chiffres clés et concepts importants.\n===SECTION_SEPARATOR===\n[SECTION 5: CITATIONS]\nCitations fortes ou points saillants.\n\nTranscription:\n{transcript_text}"
                
                with st.spinner("Analyse du contenu..."):
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_text)
                
                raw_sections = response.text.split("===SECTION_SEPARATOR===")
                sections = [s.strip() for s in raw_sections if s.strip()]
                
                while len(sections) < 5:
                    sections.append("")
                
                st.session_state['report_data'] = {
                    "synth": sections[0], "flash": sections[1], "detail": sections[2], "points": sections[3], "citations": sections[4]
                }
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la génération : {str(e)}")

# --- BOUTON DE COPIE IMMÉDIAT & CONSULTATION ---
if 'report_data' in st.session_state:
    data = st.session_state['report_data']
    
    html_synth = md_to_clean_html(data['synth'])
    html_flash = md_to_clean_html(data['flash'])
    html_detail = md_to_clean_html(data['detail'])
    html_points = md_to_clean_html(data['points'])
    html_citations = md_to_clean_html(data['citations'])
    
    final_rich_html = (
        f"<h2>📊 SYNTHÈSE</h2>\n{html_synth}<br>\n\n"
        f"<h2>⚡ RÉSUMÉ FLASH</h2>\n{html_flash}<br>\n\n"
        f"<h2>📖 ANALYSE DÉTAILLÉE</h2>\n{html_detail}<br>\n\n"
        f"<h2>💡 POINTS CLÉS & CHIFFRES</h2>\n{html_points}<br>\n\n"
        f"<h2>💬 CITATIONS & RÉFÉRENCES</h2>\n{html_citations}"
    )
    
    escaped_html = final_rich_html.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
    
    # Injection du script de copie en mode Glassmorphism épuré
    js_copier_code = f"""
    <div style="text-align: center; margin-top: 4px; margin-bottom: 4px;">
        <button onclick="copyToClipboard()" style="
            background: linear-gradient(135deg, rgba(255, 75, 75, 0.9), rgba(220, 38, 38, 0.9));
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 10px 20px;
            font-weight: bold;
            font-size: 0.95rem;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            box-shadow: 0px 4px 12px rgba(255, 75, 75, 0.2);
            backdrop-filter: blur(4px);
        ">📋 COPIER LE RAPPORT EN UN CLIC</button>
    </div>

    <script>
    function copyToClipboard() {{
        const htmlData = "{escaped_html}";
        const blobHtml = new Blob([htmlData], {{ type: 'text/html' }});
        
        const div = document.createElement('div');
        div.innerHTML = htmlData.replace(/<br\s*\\/?>/gi, '\\n').replace(/<\/p>/gi, '\\n').replace(/<\/li>/gi, '\\n');
        const plainText = div.textContent || div.innerText || "";
        const blobText = new Blob([plainText], {{ type: 'text/plain' }});
        
        const item = new ClipboardItem({{
            'text/html': blobHtml,
            'text/plain': blobText
        }});
        
        navigator.clipboard.write([item]).then(() => {{
            alert('✅ Rapport copié !');
        }}).catch(err => {{
            alert('❌ Erreur de copie.');
        }});
    }}
    </script>
    """
    st.components.v1.html(js_copier_code, height=48)
    
    # Zone de rendu visuel sous forme d'onglets discrets
    tab_synth, tab_flash, tab_detail, tab_points, tab_cit = st.tabs([
        "📊 Synthèse", "⚡ Flash", "📖 Détail", "💡 Points clés", "💬 Citations"
    ])
    
    with tab_synth: st.markdown(data["synth"])
    with tab_flash: st.markdown(data["flash"])
    with tab_detail: st.markdown(data["detail"])
    with tab_points: st.markdown(data["points"])
    with tab_cit: st.markdown(data["citations"])
