import csv
import re
from collections import defaultdict
from pathlib import Path

import pdfplumber


PDF_PATH = Path(__file__).resolve().parent.parent / "data" / "wohnmarktreport_2026.pdf"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "wohnmarktreport_kaufkraft_2026.csv"

DISTRICT_PAGES = list(range(20, 43, 2))  # 20, 22, 24, ..., 42
YEAR = 2026


def clean_token(text: str) -> str:
    text = text.replace("–", "-")
    text = text.replace("−", "-")
    text = text.replace("ﬁ", "fi")
    text = text.replace("ﬂ", "fl")
    text = text.replace("\xa0", " ")
    return text.strip()


def extract_district_name_from_words(words: list[dict]) -> str | None:
    line_map = build_lines(words)
    top_keys = sorted(line_map.keys())[:6]

    for key in top_keys:
        line = " ".join(token["text"] for token in line_map[key])
        line = clean_token(line)
        match = re.match(r"^(.*?)\s+Bezirke\s+Wohnmarktreport Berlin 2026$", line)
        if match:
            return match.group(1).strip()

    return None


def build_lines(words: list[dict]) -> dict:
    """
    Gruppiert Wörter zeilenweise über die y-Position.
    """
    lines = defaultdict(list)

    for word in words:
        top_key = round(word["top"], 1)
        lines[top_key].append(word)

    for key in lines:
        lines[key] = sorted(lines[key], key=lambda w: w["x0"])

    return lines


def parse_plz_rows_from_lines(lines: dict) -> list[dict]:
    results = []

    for key in sorted(lines.keys()):
        tokens = [clean_token(w["text"]) for w in lines[key]]
        tokens = [t for t in tokens if t]

        if not tokens:
            continue

        if not re.fullmatch(r"\d{5}", tokens[0]):
            continue

        # n/a-Zeilen überspringen
        if "n/a" in [t.lower() for t in tokens]:
            continue

        # Wir suchen die letzte Zahl mit Rang in Klammern:
        # Beispiel Ende: 4.214 (115)
        joined = " ".join(tokens)
        match = re.search(r"(\d[\d\.]*,\d|\d[\d\.]*)\s*\((\d+)\)\s*$", joined)
        if not match:
            continue

        kaufkraft_plz = match.group(1)
        rang_plz = match.group(2)

        results.append({
            "plz": tokens[0],
            "kaufkraft_plz": kaufkraft_plz,
            "rang_plz": rang_plz,
            "raw_line": joined,
        })

    return results


def parse_summary_values_from_lines(lines: dict) -> tuple[str | None, str | None]:
    kaufkraft_bezirk = None
    kaufkraft_berlin = None

    for key in sorted(lines.keys()):
        tokens = [clean_token(w["text"]) for w in lines[key]]
        tokens = [t for t in tokens if t]

        if not tokens:
            continue

        if tokens[0] == "Bezirk":
            joined = " ".join(tokens)
            numbers = re.findall(r"\d[\d\.]*,\d|\d[\d\.]*", joined)
            # Erwartung z. B.:
            # Bezirk 2.917 19,47 7,33 31,03 62,9 1.224 4.072 40,3
            if len(numbers) >= 2:
                kaufkraft_bezirk = numbers[-2]

        if tokens[0] == "Berlin":
            joined = " ".join(tokens)
            numbers = re.findall(r"\d[\d\.]*,\d|\d[\d\.]*", joined)
            # Erwartung:
            # Berlin 40.035 15,80 7,06 28,57 63,0 995 4.445
            if numbers:
                kaufkraft_berlin = numbers[-1]

    return kaufkraft_bezirk, kaufkraft_berlin


def import_wohnmarktreport_kaufkraft():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF nicht gefunden: {PDF_PATH}")

    rows = []

    with pdfplumber.open(PDF_PATH) as pdf:
        for page_number in DISTRICT_PAGES:
            page = pdf.pages[page_number - 1]

            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=2,
                keep_blank_chars=False,
                use_text_flow=False
            )

            words = [{**w, "text": clean_token(w["text"])} for w in words if clean_token(w["text"])]

            district_name = extract_district_name_from_words(words)
            if not district_name:
                print(f"Kein Bezirksname erkannt auf Seite {page_number}")
                continue

            lines = build_lines(words)
            plz_rows = parse_plz_rows_from_lines(lines)
            kaufkraft_bezirk, kaufkraft_berlin = parse_summary_values_from_lines(lines)

            print(f"Seite {page_number}: {district_name}")
            print(f"  PLZ-Treffer: {len(plz_rows)}")
            print(f"  Bezirkswert: {kaufkraft_bezirk}")
            print(f"  Berlin-Wert: {kaufkraft_berlin}")

            if plz_rows:
                print(f"  Erste PLZ-Zeile: {plz_rows[0]['raw_line']}")

            for item in plz_rows:
                rows.append({
                    "jahr": YEAR,
                    "bezirk": district_name,
                    "plz": item["plz"],
                    "kaufkraft_plz": item["kaufkraft_plz"],
                    "rang_plz": item["rang_plz"],
                    "kaufkraft_bezirk": kaufkraft_bezirk,
                    "kaufkraft_berlin": kaufkraft_berlin,
                })

    if not rows:
        raise ValueError("Es konnten keine Kaufkraftdaten aus dem Wohnmarktreport extrahiert werden.")

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "jahr",
                "bezirk",
                "plz",
                "kaufkraft_plz",
                "rang_plz",
                "kaufkraft_bezirk",
                "kaufkraft_berlin",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV gespeichert unter: {OUTPUT_PATH}")
    print(f"Anzahl Datensätze: {len(rows)}")