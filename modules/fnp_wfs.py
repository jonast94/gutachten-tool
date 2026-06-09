import requests
from shapely.geometry import shape, Point


WFS_URL = "https://gdi.berlin.de/services/wfs/fnp_2025"
WFS_TYPENAME = "fnp_2025:fnp_2025_vektor"


def get_fnp_data(latitude: str, longitude: str) -> dict:
    """
    Prüft per Punkt-in-Polygon, ob die Koordinate in einer FNP-Fläche liegt,
    und gibt die relevanten FNP-Daten zurück.
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
                "in_fnp": True,
                "nutzungsart": properties.get("nutzungsart"),
                "zweckbestimmung": properties.get("zweckbestimmung"),
                "gisid": properties.get("gisid"),
                "os_nr": properties.get("os_nr"),
                "feature_count": len(features),
            }

    return {
        "in_fnp": False,
        "nutzungsart": None,
        "zweckbestimmung": None,
        "gisid": None,
        "os_nr": None,
        "feature_count": len(features),
    }