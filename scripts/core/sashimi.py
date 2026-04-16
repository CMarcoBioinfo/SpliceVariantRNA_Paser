import os
import zipfile
import io
import subprocess
import tempfile
import threading
import time

def find_sashimi_pdf(run_sashimi_zip, group_name, patient_id, sashimi_filename):
    """
    Trouve un PDF sashimi dans la structure :
    run_sashimi.zip → group_sashimi.zip → patient_sashimi.zip → sashimi_plot/.../file.pdf

    Retourne (patient_zip_bytes, internal_pdf_path) ou None.
    """

    # 1) ZIP du RUN
    with zipfile.ZipFile(run_sashimi_zip, "r") as z1:
        group_zip_name = f"{group_name}_sashimi.zip"
        if group_zip_name not in z1.namelist():
            return None

        group_bytes = z1.read(group_zip_name)
        group_buffer = io.BytesIO(group_bytes)

    # 2) ZIP du GROUPE
    with zipfile.ZipFile(group_buffer, "r") as z2:
        patient_zip_name = f"{patient_id}_sashimi.zip"
        if patient_zip_name not in z2.namelist():
            return None

        patient_bytes = z2.read(patient_zip_name)
        patient_buffer = io.BytesIO(patient_bytes)

    # 3) ZIP du PATIENT
    with zipfile.ZipFile(patient_buffer, "r") as z3:
        matches = [f for f in z3.namelist() if f.endswith(sashimi_filename)]
        if not matches:
            return None

        internal_pdf = matches[0]
        pdf_bytes = z3.read(internal_pdf)

    return pdf_bytes


def open_sashimi_plot(run_sashimi_zip, group_name, patient_id, sashimi_filename, window, global_tmp):
    """
    Extrait un sashimi PDF dans un dossier temporaire et l'ouvre.
    """

    try:
        pdf_bytes = find_sashimi_pdf(run_sashimi_zip, group_name, patient_id, sashimi_filename)

        if pdf_bytes is None:
            window["-STATUS-"].update("Sashimi introuvable.", text_color="red")
            return

        # Dossier temporaire
        tmp_dir = os.path.join(global_tmp, "sashimi_plots", patient_id)
        os.makedirs(tmp_dir, exist_ok=True)

        pdf_path = os.path.join(tmp_dir, sashimi_filename)

        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        window["-STATUS-"].update("Sashimi extrait.", text_color="green")

        # Ouvrir dans le navigateur
        subprocess.Popen(f'explorer "{pdf_path}"')

        # Suppression automatique après 30s (comme TRGT)
        def cleanup(path):
            time.sleep(30)
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

        threading.Thread(target=cleanup, args=(pdf_path,), daemon=True).start()

    except Exception as e:
        window["-STATUS-"].update(f"Erreur sashimi : {e}", text_color="red")
