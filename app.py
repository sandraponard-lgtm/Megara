import streamlit as st
import requests
from google import genai

# Configuration de la page Streamlit
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="📊", layout="wide")

# Interface utilisateur
st.title("📊 Analyseur & Extracteur de Contenu YouTube")
st.write("Collez une URL YouTube pour générer une analyse complète selon vos critères personnalisés.")

# Sidebar pour la configuration de l'API Key
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Clé API Google Gemini", type="password", help="Obtenez une clé gratuite sur Google AI Studio")
    st.markdown("---")
    st.caption("Développé avec Streamlit & Gemini API")

# Champ de saisie pour l'URL
video_url = st.text_input("Entrez l'URL de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

# Fonction de secours pour extraire l'ID de la vidéo
def get_video_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    return None

if st.button("Analyser la vidéo", type="primary"):
    if not api_key:
        st.warning("Veuillez renseigner votre clé API Gemini dans la barre latérale.")
    elif not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        video_id = get_video_id(video_url)
        
        if not video_id:
            st.error("Impossible de détecter l'ID de la vidéo. Vérifiez l'URL.")
        else:
            # Étape 1 : Récupération des sous-titres via un outil tiers gratuit pour éviter le blocage IP de Streamlit
            st.info("Récupération du contenu de la vidéo...")
            transcript_text = ""
            
            try:
                # Utilisation d'une API de décodage de sous-titres publique et gratuite
                response = requests.get(f"https://transcript.samuelcolvin.workers.dev/{video_id}", timeout=15)
                if response.status_code == 200 and len(response.text.strip()) > 100:
                    transcript_text = response.text
                else:
                    # Deuxième tentative sur un autre résolveur si le premier échoue
                    res = requests.get(f"https://api.vemos.org/transcript?v={video_id}", timeout=15)
                    if res.status_code == 200:
                        data = res.json()
                        transcript_text = " ".join([part.get('text', '') for part in data.get('lines', [])])
            except Exception as e:
                pass

            # Si aucune API externe n'a pu extraire le texte, on tente un appel direct
            if not transcript_text:
                st.warning("⚠️ Impossible d'extraire les sous-titres textuels de manière automatisée. Tentative d'analyse contextuelle brute...")
                transcript_text = f"[ID de la vidéo à analyser : {video_id}. Analyse le sujet global de cette vidéo.]"

            # Étape 2 : Envoi du texte structuré à Gemini
            try:
                client = genai.Client(api_key=api_key)
                
                prompt_text = f"""
                Agis comme un analyste expert. Analyse attentivement la transcription textuelle de la vidéo YouTube (ID: {video_id}) fournie ci-dessous et rédige un rapport structuré en français en respectant SCRUPULEUSEMENT le plan suivant :

                ## 📝 Résumé rapide
                *(Rédige ici un résumé très condensé en 2 ou 3 phrases maximum, obligatoirement en italique)*

                ---

                ## ℹ️ Informations
                - **Titre :** (Déduis le titre exact ou probable de la vidéo d'après le contexte)
                - **Chaîne :** (Identifie le créateur ou la chaîne d'après le texte)
                - **Date :** (La date ou l'époque estimée d'après les propos)
                - **Durée :** (Estime la durée ou indique "Non calculable")
                - **Langue :** Français
                - **Vues :** (Indique "Non extrait")

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
                - **📚 Livres :** (Liste des livres, ouvrages ou documents cités. Si aucun n'est cité, écris "Aucun livre mentionné")
                - **👤 Personnalités :** (Liste des personnes, auteurs, experts ou figures historiques cités. Si aucune n'est citée, écris "Aucune personnalité mentionnée")

                Voici le contenu textuel de la vidéo à analyser :
                {transcript_text}
                """
                
                with st.spinner("Gemini génère votre rapport personnalisé..."):
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_text
                    )
                
                # Affichage final des résultats
                st.markdown("---")
                st.subheader("🎬 Rapport d'Analyse Vidéo")
                st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"Erreur lors de la génération par l'IA : {str(e)}")
