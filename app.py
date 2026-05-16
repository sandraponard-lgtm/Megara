import streamlit as st
from google import genai
from google.genai.types import Part

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

if st.button("Analyser la vidéo", type="primary"):
    if not api_key:
        st.warning("Veuillez renseigner votre clé API Gemini dans la barre latérale.")
    elif not video_url:
        st.warning("Veuillez entrer une URL valide.")
    else:
        # Nettoyage de l'URL pour s'assurer qu'elle est au format standard attendu par Google
        if "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
            clean_url = f"https://www.youtube.com/watch?v={video_id}"
        elif "watch?v=" in video_url:
            video_id = video_url.split("watch?v=")[1].split("&")[0]
            clean_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            clean_url = video_url

        st.info("Connexion à l'infrastructure Google... Analyse de la vidéo en cours.")
        
        try:
            # Initialisation du client Gemini
            client = genai.Client(api_key=api_key)
            
            # Prompt ultra-structuré basé sur vos critères
            prompt_text = """
            Agis comme un analyste expert. Analyse attentivement le contenu visuel et audio de la vidéo YouTube fournie et rédige un rapport structuré en français en respectant SCRUPULEUSEMENT le plan suivant :

            ## 📝 Résumé rapide
            *(Rédige ici un résumé très condensé en 2 ou 3 phrases maximum, obligatoirement en italique)*

            ---

            ## ℹ️ Informations
            - **Titre :** (Le titre de la vidéo)
            - **Chaîne :** (Le nom de la chaîne YouTube qui a publié la vidéo)
            - **Date :** (La date de publication ou une estimation d'après les propos)
            - **Durée :** (La durée de la vidéo)
            - **Langue :** (La langue parlée dans la vidéo)
            - **Vues :** (Le nombre de vues si disponible, sinon indique "Non extrait")

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
            """
            
            # Appel au modèle avec injection du flux URI
            with st.spinner("Gemini examine la vidéo... Cela prend généralement entre 15 et 30 secondes."):
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        Part.from_uri(
                            file_uri=clean_url,
                            mime_type="video/mp4"
                        ),
                        prompt_text
                    ]
                )
            
            # Affichage des résultats personnalisés
            st.markdown("---")
            st.subheader("🎬 Rapport d'Analyse Vidéo")
            st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Erreur lors de la génération par l'IA : {str(e)}")
