import requests
from shapely.geometry import shape, Point


WFS_URL = "https://gdi.berlin.de/services/wfs/denkmale"
WFS_TYPENAME = "denkmale:denkmale"


def get_denkmalschutz_data(latitude: str, longitude: str) -> dict:
    """
    Prüft Denkmalschutz an einer Berliner Adresse.
    Unterscheidet zwischen exaktem Treffer und Denkmalbezug in der Umgebung.
    """

    lat = float(latitude)
    lon = float(longitude)

    delta = 0.001
    point = Point(lon, lat)

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

    exact_hit = None
    nearest_hit = None
    nearest_distance = None

    for feature in features:
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})

        if not geometry:
            continue

        geom = shape(geometry)

        try:
            distance = geom.distance(point)
        except Exception:
            continue

        contains_point = False
        if geom.geom_type in ["Polygon", "MultiPolygon"]:
            contains_point = geom.contains(point) or geom.touches(point)

        # Exakter Treffer
        if contains_point or distance < 0.00008:
            exact_hit = {
                "typ": properties.get("typ"),
                "id": properties.get("id"),
                "gisid": properties.get("gisid"),
                "link": properties.get("link"),
                "distance": distance,
                "geometry_type": geom.geom_type,
            }
            break

        # Nächstgelegener Treffer
        if nearest_distance is None or distance < nearest_distance:
            nearest_distance = distance
            nearest_hit = {
                "typ": properties.get("typ"),
                "id": properties.get("id"),
                "gisid": properties.get("gisid"),
                "link": properties.get("link"),
                "distance": distance,
                "geometry_type": geom.geom_type,
            }

    if exact_hit:
        return {
            "denkmalschutz_exakt": True,
            "trefferart": exact_hit["typ"],
            "link": exact_hit["link"],
            "id": exact_hit["id"],
            "gisid": exact_hit["gisid"],
            "distanz": exact_hit["distance"],
            "geometrie": exact_hit["geometry_type"],
            "umgebungstreffer": nearest_hit,
        }

    return {
        "denkmalschutz_exakt": False,
        "trefferart": None,
        "link": None,
        "id": None,
        "gisid": None,
        "distanz": None,
        "geometrie": None,
        "umgebungstreffer": nearest_hit,
    }