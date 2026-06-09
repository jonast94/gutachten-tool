import requests
from shapely.geometry import shape, Point


WFS_URL = "https://gdi.berlin.de/services/wfs/erhaltungsverordnungsgebiete"
WFS_TYPENAME = "erhaltungsverordnungsgebiete:erhaltgeb_em"


def get_milieuschutz_data(latitude: str, longitude: str) -> dict:
    """
    Prüft, ob die Koordinate tatsächlich innerhalb eines Milieuschutzgebiets liegt.
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
                "in_milieuschutz": True,
                "gebietsname": properties.get("gebietsname"),
                "bezirk": properties.get("bezirk"),
                "inkraft": properties.get("f_in_kraft"),
                "flaeche_ha": properties.get("fl_ha"),
                "feature_count": len(features),
            }

    return {
        "in_milieuschutz": False,
        "gebietsname": None,
        "bezirk": None,
        "inkraft": None,
        "flaeche_ha": None,
        "feature_count": len(features),
    }