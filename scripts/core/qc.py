import os
import zipfile
import webbrowser
import tempfile
import threading
import time

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

            # Dossier temporaire
            tmp_dir = os.path.join(tempfile.gettempdir(), ".tmp_qc_html")
            os.makedirs(tmp_dir, exist_ok=True)

            # Extraire uniquement le HTML (comme TRGT)
            html_name = os.path.basename(internal_html)
            html_path = os.path.join(tmp_dir, html_name)

            with open(html_path, "wb") as f:
                f.write(z.read(internal_html))

            # Ouvrir même si la page sera blanche
            webbrowser.open(f"file://{html_path}")
            window["-STATUS-"].update(f"{label} ouvert (sans data).", text_color="orange")

            # Nettoyage TRGT-style
            def cleanup():
                time.sleep(30)
                try:
                    os.remove(html_path)
                except:
                    pass

            threading.Thread(target=cleanup, daemon=True).start()

    except Exception as e:
        window["-STATUS-"].update(f"Erreur QC : {e}", text_color="red")
