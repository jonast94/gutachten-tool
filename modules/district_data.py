import csv
from pathlib import Path


def get_district_data(district_name: str) -> dict:
    """
    Liest Bezirksdaten aus der CSV-Datei und gibt die Daten
    für den angegebenen Berliner Bezirk zurück.
    """

    csv_path = Path(__file__).resolve().parent.parent / "data" / "berlin_districts.csv"

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["bezirk"].strip().lower() == district_name.strip().lower():
                return {
                    "bezirk": row["bezirk"],
                    "einwohner": row["einwohner"],
                    "flaeche_km2": row["flaeche_km2"],
                    "ortsteile": row["ortsteile"]
                }

    raise ValueError(f"Keine Bezirksdaten gefunden für: {district_name}")