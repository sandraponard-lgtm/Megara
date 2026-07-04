import streamlit as st
import requests
import io
import sys
import re
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
    
    /* Zone de rendu final propre */
    .preview-box-clean {
        background-color: #171721;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-top: 10px;
        color: #e2e8f0;
        font-family: system-ui, -apple-system, sans-serif;
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

# --- CONVERTISSEUR LIGHT MARKDOWN -> HTML PROPRE (SANS BALISES IA) ---
def md_to_clean_html(text):
    if not text: return ""
    
    # Nettoyage des marqueurs de structure générés par l'IA
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
                html_output.append("</ul>")
                in_list = False
            continue
            
        if line_str.startswith('#'):
            if in_list:
                html_output.append("</ul>")
                in_list = False
            title_text = line_str.lstrip('#').strip()
            html_output.append(f"<h3 style='color: #c084fc; margin-top: 16px; margin-bottom: 6px; font-size:1.15rem;'>{title_text}</h3>")
            continue
            
        if line_str.startswith('- ') or line_str.startswith('* ') or line_str.startswith('• '):
            if not in_list:
                html_output.append("<ul style='margin-top: 4px; margin-bottom: 4px; padding-left: 20px;'>")
                in_list = True
            bullet_content = re.sub(r'^[-*•]\s*', '', line_str)
            bullet_content = re.sub(r'\*\*(.*?)\*\*|\_\_(.*?)\_\_', r'<b>\1\2</b>', bullet_content)
            html_output.append(f"<li style='margin-bottom: 4px;'>{bullet_content}</li>")
            continue
            
        if in_list:
            html_output.append("</ul>")
            in_list = False
            
        line_str = re.sub(r'\*\*(.*?)\*\*|\_\_(.*?)\_\_', r'<b>\1\2</b>', line_str)
        line_str = re.sub(r'\*(.*?)\*|\_(.*?)\_', r'<i>\1\2</i>', line_str)
        html_output.append(f"<p style='margin-top: 4px; margin-bottom: 4px; line-height: 1.4;'>{line_str}</p>")
        
    if in_list:
        html_output.append("</ul>")
        
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

# --- INTERFACE GRAPHIQUE ---
st.markdown('<h1 class="main-title">Analyseur YouTube</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Résumé, points clés et chiffres extraits en quelques secondes</p>', unsafe_allow_html=True)

col_url, col_btn = st.columns([3, 1])
with col_url:
    video_url = st.text_input("URL DE LA VIDÉO", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
with col_btn:
    trigger_analyse = st.button("Analyser", type="primary", use_container_width=True)

with st.expander("📝 Option : Coller directement une transcription brute", expanded=False):
    manual_transcript = st.text_area("Colle ton texte ou ta transcription ici", height=150)

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
            details = get_official_youtube_details(video_id, yt_key) if video_id != "texte_manuel" else None
            title_clean = details['title'] if details else "Analyse_Manuelle"
            meta_part = f"- **Titre :** {details['title']}\n- **Chaîne :** {details['channel']}\n- **URL :** {video_url}" if details else f"- **Titre :** Déduction auto\n- **URL :** {video_url if video_url else 'Manuel'}"

            try:
                client = genai.Client(api_key=gemini_key)
                prompt_text = f"Analyse cette transcription et sépare strictement chaque bloc par '===SECTION_SEPARATOR==='.\n[SECTION 1: SYNTHESE]\nRésumé en 2 phrases italiques.\n{meta_part}\n===SECTION_SEPARATOR===\n[SECTION 2: RESUME_FLASH]\n4 à 6 puces percutantes.\n===SECTION_SEPARATOR===\n[SECTION 3: DETAIL]\nRésumé dense en paragraphes.\n===SECTION_SEPARATOR===\n[SECTION 4: POINTS_CLES]\nListe numérotée et chiffres clés.\n===SECTION_SEPARATOR===\n[SECTION 5: CITATIONS]\nCitations fortes et références.\n\nTranscription:\n{transcript_text}"
                
                with st.spinner("Analyse en cours..."):
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_text)
                
                sections = response.text.split("===SECTION_SEPARATOR===")
                st.session_state['report_data'] = {
                    "synth": sections[0].strip(), "flash": sections[1].strip(), "detail": sections[2].strip(), "points": sections[3].strip(), "citations": sections[4].strip()
                }
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

# --- VISUALISATION ET ACTION DE COPIE UNIQUE SANS CODE EXTÉRIEUR ---
if 'report_data' in st.session_state:
    data = st.session_state['report_data']
    
    tab_synth, tab_flash, tab_detail, tab_points, tab_cit, tab_export = st.tabs([
        "📊 Synthèse", "⚡ Résumé Flash", "📖 Analyse détaillée", "💡 Points clés", "💬 Citations", "📋 Copie en Un Clic"
    ])
    
    with tab_synth: st.markdown(data["synth"])
    with tab_flash: st.markdown(data["flash"])
    with tab_detail: st.markdown(data["detail"])
    with tab_points: st.markdown(data["points"])
    with tab_cit: st.markdown(data["citations"])
    
    with tab_export:
        # Conversion invisible
        html_synth = md_to_clean_html(data['synth'])
        html_flash = md_to_clean_html(data['flash'])
        html_detail = md_to_clean_html(data['detail'])
        html_points = md_to_clean_html(data['points'])
        html_citations = md_to_clean_html(data['citations'])
        
        # Structure HTML propre pour le presse-papiers
        final_rich_html = (
            f"<h2>📊 SYNTHÈSE</h2>{html_synth}<br><br>"
            f"<h2>⚡ RÉSUMÉ FLASH</h2>{html_flash}<br><br>"
            f"<h2>📖 ANALYSE DÉTAILLÉE</h2>{html_detail}<br><br>"
            f"<h2>💡 POINTS CLÉS & CHIFFRES</h2>{html_points}<br><br>"
            f"<h2>💬 CITATIONS & RÉFÉRENCES</h2>{html_citations}"
        )
        
        st.subheader("📋 Presse-papiers intelligent")
        st.info("📱 Clique sur le bouton rouge. Tout le document sera mis en mémoire avec ses styles (Titres, listes). Tu n'as plus qu'à aller le coller directement dans Teams, Word ou ton application de notes.")
        
        # Encodage JS sécurisé pour éliminer l'affichage des balises brutes à l'écran
        escaped_html = final_rich_html.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
        
        js_copier_code = f"""
        <div style="text-align: center; margin-bottom: 15px;">
            <button onclick="copyToClipboard()" style="
                background-color: #ff4b4b;
                color: white;
                border: none;
                padding: 14px 28px;
                font-weight: bold;
                font-size: 1.05rem;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
                box-shadow: 0px 4px 12px rgba(255, 75, 75, 0.3);
            ">📋 COPIER LE RAPPORT EN TEXTE RICHE</button>
        </div>

        <script>
        function copyToClipboard() {{
            const htmlData = "{escaped_html}";
            const blobHtml = new Blob([htmlData], {{ type: 'text/html' }});
            
            // Extraction du texte brut pour fallback universel
            const div = document.createElement('div');
            div.innerHTML = htmlData;
            const plainText = div.textContent || div.innerText || "";
            const blobText = new Blob([plainText], {{ type: 'text/plain' }});
            
            const item = new ClipboardItem({{
                'text/html': blobHtml,
                'text/plain': blobText
            }});
            
            navigator.clipboard.write([item]).then(() => {{
                alert('✅ Rapport copié avec succès en texte riche !');
            }}).catch(err => {{
                alert('❌ Erreur de copie automatique. Utilise la sélection manuelle ci-dessous.');
            }});
        }}
        </script>
        """
        # Injection du composant bouton invisible/interactif
        st.components.v1.html(js_copier_code, height=65)
        
        # Zone d'aperçu de ce qui a été copié (Interprété, propre, sans balises HTML visibles)
        st.markdown("**🔍 Aperçu visuel de ton texte formaté après le collage :**")
        st.markdown(f'<div class="preview-box-clean">{final_rich_html}</div>', unsafe_allow_html=True)
