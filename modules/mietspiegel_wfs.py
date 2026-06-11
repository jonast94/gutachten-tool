import math
import requests


WFS_URL = "https://gdi.berlin.de/services/wfs/wohnlagenadr2026"
WFS_TYPENAME = "wohnlagenadr2026:wohnlagenadr2026"


def _normalize_key(value: str) -> str:
    if not value:
        return ""
    return (
        value.strip()
        .lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def _distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    return math.sqrt((lon1 - lon2) ** 2 + (lat1 - lat2) ** 2)


def _extract_coords(feature: dict) -> tuple[float, float] | tuple[None, None]:
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates")

    if not coords:
        return None, None

    # erwartet Punktgeometrie [lon, lat]
    if isinstance(coords, list) and len(coords) >= 2 and isinstance(coords[0], (int, float)):
        return float(coords[0]), float(coords[1])

    return None, None


def _find_wohnlage_property(properties: dict) -> str | None:
    """
    Sucht robust nach einem Attribut, das die Wohnlage enthält.
    Übersetzt bekannte Berliner Kürzel direkt in lesbare Werte.
    """
    if not properties:
        return None

    preferred_keys = [
        "wohnlage",
        "wohn_lage",
        "wohnlag",
        "wol",
        "wl",
    ]

    normalized = {_normalize_key(k): v for k, v in properties.items()}

    raw_value = None

    for key in preferred_keys:
        if key in normalized and normalized[key]:
            raw_value = str(normalized[key]).strip()
            break

    if raw_value is None:
        for key, value in normalized.items():
            if "wohnlag" in key and value:
                raw_value = str(value).strip()
                break

    if raw_value is None:
        return None

    value_norm = _normalize_key(raw_value)

    mapping = {
        "e": "einfach",
        "m": "mittel",
        "g": "gut",
        "einfach": "einfach",
        "mittel": "mittel",
        "gut": "gut",
    }

    return mapping.get(value_norm, raw_value)

    normalized = { _normalize_key(k): v for k, v in properties.items() }

    for key in preferred_keys:
        if key in normalized and normalized[key]:
            return str(normalized[key])

    # Fallback: irgendein Feld, dessen Name 'wohnlag' enthält
    for key, value in normalized.items():
        if "wohnlag" in key and value:
            return str(value)

    return None


def get_wohnlage_from_wfs(latitude: str, longitude: str) -> dict:
    """
    Holt die Wohnlage für eine Berliner Adresse über den offiziellen WFS-Dienst.
    Die Suche erfolgt über eine kleine Bounding Box um die geocodierte Koordinate.
    """

    lat = float(latitude)
    lon = float(longitude)

    # kleine Suchbox um den Punkt
    delta = 0.0008  # ca. wenige Dutzend Meter in Berlin

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": WFS_TYPENAME,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "bbox": f"{lon - delta},{lat - delta},{lon + delta},{lat + delta},EPSG:4326",
    }

    headers = {
        "User-Agent": "gutachten-tool/1.0"
    }

    response = requests.get(WFS_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    features = data.get("features", [])

    if not features:
        raise ValueError("Keine Wohnlagen-Daten im WFS für diese Koordinate gefunden.")

    # nächstgelegenen Treffer zum geocodierten Punkt auswählen
    best_feature = None
    best_distance = None

    for feature in features:
        feat_lon, feat_lat = _extract_coords(feature)
        if feat_lon is None or feat_lat is None:
            continue

        dist = _distance(lon, lat, feat_lon, feat_lat)

        if best_distance is None or dist < best_distance:
            best_distance = dist
            best_feature = feature

    # falls keine auswertbare Geometrie vorhanden ist, ersten Treffer nehmen
    if best_feature is None:
        best_feature = features[0]

    properties = best_feature.get("properties", {})
    wohnlage = _find_wohnlage_property(properties)

    if not wohnlage:
        available_fields = ", ".join(properties.keys())
        raise ValueError(
            "Wohnlage-Feld im WFS-Treffer nicht erkannt. "
            f"Verfügbare Felder: {available_fields}"
        )

    return {
        "wohnlage": wohnlage,
        "properties": properties,
        "feature_count": len(features),
    }