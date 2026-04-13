import PySimpleGUI as sg
import zipfile
import tempfile
import shutil
import os

from scripts.core.orchestrator import process_sample
from scripts.core.qc import open_html_from_zip
from scripts.ui.sample_window import open_patient_window

GLOBAL_QC_TMP = tempfile.mkdtemp(prefix="qc_session_")

import ctypes
import sys

def open_console():
    # Ouvre une console Windows
    ctypes.windll.kernel32.AllocConsole()
    # Redirige stdout et stderr vers la console
    sys.stdout = open("CONOUT$", "w")
    sys.stderr = open("CONOUT$", "w")

open_console()

# --------------------------
# UTILITAIRES
# --------------------------

def list_groups(run_zip):
    """Retourne la liste des groupes *_recap.zip dans un RUN."""
    with zipfile.ZipFile(run_zip, "r") as z:
        return [
            f for f in z.namelist()
            if f.lower().endswith("_recap.zip")
            ]


def list_samples(run_zip, group_zip):
    """Retourne la liste des fichier .recap.xlsx dans un groupe interne."""
    with zipfile.ZipFile(run_zip, "r") as z:
        with z.open(group_zip) as inner:
            with zipfile.ZipFile(inner) as gz:
                return [
                    f for f  in gz.namelist()
                    if f.lower().endswith(".recap.xlsx")
                ]


# --------------------------
# MAIN UI
# --------------------------

def main():
    sg.theme("SystemDefault")

    layout = [
        [sg.Text("Sélection du fichier SpliceVariantRNA (.recap.zip)")],
        [sg.Input(key="-RUN-", enable_events=True), sg.FileBrowse("Parcourir")],

        [sg.Text("Groupe à analyser")],
        [sg.Combo([], key="-GROUP-", size=(40,1), readonly=True, enable_events=True)],

        [sg.Text("Contrôle qualité")],
        [
            sg.Button("FASTQ Raw QC", key="-QC-RAW-", disabled=True),
            sg.Button("FASTQ Trimmed QC", key="-QC-TRIM-", disabled=True),
            sg.Button("BAM QC", key="-QC-BAM-", disabled=True),
        ],

        [sg.Text("Patient à analyser")],
        [sg.Input(key="-SEARCH-", enable_events=True, size=(40,1))],
        [sg.Combo([], key="-SAMPLE-", size=(40,1), readonly=True)],

        [sg.Button("Lancer l'analyse", key="-ANALYZE-")],
        [sg.Text("", key="-STATUS-", text_color="blue")],

        [sg.Text("by Corentin Marco", justification="right", font=("Helvetica",8), text_color="gray")]
    ]

    window = sg.Window("SpliceVaraintRNA Parser", layout)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            shutil.rmtree(GLOBAL_QC_TMP, ignore_errors=True)
            break
        
        # --------------------------
        # 1) Sélection du RUN
        # --------------------------

        if event == "-RUN-":
            run_path = values["-RUN-"]

            if not run_path:
                continue
            
            if not run_path.lower().endswith(".zip"):
                window["-STATUS-"].update("Veuillez sélectionner un fichier ZIP valide.", text_color="red")
                continue
            

            run_name = os.path.basename(run_path)
            groups = list_groups(run_path)

            if not groups:
                window["-STATUS-"].update("Aucun groupe n'est trouvé dans : {run_name}", text_color="red")
            
            all_samples = {}

            for group_zip in groups:
                samples = list_samples(run_path, group_zip)
                for s in samples:
                    all_samples[s] = group_zip
            
            window.metadata = {}
            window.metadata["all_samples"] = all_samples

            window["-GROUP-"].update(values=groups)
            window["-STATUS-"].update(f"{len(groups)} groupes trouvés", text_color="blue")
            
        # --------------------------
        # 2) Sélection du groupe
        # --------------------------
        
        if event == "-GROUP-":
            run_path = values["-RUN-"]
            group_zip = values["-GROUP-"]

            run_dir = os.path.dirname(run_path)
            run_base = os.path.basename(run_path).replace("_recap.zip","")
            qc_zip = os.path.join(run_dir, f"{run_base}_qc.zip")

            window["-QC-RAW-"].update(disabled=True)
            window["-QC-TRIM-"].update(disabled=True)
            window["-QC-BAM-"].update(disabled=True)

            if os.path.exists(qc_zip):
                with zipfile.ZipFile(qc_zip, "r") as z:
                    names = z.namelist()

                    if any(n.endswith(".html") and n.startswith("fastq_raw/") for n in names):
                        window["-QC-RAW-"].update(disabled=False)

                    if any(n.endswith(".html") and n.startswith("fastq_trimmed/") for n in names):
                        window["-QC-TRIM-"].update(disabled=False)

                    if any(n.endswith(".html") and n.startswith("BAM/") for n in names):
                        window["-QC-BAM-"].update(disabled=False)

            if not group_zip:
                continue
            
            samples = list_samples(run_path, group_zip)
            group_name = os.path.basename(group_zip)

            window.metadata = {}
            window.metadata["all_samples"] = samples
            window["-SAMPLE-"].update(values=samples)


            if not samples:
                window["-STATUS-"].update("Aucun patient n'est trouvé dans : {group_name}", text_color="red")
                continue
            
            window["-SAMPLE-"].update(values=samples)
            window["-STATUS-"].update(f"{len(samples)} patients trouvés.", text_color="blue")

        
        # --------------------------
        # 3) Sélection du patient
        # --------------------------

        if event == "-SEARCH-":
            query = values["-SEARCH-"].lower()
            all_samples = window.metadata.get("all_samples", {})

            filtered = [s for s in all_samples if query in s.lower()]
            
            window["-SAMPLE-"].update(values=filtered)

            if len(filtered) == 1:
                sample = filtered[0]
                group = all_samples[sample]

                window["-GROUP-"].update(group)

                samples = list_samples(values["-RUN-"], group)
                window["-SAMPLE-"].update(values=samples)

                window["-SAMPLE-"].update(sample)

        
        # --------------------------
        # 4) Lancement de l'analyse pour le patient sélectionné
        # --------------------------

        if event == "-ANALYZE-":
            run_path = values["-RUN-"]
            group_zip = values["-GROUP-"]
            sample = values["-SAMPLE-"]

            # Vérifications simples
            if not run_path:
                window["-STATUS-"].update("Veuillez sélectionner un fichier ZIP", text_color="red")
                continue

            if not group_zip:
                window["-STATUS-"].update("Veuillez sélectionner un groupe", text_color="red")
                continue

            if not sample:
                window["-STATUS-"].update("Veuillez sélectionner un patient", text_color="red")
                continue

            # Lancer l'analyse
            window["-STATUS-"].update(f"Analyse en cours pour : {sample}", text_color="blue")

            try:
                events = process_sample(run_path, group_zip, sample)
                open_patient_window(events)
                #window["-STATUS-"].update(f"Analyse terminée pour : {sample}", text_color="green")

            except Exception as e:
                window["-STATUS-"].update(f"Erreur lors de l'analyse : {e}", text_color="red")

        # --------------------------
        # 5) Lancement des contrôle qualité
        # --------------------------

        if event == "-QC-RAW-":
            run_dir = os.path.dirname(values["-RUN-"])
            run_base = os.path.basename(values["-RUN-"]).replace("_recap.zip", "")
            qc_zip = os.path.join(run_dir, f"{run_base}_qc.zip")
            open_html_from_zip(qc_zip, "fastq_raw/", window, "FASTQ Raw QC", GLOBAL_QC_TMP)



        if event == "-QC-TRIM-":
            run_dir = os.path.dirname(values["-RUN-"])
            run_base = os.path.basename(values["-RUN-"]).replace("_recap.zip", "")
            qc_zip = os.path.join(run_dir, f"{run_base}_qc.zip")
            open_html_from_zip(qc_zip, "fastq_trimmed/", window, "FASTQ Trimmed QC", GLOBAL_QC_TMP)


        if event == "-QC-BAM-":
            run_dir = os.path.dirname(values["-RUN-"])
            run_base = os.path.basename(values["-RUN-"]).replace("_recap.zip", "")
            qc_zip = os.path.join(run_dir, f"{run_base}_qc.zip")
            open_html_from_zip(qc_zip, "BAM/", window, "BAM QC", GLOBAL_QC_TMP)
        
    window.close() 

if __name__ == "__main__":
    main()
