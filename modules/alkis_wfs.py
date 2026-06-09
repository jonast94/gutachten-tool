import requests
import xml.etree.ElementTree as ET
from shapely.geometry import shape, Point


BEZIRKE_WFS_URL = "https://gdi.berlin.de/services/wfs/alkis_bezirke"
ORTSTEILE_WFS_URL = "https://gdi.berlin.de/services/wfs/alkis_ortsteile"


def _get_feature_type_name(wfs_url: str) -> str:
    params = {
        "SERVICE": "WFS",
        "REQUEST": "GetCapabilities",
    }

    response = requests.get(wfs_url, params=params, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    namespaces = {
        "wfs": "http://www.opengis.net/wfs/2.0"
    }

    elem = root.find(".//wfs:FeatureType/wfs:Name", namespaces)

    if elem is not None and elem.text:
        return elem.text.strip()

    raise ValueError(f"Kein Feature-Type gefunden für {wfs_url}")


def _query_wfs_features(wfs_url: str, typename: str, lat: float, lon: float):
    delta = 0.001

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": typename,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "bbox": f"{lon - delta},{lat - delta},{lon + delta},{lat + delta},EPSG:4326",
    }

    response = requests.get(wfs_url, params=params, timeout=30)
    response.raise_for_status()

    return response.json().get("features", [])


def _find_containing_feature(features, lat: float, lon: float):
    point = Point(lon, lat)

    for feature in features:
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})

        if not geometry:
            continue

        polygon = shape(geometry)

        if polygon.contains(point) or polygon.touches(point):
            return properties

    return None


def _pick_name(props, level):
    if not props:
        return None

    if level == "bezirk":
        candidates = ["namgem", "name"]
    elif level == "ortsteil":
        candidates = ["nam", "name"]
    else:
        candidates = ["name", "nam", "namgem"]

    for key in candidates:
        value = props.get(key)
        if value not in (None, "", "None"):
            return str(value).strip()

    return None


def get_alkis_location_data(latitude, longitude):
    lat = float(latitude)
    lon = float(longitude)

    bezirk_typename = _get_feature_type_name(BEZIRKE_WFS_URL)
    ortsteil_typename = _get_feature_type_name(ORTSTEILE_WFS_URL)

    bezirk_features = _query_wfs_features(BEZIRKE_WFS_URL, bezirk_typename, lat, lon)
    ortsteil_features = _query_wfs_features(ORTSTEILE_WFS_URL, ortsteil_typename, lat, lon)

    bezirk_props = _find_containing_feature(bezirk_features, lat, lon)
    ortsteil_props = _find_containing_feature(ortsteil_features, lat, lon)

    return {
        "bezirk_wfs": _pick_name(bezirk_props, "bezirk"),
        "ortsteil_wfs": _pick_name(ortsteil_props, "ortsteil"),
        "bezirk_props": bezirk_props,
        "ortsteil_props": ortsteil_props,
    }