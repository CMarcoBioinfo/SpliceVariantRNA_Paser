from .recap_parser import parse_recap, row_to_event

def process_sample(run_zip, group_zip, sample_file):
    rows = parse_recap(run_zip, group_zip, sample_file)
    return [row_to_event(r, sample_file) for r in rows]
