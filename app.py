import streamlit as st
import sys

# Configuration de la page avec thème sombre natif forcé via le design
st.set_page_config(page_title="Analyseur YouTube (Mode UI Studio)", page_icon="📊", layout="wide")

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

    /* Ajustement spécifique pour l'alignement vertical du bouton URL */
    .url-container {
        display: flex;
        align-items: flex-end;
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
        if password == st.secrets.get("APP_PASSWORD", "admin"): # "admin" par défaut si test local sans secrets
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Code d'accès incorrect.")
    st.markdown('</div>', unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()

# --- INITIALISATION DES ÉTATS ET JEU DE DONNÉES DE TEST (CRÉDITS PARÉS) ---
if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = "📊 Synthèse"

if "debug_logs" not in st.session_state:
    st.session_state["debug_logs"] = [
        "⚙️ [MODE STUDIO UI] Initialisation du layout fictif réussie.",
        "📡 1min.ai : Mock HTTP 200 (Mode simulation activé, aucun crédit consommé)",
        "📝 Faux rapport injecté avec succès pour l'ajustement des styles graphiques."
    ]

# Génération automatique du faux contenu pour travailler l'UI sereinement
if 'report_data' not in st.session_state:
    st.session_state['report_data'] = {
        "synth": """
*Cette vidéo propose une immersion complète au cœur des architectures logicielles modernes. L'intervenant y décortique les transitions complexes des monolithes vers les microservices, tout en mettant en garde contre le piège de la sur-ingénierie dans les projets à forte scalabilité.*

- **Titre :** Maîtriser l'Architecture Logicielle en 2026 : Au-delà du Buzzword
- **Chaîne :** TechArchitect Pro
- **URL :** https://youtu.be/Jx_VtbJFLX8
- **Date :** 14/05/2026
- **Durée :** 24m 42s
- **Vues :** 128,450 vues
""",
        "detail": """
### 🏢 Chapitre 1 : L'illusion du découpage systématique
La vidéo débute par une critique constructive de la mode du "tout-microservices". Trop souvent, les équipes choisissent ce pattern d'architecture pour des raisons culturelles ou managériales plutôt que techniques. L'auteur rappelle que diviser une base de code augmente drastiquement la complexité réseau, la latence et rend la gestion des transactions distribuées particulièrement difficile.

### 🌐 Chapitre 2 : La communication inter-services
Dans un second temps, l'analyse se porte sur l'importance du choix entre protocoles synchrones (REST, gRPC) et asynchrones (Event-driven avec Kafka ou RabbitMQ). Le recours à l'asynchronisme est présenté comme le véritable pilier de la résilience, permettant de découpler efficacement la disponibilité des systèmes sous-jacents.
""",
        "points": """
1. **Le Monolithe modulaire d'abord** : Il est presque toujours préférable de démarrer avec une base de code unifiée mais rigoureusement segmentée en packages étanches avant de casser le modèle.
2. **Taxe Réseau** : Tout appel réseau a un coût. Multiplier les microservices sans une couche de cache ou un API Gateway performant détruit l'expérience utilisateur.
3. **Obsolescence technique** : Choisir un outil uniquement parce qu'il est poussé par les GAFAM est la cause numéro 1 des échecs de refonte.

### 🔢 Chiffres clés par Thématiques
### 💻 Performances Système
- **99.9%** : Objectif de disponibilité (SLA) ciblé par la mise en place de patterns de Circuit Breaker.
- **< 45ms** : Latence maximale tolérée pour les échanges inter-services via gRPC.

### 👥 Gestion des Équipes
- **2 Pizzas Team** : La taille idéale d'une équipe technique pour maintenir un domaine métier autonome sans surcharge de communication.
- **35%** : Réduction du temps de déploiement observée après la mise en conformité des contrats d'API.
""",
        "citations": """
### 💬 Citations fortes
- « Un mauvais monolithe transformé en microservices devient simplement un micro-bazar distribué. » *(Explique que déplacer le code sans revoir les frontières du domaine métier aggrave les problèmes au lieu de les résoudre)*.
- « Si votre base de données est partagée entre trois services, vous n'avez pas des microservices, vous avez un monolithe distribué secret. » *(Met en lumière l'erreur classique de couplage fort au niveau de la couche de persistance)*.

### 📚 Références et Livres mentionnés
- **Designing Data-Intensive Applications** par *Martin Kleppmann* (Le guide absolu pour comprendre le stockage et le traitement des données à grande échelle).
- **Domain-Driven Design (DDD)** par *Eric Evans* (L'approche conceptuelle indispensable pour découpler ses services d'après les contextes bornés du business).
"""
    }

# --- INTERFACE VISUELLE (TITRE & SOUS-TITRE) ---
st.markdown('<h1 class="main-title">Analyseur YouTube</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Résumé, points clés, chiffres et références extraits en quelques secondes</p>', unsafe_allow_html=True)

# --- ZONE URL + BOUTON À DROITE (SUR LA MÊME LIGNE) ---
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
col_url, col_btn = st.columns([5, 1]) # 5/6 pour l'input, 1/6 pour le bouton

with col_url:
    dummy_url = st.text_input("URL DE LA VIDÉO", value="https://youtu.be/Jx_VtbJFLX8", placeholder="https://www.youtube.com/watch?v=...")

with col_btn:
    # Petit hack CSS de marge supérieure pour aligner parfaitement le bouton avec le champ de saisie
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("Analyser", type="primary", use_container_width=True):
        st.toast("Mode Simulation : Aucun crédit consommé !", icon="🚀")
st.markdown('</div>', unsafe_allow_html=True)

# --- NAVIGATION INTERNE (TABULATION FIXE) ---
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

# --- RENDU DYNAMIQUE DU CONTENU DES SECTIONS ---
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
    st.subheader("📋 Copie brute du rapport complet (Markdown)")
    full_markdown = f"{data['synth']}\n\n---\n\n{data['detail']}\n\n---\n\n{data['points']}\n\n---\n\n{data['citations']}"
    st.code(full_markdown, language="markdown")
    
st.markdown('</div>', unsafe_allow_html=True)

# --- ZONE DE DEBUG EN BAS DE PAGE ---
st.markdown("<br><br><hr style='border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
with st.expander("🛠️ Console de Diagnostic technique (Debug)", expanded=True): # Ouvert par défaut pour travailler l'UI
    st.subheader("⚙️ État des Secrets (Simulation)")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1: st.metric("GEMINI_API_KEY", "Simulation active Mode UI 🛡️")
    with col_s2: st.metric("ONEMIN_API_KEY", "Crédits préservés 💸")
    with col_s3: st.metric("YOUTUBE_API_KEY", "Hors ligne 🌐")
        
    st.subheader("📜 Logs d'exécution simulés")
    log_text = "\n".join(st.session_state["debug_logs"])
    st.code(log_text, language="text")
