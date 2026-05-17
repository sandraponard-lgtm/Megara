import streamlit as st
import sys

# Configuration de la page
st.set_page_config(page_title="Analyseur YouTube", page_icon="📊", layout="wide")

# --- INJECTION CSS DE NETTOYAGE ET COMPACTAGE ---
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #0f0f13;
        color: #e2e8f0;
    }
    
    /* En-tête ultra-compact (prend beaucoup moins de place) */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 1.8rem;
        background: linear-gradient(45deg, #a78bfa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: -2rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }

    /* Container de la zone de recherche sans fioritures (retire les rectangles vides) */
    .search-box {
        margin-bottom: 1.5rem;
    }

    /* Forcer l'alignement horizontal du bouton et de l'input même sur mobile */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
    }

    /* Style des onglets natifs Streamlit pour correspondre au thème sombre */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(23, 23, 33, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 8px 16px;
        color: #94a3b8;
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
        if password == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Code d'accès incorrect.")
    return False

if not check_password():
    st.stop()

# --- DONNÉES DE SIMULATION (UI STUDIO) ---
if "debug_logs" not in st.session_state:
    st.session_state["debug_logs"] = [
        "⚙️ [MODE STUDIO UI] Version compacte mobile chargée.",
        "📡 1min.ai : Mock HTTP 200 (Aucun crédit consommé)"
    ]

if 'report_data' not in st.session_state:
    st.session_state['report_data'] = {
        "synth": """*Cette vidéo propose une immersion complète au cœur des architectures logicielles modernes. L'intervenant y décortique les transitions complexes des monolithes vers les microservices.*
        
- **Titre :** Maîtriser l'Architecture Logicielle en 2026
- **Chaîne :** TechArchitect Pro
- **Date :** 14/05/2026
- **Durée :** 24m 42s""",
        "detail": """### 🏢 Chapitre 1 : L'illusion du découpage systématique
La vidéo débute par une critique constructive de la mode du "tout-microservices". Trop souvent, les équipes choisissent ce pattern d'architecture pour des raisons culturelles ou managériales plutôt que techniques. L'auteur rappelle que diviser une base de code augmente drastiquement la complexité réseau.""",
        "points": """1. **Le Monolithe modulaire d'abord** : Il est presque toujours préférable de démarrer avec une base de code unifiée.
2. **Taxe Réseau** : Tout appel réseau a un coût.

### 🔢 Chiffres clés
- **99.9%** : Objectif de disponibilité (SLA) ciblé.
- **< 45ms** : Latence maximale tolérée.""",
        "citations": """### 💬 Citations fortes
- « Un mauvais monolithe transformé en microservices devient simplement un micro-bazar distribué. »
- « Si votre base de données est partagée entre trois services, vous avez un monolithe distribué secret. »"""
    }

data = st.session_state['report_data']

# --- INTERFACE VISUELLE (HAUT DE PAGE COMPACT) ---
st.markdown('<h1 class="main-title">Analyseur YouTube</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Résumé, points clés et chiffres en quelques secondes</p>', unsafe_allow_html=True)

# --- BLOC RECHERCHE : URL ET BOUTON CÔTE À CÔTE ---
col_url, col_btn = st.columns([3, 1])

with col_url:
    st.text_input("URL DE LA VIDÉO", value="https://youtu.be/Jx_VtbJFLX8", label_visibility="collapsed")

with col_btn:
    if st.button("Analyser", type="primary", use_container_width=True):
        st.toast("Mode Simulation !", icon="🚀")

st.markdown("<br>", unsafe_allow_html=True)

# --- NAVIGATION HORIZONTALE VIA ST.TABS ---
tab_synth, tab_detail, tab_points, tab_cit, tab_export = st.tabs([
    "📊 Synthèse", "📖 Analyse détaillée", "💡 Points clés", "💬 Citations", "📋 Export"
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
    st.subheader("📋 Copie brute (Markdown)")
    full_markdown = f"{data['synth']}\n\n---\n\n{data['detail']}\n\n---\n\n{data['points']}\n\n---\n\n{data['citations']}"
    st.code(full_markdown, language="markdown")

# --- ZONE DE DEBUG EN BAS DE PAGE ---
st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
with st.expander("🛠️ Console de Diagnostic (Debug)", expanded=False):
    st.code("\n".join(st.session_state["debug_logs"]), language="text")
