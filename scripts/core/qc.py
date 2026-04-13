import os
import zipfile
import tempfile
import shutil
import subprocess

def open_html_from_zip(zip_path, folder, window, label):
    try:
        with zipfile.ZipFile(zip_path, "r") as z:

            # Trouver le HTML
            html_candidates = [
                name for name in z.namelist()
                if name.startswith(folder) and name.endswith(".html")
            ]

            if not html_candidates:
                window["-STATUS-"].update(f"{label} introuvable.", text_color="red")
                return

            internal_html = html_candidates[0]

            # Dossier temporaire unique
            tmp_dir = tempfile.mkdtemp(prefix="qc_tmp_")

            # Extraction du HTML
            html_name = os.path.basename(internal_html)
            html_path = os.path.join(tmp_dir, html_name)

            with open(html_path, "wb") as f:
                f.write(z.read(internal_html))

            # Extraction du dossier _data
            data_prefix = internal_html.replace(".html", "_data/")
            for name in z.namelist():
                if name.startswith(data_prefix):
                    z.extract(name, tmp_dir)

            window["-STATUS-"].update(f"{label} ouvert.", text_color="green")

            # --- OUVERTURE + ATTENTE FERMETURE (Windows) ---
            cmd = f'start "" /WAIT "{html_path}"'
            subprocess.call(cmd, shell=True)

            # --- SUPPRESSION APRÈS FERMETURE ---
            shutil.rmtree(tmp_dir, ignore_errors=True)

    except Exception as e:
        window["-STATUS-"].update(f"Erreur QC : {e}", text_color="red")

