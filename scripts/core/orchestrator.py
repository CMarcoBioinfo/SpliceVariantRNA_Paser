from .recap_parser import parse_recap, row_to_event

def process_sample(run_zip, group_zip, sample_file):
    df = parse_recap(run_zip, group_zip, sample_file)
    if df.empty:
        return []

    events = []
    for _, row in df.iterrows():
        events.append(row_to_event(row, sample_file))

    return events
