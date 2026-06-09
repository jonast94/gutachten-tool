import requests
from shapely.geometry import shape, Point


WFS_URL = "https://gdi.berlin.de/services/wfs/ua_uesg"
WFS_TYPENAME = "ua_uesg:c_ueberschwemmungsgebiete"


def get_hochwasser_data(latitude: str, longitude: str) -> dict:
    """
    Prüft per Punkt-in-Polygon, ob die Koordinate in einem festgesetzten
    Überschwemmungsgebiet liegt.
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
                "in_hochwasser": True,
                "bezeichnung": properties.get("name") or properties.get("bezeichnung"),
                "gewaesser": properties.get("gewaesser") or properties.get("gew_name"),
                "rechtsstand": properties.get("rechtsstand") or properties.get("status"),
                "feature_count": len(features),
            }

    return {
        "in_hochwasser": False,
        "bezeichnung": None,
        "gewaesser": None,
        "rechtsstand": None,
        "feature_count": len(features),
    }