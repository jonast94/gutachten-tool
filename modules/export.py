import json
from pathlib import Path


def _create_filename(street: str, house_number: str, postal_code: str) -> str:
    """
    Erzeugt einen sauberen Dateinamen.
    """
    street_clean = street.replace(" ", "_")
    return f"{street_clean}_{house_number}_{postal_code}.json"


def save_result(data: dict, street: str, house_number: str, postal_code: str):
    """
    Speichert die Ergebnisdaten als JSON-Datei im output-Ordner.
    """

    base_path = Path(__file__).resolve().parent.parent
    output_dir = base_path / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = _create_filename(street, house_number, postal_code)
    file_path = output_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return file_path