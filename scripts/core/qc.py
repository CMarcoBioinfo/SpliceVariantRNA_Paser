import os
import zipfile
import webbrowser
import tempfile
import threading
import time
import shutil


def open_html_from_zip(zip_path, folder, window, label):
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            # Trouver un fichier HTML dans le dossier demandé
            html_candidates = [
                name for name in z.namelist()
                if name.startswith(folder) and name.endswith(".html")
            ]

            if not html_candidates:
                window["-STATUS-"].update(f"{label} introuvable.", text_color="red")
                return

            internal_html = html_candidates[0]

            tmp_dir = os.path.join(tempfile.gettempdir(), ".tmp_qc_html")
            os.makedirs(tmp_dir, exist_ok=True)

            # Extraire le HTML
            html_name = os.path.basename(internal_html)
            html_path = os.path.join(tmp_dir, html_name)
            with open(html_path, "wb") as f:
                f.write(z.read(internal_html))

            # Extraire le dossier _data au même niveau que le HTML
            data_prefix = internal_html.replace(".html", "_data/")
            for name in z.namelist():
                if name.startswith(data_prefix):
                    # On ne garde que les deux derniers segments : dossier_data/fichier
                    parts = name.split("/")[-2:]
                    out_path = os.path.join(tmp_dir, *parts)

                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    with open(out_path, "wb") as f:
                        f.write(z.read(name))

            # Ouvrir dans le navigateur
            webbrowser.open(f"file://{html_path}")
            window["-STATUS-"].update(f"{label} ouvert.", text_color="green")

            # Nettoyage automatique
            def cleanup():
                time.sleep(30)
                try:
                    os.remove(html_path)
                except:
                    pass

                data_dir = os.path.join(tmp_dir, os.path.basename(data_prefix))
                if os.path.exists(data_dir):
                    shutil.rmtree(data_dir, ignore_errors=True)

            threading.Thread(target=cleanup, daemon=True).start()

    except Exception as e:
        window["-STATUS-"].update(f"Erreur QC : {e}", text_color="red")
