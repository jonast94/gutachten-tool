import re
import requests
from shapely.geometry import shape, Point


WFS_URL = "https://gdi.berlin.de/services/wfs/bplan"
WFS_TYPENAME = "bplan:b_bp_fs"


def _extract_bplan_name(properties: dict) -> str | None:
    """
    Versucht die B-Plan-Bezeichnung aus den Attributen zu ermitteln.
    """

    direct_keys = [
        "name",
        "planname",
        "plannr",
        "plan_nr",
        "nummer",
        "bebauungsplan",
        "bplan",
        "planbez",
        "bezeichnung",
    ]

    for key in direct_keys:
        value = properties.get(key)
        if value not in (None, ""):
            return str(value).strip()

    scan_url = properties.get("scan_www")
    if scan_url:
        match = re.search(r"bebauungsplan_([a-z0-9_]+)\.pdf", str(scan_url), re.IGNORECASE)
        if match:
            raw = match.group(1)
            parts = raw.split("_")
            if len(parts) >= 2:
                first = parts[0].upper()
                rest = "-".join(part.upper() for part in parts[1:])
                return f"{first}-{rest}"
            return raw.upper()

    return None


def get_bplan_data(latitude: str, longitude: str) -> dict:
    """
    Prüft, ob die Koordinate innerhalb eines festgesetzten Bebauungsplans liegt.
    Gibt die Planbezeichnung und einige Zusatzinfos zurück.
    """

    lat = float(latitude)
    lon = float(longitude)

    delta = 0.001

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
    point = Point(lon, lat)

    for feature in features:
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})

        if not geometry:
            continue

        polygon = shape(geometry)

        if polygon.contains(point) or polygon.touches(point):
            return {
                "in_bplan": True,
                "bezeichnung": _extract_bplan_name(properties),
                "inhalt": properties.get("inhalt"),
                "scan_www": properties.get("scan_www"),
                "feature_count": len(features),
            }

    return {
        "in_bplan": False,
        "bezeichnung": None,
        "inhalt": None,
        "scan_www": None,
        "feature_count": len(features),
    }