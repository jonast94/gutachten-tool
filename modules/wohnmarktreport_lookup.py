import csv
from pathlib import Path


PLZ_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "wohnmarktreport_kaufkraft_2026.csv"
BEZIRK_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "wohnmarktreport_bezirke_2026.csv"


def get_kaufkraft_data(plz: str, bezirk_clean: str) -> dict:
    """
    Holt Kaufkraftdaten aus zwei Quellen:
    1. PLZ-Wert aus der PLZ-Tabelle
    2. Bezirkswert aus der Bezirkstabelle

    Dadurch werden grenzüberschreitende PLZ-Fälle sauberer behandelt.
    """

    if not PLZ_CSV_PATH.exists():
        raise FileNotFoundError(f"PLZ-Kaufkraft-CSV nicht gefunden: {PLZ_CSV_PATH}")

    if not BEZIRK_CSV_PATH.exists():
        raise FileNotFoundError(f"Bezirks-Kaufkraft-CSV nicht gefunden: {BEZIRK_CSV_PATH}")

    plz_matches = []

    with open(PLZ_CSV_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["plz"].strip() == plz.strip():
                plz_matches.append(row)

    chosen_plz_row = None

    if len(plz_matches) == 1:
        chosen_plz_row = plz_matches[0]
    elif len(plz_matches) > 1:
        for row in plz_matches:
            if row["bezirk"].strip().lower() == bezirk_clean.strip().lower():
                chosen_plz_row = row
                break

        if chosen_plz_row is None:
            chosen_plz_row = plz_matches[0]

    bezirk_row = None

    with open(BEZIRK_CSV_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["bezirk"].strip().lower() == bezirk_clean.strip().lower():
                bezirk_row = row
                break

    return {
        "jahr": "2026",
        "plz": plz,
        "bezirk_aus_adresse": bezirk_clean,
        "bezirk_aus_plz_tabelle": chosen_plz_row["bezirk"] if chosen_plz_row else None,
        "kaufkraft_plz": chosen_plz_row["kaufkraft_plz"] if chosen_plz_row else None,
        "rang_plz": chosen_plz_row["rang_plz"] if chosen_plz_row else None,
        "bezirk_fuer_bezirkswert": bezirk_row["bezirk"] if bezirk_row else bezirk_clean,
        "kaufkraft_bezirk": bezirk_row["kaufkraft_bezirk"] if bezirk_row else None,
        "kaufkraft_berlin": chosen_plz_row["kaufkraft_berlin"] if chosen_plz_row else None,
        "plz_mehrfachtreffer": len(plz_matches),
        "bezirksabweichung": (
            chosen_plz_row["bezirk"].strip().lower() != bezirk_clean.strip().lower()
            if chosen_plz_row and chosen_plz_row.get("bezirk")
            else False
        )
    }