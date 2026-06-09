import requests
from shapely.geometry import shape, Point


WFS_URL = "https://gdi.berlin.de/services/wfs/brw2026"
WFS_TYPENAME = "brw2026:brw2026_vector"


def _query_brw_features(latitude: float, longitude: float) -> list:
    delta = 0.001

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": WFS_TYPENAME,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "bbox": f"{longitude - delta},{latitude - delta},{longitude + delta},{latitude + delta},EPSG:4326",
    }

    headers = {
        "User-Agent": "gutachten-tool/1.0"
    }

    response = requests.get(WFS_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data.get("features", [])


def _find_zone_for_point(lat: float, lon: float) -> dict | None:
    point = Point(lon, lat)
    features = _query_brw_features(lat, lon)

    for feature in features:
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})

        if not geometry:
            continue

        polygon = shape(geometry)

        if polygon.contains(point) or polygon.touches(point):
            return {
                "brwid": properties.get("brwid"),
                "bezirk": properties.get("bezirk"),
                "brw": properties.get("brw"),
                "nutzung": properties.get("nutzung"),
                "stichtag": properties.get("stichtag"),
                "gfz": properties.get("gfz"),
                "beitragszustand": properties.get("beitragszustand"),
                "lumnum": properties.get("lumnum"),
            }

    return None


def get_brw_data(latitude: str, longitude: str) -> dict:
    """
    Ermittelt den Bodenrichtwert robuster über mehrere Prüf-Punkte
    rund um die Adresse, um Grenzfälle zu erkennen.
    """

    lat = float(latitude)
    lon = float(longitude)

    # kleiner Prüfkranz um den Adresspunkt
    offset = 0.00005  # wenige Meter
    test_points = [
        ("zentrum", lat, lon),
        ("nord", lat + offset, lon),
        ("sued", lat - offset, lon),
        ("ost", lat, lon + offset),
        ("west", lat, lon - offset),
    ]

    found_zones = []

    for label, test_lat, test_lon in test_points:
        zone = _find_zone_for_point(test_lat, test_lon)
        if zone:
            zone["testpunkt"] = label
            found_zones.append(zone)

    if not found_zones:
        return {
            "in_brw_zone": False,
            "grenzfall": False,
            "anzahl_zonen": 0,
            "brw": None,
            "nutzung": None,
            "stichtag": None,
            "gfz": None,
            "beitragszustand": None,
            "bezirk": None,
            "brwid": None,
            "hinweis": "Keine Bodenrichtwertzone gefunden.",
            "zonen_details": []
        }

    # eindeutige Zonen nach brwid sammeln
    unique_zones = {}
    for zone in found_zones:
        brwid = zone.get("brwid")
        if brwid not in unique_zones:
            unique_zones[brwid] = zone

    zones_list = list(unique_zones.values())

    if len(zones_list) == 1:
        zone = zones_list[0]
        return {
            "in_brw_zone": True,
            "grenzfall": False,
            "anzahl_zonen": 1,
            "brw": zone.get("brw"),
            "nutzung": zone.get("nutzung"),
            "stichtag": zone.get("stichtag"),
            "gfz": zone.get("gfz"),
            "beitragszustand": zone.get("beitragszustand"),
            "bezirk": zone.get("bezirk"),
            "brwid": zone.get("brwid"),
            "hinweis": "Eindeutige Bodenrichtwertzone.",
            "zonen_details": zones_list
        }

    # Grenzfall: mehrere Zonen im unmittelbaren Umfeld
    return {
        "in_brw_zone": True,
        "grenzfall": True,
        "anzahl_zonen": len(zones_list),
        "brw": None,
        "nutzung": None,
        "stichtag": None,
        "gfz": None,
        "beitragszustand": None,
        "bezirk": None,
        "brwid": None,
        "hinweis": "Mehrere Bodenrichtwertzonen im unmittelbaren Gebäudebereich. Manuelle Prüfung erforderlich.",
        "zonen_details": zones_list
    }