import pandas as pd
import zipfile
import io
import math

SHEETS = {
    "Statistical Junctions": "Statistical",
    "Unique Junctions": "Unique",
    "Threshold Exceeded Junctions": "ThresholdExceeded",
    "No model Junctions": "NoModel",
    "Event too complex": "TooComplex"
}

def safe_int(x):
    """Convertit en int sauf si NaN ou None."""
    if x is None:
        return 0
    if isinstance(x, float) and math.isnan(x):
        return 0
    try:
        return int(x)
    except:
        return 0

def safe_float(x):
    """Convertit en float sauf si NaN ou None."""
    if x is None:
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    try:
        return float(x)
    except:
        return None

def read_recap_from_zip(run_zip, group_zip, sample_file):
    """Lit un fichier recap.xlsx dans un ZIP imbriqué, compatible Python 3.12."""
    with zipfile.ZipFile(run_zip, "r") as outer:
        # Lire le ZIP interne ENTIER dans un buffer
        inner_bytes = outer.read(group_zip)
        inner_buffer = io.BytesIO(inner_bytes)

        # Ouvrir le ZIP interne depuis le buffer
        with zipfile.ZipFile(inner_buffer, "r") as inner_zip:
            raw = inner_zip.read(sample_file)
            return io.BytesIO(raw)


def parse_recap(run_zip, group_zip, sample_file):
    bio = read_recap_from_zip(run_zip, group_zip, sample_file)
    dfs = []

    for sheet_name, source_label in SHEETS.items():
        try:
            bio.seek(0)
            df = pd.read_excel(bio, sheet_name=sheet_name)
        except Exception:
            continue

        if df.empty:
            continue

        df["Source"] = source_label
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True, join="outer")

def row_to_event(row, sample_file):
    sample_name = sample_file.replace(".recap.xlsx", "")
    reads_col = sample_name
    psi_col = f"P_{sample_name}"

    chrom = row.get("chr")
    start = row.get("start")
    end = row.get("end")
    strand = row.get("strand")

    position = None
    if chrom and start and end and strand:
        position = f"{chrom}:{start}-{end}"

    # p-value
    p = safe_float(row.get("p_value"))
    level = row.get("SignificanceLevel")

    if p is None:
        pvalue_fmt = "nan"
    else:
        p_round = round(p, 2)
        pvalue_fmt = f"{p_round} ({level})" if level else f"{p_round}"

    # PSI-like
    psi_raw = safe_float(row.get(psi_col))
    psi_val = round(psi_raw, 2) if psi_raw is not None else None

    event = {
        "Gene": row.get("Gene"),
        "Event": row.get("event_type"),
        "Position": position,
        "Depth": safe_int(row.get(reads_col)),
        "PSI-like": psi_val,

        "Distribution": row.get("DistribAjust"),
        "p-value": pvalue_fmt,
        "Significative": row.get("Significative"),
        "nbSignificantSamples": safe_int(row.get("nbSignificantSamples")),

        "SampleReads": row.get("SampleReads"),
        "nbFilteredSamples": safe_int(row.get("nbSampFilter")),

        "cStart": row.get("cStart"),
        "cEnd": row.get("cEnd"),
        "HGVS": row.get("HGVS"),

        "Source": row.get("Source"),

        "Plots_links": {},
        "IGV_links": {},
    }

    return event
