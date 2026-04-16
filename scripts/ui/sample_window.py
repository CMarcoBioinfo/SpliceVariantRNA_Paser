import PySimpleGUI as sg
from scripts.core.qc import open_html_from_zip

COLUMNS_BY_SOURCE = {
    "Statistical": ["Gene", "Event", "Position", "Depth", "PSI-like", "p-value", "nbSignificantSamples"],
    "Unique": ["Gene", "Event", "Position", "Depth", "PSI-like", "p-value", "nbFilteredSamples"],
    "ThresholdExceeded": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
    "NoModel": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
    "TooComplex": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
}

def normalize(s):
    return s.strip().replace(" ", "").lower()

def events_to_table(events, columns):
    return [[ev.get(col, "") for col in columns] for ev in events]

def open_patient_window(events, patient_id, qc_zip, global_tmp):
    sg.theme("SystemDefault")

    # Normalisation des sources
    for ev in events:
        ev["Source"] = normalize(ev["Source"])

    COLUMNS_NORM = { normalize(k): v for k, v in COLUMNS_BY_SOURCE.items() }

    events_by_cat = {
        cat: [ev for ev in events if ev["Source"] == cat]
        for cat in COLUMNS_NORM.keys()
    }

    # Tabs
    tabs = []
    for original_name, cols in COLUMNS_BY_SOURCE.items():
        cat_norm = normalize(original_name)

        table = sg.Table(
            values=events_to_table(events_by_cat[cat_norm], cols),
            headings=cols,
            key=f"-TABLE-{cat_norm}-",
            auto_size_columns=True,
            enable_events=True,
            expand_x=True,
            expand_y=True,
            num_rows=12
        )

        tabs.append(sg.Tab(original_name, [[table]], key=f"-TAB-{cat_norm}-"))

    tab_group = sg.TabGroup(
        [tabs],
        key="-TABGROUP-",
        expand_x=True,
        expand_y=True,
        enable_events=True
    )

    # Layout avec les 3 boutons QC
    layout = [
        [tab_group],
        [
            sg.Frame(
                f"Détails {patient_id}",
                [[sg.Multiline("", key="-DETAILS-", size=(80, 15), disabled=True)]],
                expand_x=True,
                expand_y=True
            )
        ],
        [
            sg.Button("FASTQ Raw QC", key="-QC-RAW-", size=(14,1)),
            sg.Button("FASTQ Trimmed QC", key="-QC-TRIM-", size=(16,1)),
            sg.Button("BAM QC", key="-QC-BAM-", size=(10,1)),
        ]
    ]

    window = sg.Window(f"SpliceVariantRNA Viewer — {patient_id}", layout, resizable=True)

    current_category = normalize("Statistical")

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        # Changement d'onglet
        if event == "-TABGROUP-":
            tab_key = values["-TABGROUP-"]
            current_category = tab_key[5:-1].lower()

        # Sélection d'une ligne
        if event.startswith("-TABLE-"):
            try:
                idx = values[event][0]
                selected_event = events_by_cat[current_category][idx]
                details = "\n".join(f"{k}: {v}" for k, v in selected_event.items())
                window["-DETAILS-"].update(details)
            except Exception as e:
                print("Erreur détails:", e)

        # --- Boutons QC ---
        if event == "-QC-RAW-":
            open_html_from_zip(qc_zip, "fastq_raw/", window, "FASTQ Raw QC", global_tmp)

        if event == "-QC-TRIM-":
            open_html_from_zip(qc_zip, "fastq_trimmed/", window, "FASTQ Trimmed QC", global_tmp)

        if event == "-QC-BAM-":
            open_html_from_zip(qc_zip, "BAM/", window, "BAM QC", global_tmp)

    window.close()


