import streamlit as st
import cv2
import os
import tempfile
import zipfile
from pathlib import Path
import time

def extract_frames_from_video(video_path, interval_seconds=2, output_dir="extracted_frames"):
    """
    Extrait des frames d'une vidéo à intervalle régulier
    """
    # Créer le dossier de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Ouvrir la vidéo
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval_seconds)
    
    frame_count = 0
    saved_count = 0
    
    progress_bar = st.progress(0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Sauvegarder la frame si c'est le bon intervalle
        if frame_count % frame_interval == 0:
            frame_filename = f"frame_{saved_count:04d}.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            saved_count += 1
            
        frame_count += 1
        
        # Mise à jour de la barre de progression
        progress = frame_count / total_frames
        progress_bar.progress(min(progress, 1.0))
    
    cap.release()
    return saved_count, output_dir

def create_zip_from_folder(folder_path, zip_name="extracted_frames.zip"):
    """
    Crée un fichier ZIP à partir d'un dossier
    """
    zip_path = os.path.join(tempfile.gettempdir(), zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    
    return zip_path

def main():
    st.set_page_config(
        page_title="Extracteur de Frames Vidéo",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Extracteur de Frames pour Dataset YOLO")
    st.markdown("---")
    
    st.markdown("""
    ### 📋 Instructions :
    1. **Uploadez votre vidéo** (formats supportés: MP4, AVI, MOV, MKV)
    2. **Choisissez l'intervalle** d'extraction des frames
    3. **Téléchargez** le dossier ZIP contenant toutes les images extraites
    4. **Utilisez LabelImg** pour annoter les plaques sur ces images
    """)
    
    # Sidebar pour les paramètres
    with st.sidebar:
        st.header("⚙️ Paramètres d'extraction")
        
        interval_seconds = st.slider(
            "Intervalle d'extraction (secondes)",
            min_value=1,
            max_value=10,
            value=2,
            help="Une image sera extraite toutes les X secondes"
        )
        
        st.info(f"📊 Une frame sera sauvegardée toutes les {interval_seconds} secondes")
    
    # Zone d'upload
    uploaded_file = st.file_uploader(
        "Choisissez votre fichier vidéo",
        type=['mp4', 'avi', 'mov', 'mkv'],
        help="Taille maximale: 200MB"
    )
    
    if uploaded_file is not None:
        # Affichage des informations sur la vidéo
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"📁 **Nom du fichier:** {uploaded_file.name}")
            st.info(f"📏 **Taille:** {uploaded_file.size / (1024*1024):.2f} MB")
        
        with col2:
            st.info(f"⏱️ **Intervalle:** {interval_seconds}s")
            st.info(f"🖼️ **Estimation:** ~{60//interval_seconds} images/minute")
        
        # Bouton pour lancer l'extraction
        if st.button("🚀 Extraire les frames", type="primary", use_container_width=True):
            try:
                # Sauvegarder temporairement la vidéo uploadée
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                    temp_video.write(uploaded_file.getvalue())
                    temp_video_path = temp_video.name
                
                # Créer un dossier temporaire pour les frames
                temp_output_dir = tempfile.mkdtemp()
                
                with st.spinner("🎬 Extraction des frames en cours..."):
                    # Extraire les frames
                    saved_count, output_dir = extract_frames_from_video(
                        temp_video_path, 
                        interval_seconds, 
                        temp_output_dir
                    )
                
                if saved_count > 0:
                    st.success(f"✅ {saved_count} images extraites avec succès!")
                    
                    # Afficher quelques images d'aperçu
                    st.subheader("🖼️ Aperçu des images extraites")
                    
                    image_files = [f for f in os.listdir(output_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    
                    # Afficher les 3 premières images en aperçu
                    cols = st.columns(min(3, len(image_files)))
                    for i, img_file in enumerate(image_files[:3]):
                        img_path = os.path.join(output_dir, img_file)
                        with cols[i]:
                            st.image(img_path, caption=img_file, use_column_width=True)
                    
                    if len(image_files) > 3:
                        st.info(f"... et {len(image_files) - 3} autres images")
                    
                    # Créer le fichier ZIP
                    with st.spinner("📦 Création du fichier ZIP..."):
                        zip_path = create_zip_from_folder(output_dir)
                    
                    # Bouton de téléchargement
                    with open(zip_path, 'rb') as zip_file:
                        st.download_button(
                            label="📥 Télécharger toutes les images (ZIP)",
                            data=zip_file.read(),
                            file_name=f"frames_extracted_{int(time.time())}.zip",
                            mime="application/zip",
                            type="primary",
                            use_container_width=True
                        )
                    
                    st.markdown("---")
                    st.markdown("""
                    ### 🎯 Étapes suivantes :
                    1. **Extraire le ZIP** téléchargé
                    2. **Ouvrir LabelImg** (`pip install labelimg`)
                    3. **Annoter les plaques** sur chaque image
                    4. **Utiliser l'App 2** pour générer le dataset OCR
                    """)
                    
                else:
                    st.error("❌ Aucune image n'a pu être extraite. Vérifiez votre fichier vidéo.")
                
                # Nettoyer les fichiers temporaires
                os.unlink(temp_video_path)
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'extraction: {str(e)}")
    
    else:
        # Placeholder quand aucun fichier n'est uploadé
        st.markdown("""
        <div style="text-align: center; padding: 50px; background-color: #f0f2f6; border-radius: 10px; margin: 20px 0;">
            <h3>👆 Uploadez une vidéo pour commencer</h3>
            <p>Formats supportés: MP4, AVI, MOV, MKV</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
