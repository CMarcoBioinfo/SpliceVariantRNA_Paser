import PySimpleGUI as sg

COLUMNS_BY_SOURCE = {
    "Statistical": ["Gene", "Event", "Position", "Depth", "PSI-like", "p-value", "nbSignificantSamples"],
    "Unique": ["Gene", "Event", "Position", "Depth", "PSI-like", "p-value", "nbFilteredSamples"],
    "ThresholdExceeded": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
    "NoModel": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
    "TooComplex": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
}

def normalize(s):
    """Normalise une chaîne pour correspondre aux clés internes."""
    return s.strip().replace(" ", "").lower()

def events_to_table(events, columns):
    return [[ev.get(col, "") for col in columns] for ev in events]

def open_patient_window(events):
    sg.theme("SystemDefault")

    # Normalisation des sources dans les events
    for ev in events:
        ev["Source"] = normalize(ev["Source"])

    # Normalisation des clés du dictionnaire
    COLUMNS_NORM = { normalize(k): v for k, v in COLUMNS_BY_SOURCE.items() }

    # Pré-filtrage des events par catégorie
    events_by_cat = {
        cat: [ev for ev in events if ev["Source"] == cat]
        for cat in COLUMNS_NORM.keys()
    }

    # Création des tabs
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

        # IMPORTANT : clé du tab = "-TAB-statistical-"
        tabs.append(sg.Tab(original_name, [[table]], key=f"-TAB-{cat_norm}-"))

    tab_group = sg.TabGroup(
        [tabs],
        key="-TABGROUP-",
        expand_x=True,
        expand_y=True,
        enable_events=True
    )

    layout = [
        [tab_group],
        [
            sg.Frame(
                "Détails de l'événement",
                [[sg.Multiline("", key="-DETAILS-", size=(80, 15), disabled=True)]],
                expand_x=True,
                expand_y=True
            )
        ]
    ]

    window = sg.Window("SpliceVariantRNA Viewer", layout, resizable=True)

    # Catégorie par défaut
    current_category = normalize("Statistical")

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        # --- Changement d'onglet ---
        if event == "-TABGROUP-":
            tab_key = values["-TABGROUP-"]      # ex: "-TAB-statistical-"
            current_category = tab_key[5:-1]    # enlève "-TAB-" et le dernier "-"
            current_category = current_category.lower()

        # --- Sélection d'une ligne ---
        if event.startswith("-TABLE-"):
            try:
                idx = values[event][0]
                selected_event = events_by_cat[current_category][idx]

                details = "\n".join(f"{k}: {v}" for k, v in selected_event.items())
                window["-DETAILS-"].update(details)

            except Exception as e:
                print("Erreur détails:", e)

    window.close()
